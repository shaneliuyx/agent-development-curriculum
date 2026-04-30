# Week 8.5 - Voice AI Agents

## Why This Week Matters

Voice AI agents have moved from research curiosity to production deployment shape. Customer support centers are replacing IVR trees; accessibility tooling now speaks back; developers run voice-enabled coding assistants hands-free. The inflection point came in October 2024 when OpenAI shipped its Realtime API — the first commercially available system that streams native audio tokens bidirectionally, collapsing the STT → LLM → TTS pipeline into a single model pass. Simultaneously, ElevenLabs and Cartesia pushed TTS time-to-first-audio below 200ms. These two shifts made sub-500ms end-to-end latency achievable outside a research lab.

---

## Theory Primer — Two Architectures

### Architecture A: Cascaded Pipeline

```
Microphone → VAD → STT (Whisper) → LLM (Claude) → TTS (ElevenLabs) → Speaker
```

Each stage is a separate network or process call.

- **STT**: `openai/whisper-large-v3` local or via API. WER 2.7% on LibriSpeech clean.
- **LLM**: Claude 3.5 Sonnet or GPT-4o via streaming API.
- **TTS**: ElevenLabs Turbo v2.5 (~120ms TTFA) or Cartesia Sonic (~90ms TTFA).

**Latency breakdown (cascaded p50):**

| Stage | p50 | p95 |
|---|---|---|
| VAD + STT (Whisper large-v3, local GPU) | 350ms | 700ms |
| LLM first token (Claude Sonnet, streaming) | 600ms | 1100ms |
| TTS time-to-first-audio (ElevenLabs Turbo) | 120ms | 280ms |
| **Total** | **~1070ms** | **~2080ms** |

**Trade-offs:** Composable — swap any stage independently. Each stage inspectable: transcript, LLM output, audio all separate artifacts. Critical for debugging, logging, PII redaction. But latency floor is high — three network hops compound. Error propagation: Whisper errors become LLM hallucinations.

### Architecture B: End-to-End Audio Models

```
Microphone → [Single Model] → Speaker
```

**OpenAI Realtime API** (October 2024): WebSocket-based, streams `input_audio_buffer` chunks, returns `response.audio.delta` events. Measured latency: 320ms p50, 600ms p95.

**Gemini 2.0 Flash Live API**: ~250ms median.

**Trade-offs:** Low latency. Less inspectable — no intermediate transcript to log, audit, or redact. Vendor lock-in — proprietary tokenizer, model, decoder. Tool calling awkward — model emits text function call, waits for response, re-enters audio. Reintroduces latency at every tool boundary.

### The Latency Budget

Humans perceive response delay as unnatural above ~500ms. Cascaded pipelines borderline at p50, poor at p95. End-to-end at 320ms p50 inside comfort zone. Local GPU cascaded reaches 600–700ms p50 — acceptable for non-real-time assistants.

---

## The Hard Parts

### Turn-Taking and Barge-In

Voice conversation is half-duplex but humans constantly violate this with overlapping speech. Voice agent must:
1. Detect end-of-utterance.
2. Allow user to interrupt (barge-in) while agent is speaking.
3. Not interrupt user mid-sentence.

Barge-in requires monitoring input stream while playing TTS output. When VAD detects speech above threshold during playback, cancel TTS stream, discard buffered audio, process new input.

### Voice Activity Detection (VAD)

Silero VAD (open-source, 1MB model, real-time on CPU) is the standard. Reports speech probability per 30ms frame. Typical config: start buffering at probability > 0.5, trigger STT when probability drops below 0.3 for 400ms.

**Critical insight:** End-of-utterance and barge-in detection need different thresholds. End-of-utterance needs to be conservative (400-600ms silence) to avoid mid-sentence cuts. Barge-in needs to be aggressive (150-200ms) to feel responsive.

### Whisper Hallucinations on Silence

Whisper reliably outputs "Thank you for watching" or "Please subscribe" on silence — over-represented YouTube data in training. Mitigations: check `avg_logprob` (discard < -1.0), check `no_speech_prob` (discard > 0.6), use `condition_on_previous_text=False`.

### Backchannel Sounds

Human listeners emit "mm-hmm" as acknowledgment. Filter by duration (< 1s) and content before passing to LLM context.

### Multilingual Code-Switching

Mid-utterance language switches cause WER spikes. Set agent system prompt to explicitly support expected language pairs.

---

## Lab — Build a Cascaded Voice Agent (~3 hours)

**Setup:**
```bash
pip install faster-whisper silero-vad pyaudio numpy anthropic elevenlabs
```

**Step 1: VAD-based audio capture**
```python
import torch, pyaudio, numpy as np

model, utils = torch.hub.load('snakers4/silero-vad', model='silero_vad')

SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE * 30 / 1000)  # 30ms
SILENCE_CHUNKS = 400 // 30  # 400ms

def record_utterance(stream, vad_model):
    audio_buffer, silence_count, speaking = [], 0, False
    while True:
        chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        prob = vad_model(torch.from_numpy(audio_np), SAMPLE_RATE).item()
        if prob > 0.5:
            speaking = True
            audio_buffer.append(chunk)
            silence_count = 0
        elif speaking:
            audio_buffer.append(chunk)
            silence_count += 1
            if silence_count >= SILENCE_CHUNKS:
                break
    return b''.join(audio_buffer)
```

**Step 2: STT with hallucination filter**
```python
from faster_whisper import WhisperModel

whisper = WhisperModel("large-v3", device="cuda", compute_type="float16")

def transcribe(audio_bytes):
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    segments, _ = whisper.transcribe(audio_np, condition_on_previous_text=False, vad_filter=True)
    segments = list(segments)
    if not segments:
        return ""
    seg = segments[0]
    if seg.no_speech_prob > 0.6 or seg.avg_logprob < -1.0:
        return ""  # filter hallucination
    return " ".join(s.text.strip() for s in segments)
```

**Step 3: LLM streaming with Claude**
```python
import anthropic
client = anthropic.Anthropic()

def get_response(transcript, history):
    history.append({"role": "user", "content": transcript})
    response_text = ""
    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        system="Voice assistant. Concise — 2-3 sentences max. No markdown.",
        messages=history,
    ) as stream:
        for text in stream.text_stream:
            response_text += text
    history.append({"role": "assistant", "content": response_text})
    return response_text
```

**Step 4: TTS with cancellation support**
```python
from elevenlabs.client import ElevenLabs
import threading

el = ElevenLabs()

def speak(text, cancel_event):
    audio = el.text_to_speech.convert_as_stream(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        text=text,
        model_id="eleven_turbo_v2_5",
    )
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)
    for chunk in audio:
        if cancel_event.is_set():
            break
        stream.write(chunk)
    stream.close(); pa.terminate()
```

**Step 5: Main loop with barge-in monitoring**
```python
def voice_agent():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    history, cancel = [], threading.Event()
    while True:
        cancel.clear()
        audio = record_utterance(stream, model)
        text = transcribe(audio)
        if not text: continue
        response = get_response(text, history)
        # TTS in thread, monitor for barge-in
        tts = threading.Thread(target=speak, args=(response, cancel))
        tts.start()
        while tts.is_alive():
            chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            if model(torch.from_numpy(audio_np), SAMPLE_RATE).item() > 0.7:
                cancel.set()
                break
        tts.join()
```

**Expected metrics (RTX 3080 + ElevenLabs Turbo):**
- p50: ~900ms, p95: ~1600ms

CPU-only with Whisper base.en:
- p50: ~1400ms, p95: ~2500ms

---

## Lab Extension — Compare to OpenAI Realtime API

| Metric | Cascaded (GPU + ElevenLabs) | OpenAI Realtime |
|---|---|---|
| E2E latency p50 | ~900ms | ~350ms |
| E2E latency p95 | ~1600ms | ~650ms |
| Cost per minute | ~$0.08 | ~$0.24 |
| Transcript available | Yes | Yes (text modality) |
| Vendor lock-in | Low | High |
| HIPAA eligible | Configurable | OpenAI BAA required |

Realtime ~2.5× faster at p50, 3× more expensive. Consumer products: cost premium often justified. B2B compliance-driven: cascaded better default.

---

## Bad-Case Journal

**Entry 1 — Whisper hallucinates on silence.** During 3-second pause while user thinks, Whisper returns "Thank you for watching." `no_speech_prob` was 0.12 (low — Whisper confident), `avg_logprob` was -0.95. Adding logprob threshold at -1.0 eliminated false positives. Whisper has no way to express "I heard nothing meaningful" — fills silence with statistically plausible YouTube text.

**Entry 2 — ElevenLabs over-emotes on technical content.** When agent reads "Error code 404: resource not found," ElevenLabs Turbo adds rising intonation appropriate for narrative speech but bizarre for technical dictation. Mitigation: `stability=0.85`, `similarity_boost=0.5` to flatten emotional range. Or switch to a "professional" voice preset.

**Entry 3 — Interruption detection lags 800ms.** Barge-in detection used 800ms VAD silence threshold (conservative to avoid mid-sentence false positives). Users had to speak for nearly a second before TTS cancelled — felt broken. Reducing barge-in VAD threshold to 200ms (separate from end-of-utterance threshold) eliminated the lag. **Two thresholds for two different problems.**

**Entry 4 — End-to-end model leaks pronoun context from audio metadata.** During testing OpenAI Realtime API, model began referring to user with pronouns matching voice acoustics (pitch, formants) rather than stated preference. End-to-end model infers demographic info from acoustics. Cascaded pipelines produce text transcripts with no acoustic metadata — LLM has no signal. Concrete privacy advantage for cascaded inspectability.

---

## Production Considerations

**PSTN integration.** Twilio Programmable Voice, Vapi.ai, Bland.ai provide WebRTC-to-PSTN bridges. PSTN audio is compressed (G.711, 8kHz) — Whisper trained on 16kHz, so PSTN input requires upsampling and accepts 15-20% WER penalty.

**HIPAA/PCI compliance.** Voice with PHI/PCI requires BAA with every vendor. Anthropic offers BAA; OpenAI Realtime offers BAA on enterprise plans; ElevenLabs offers BAA on enterprise contracts. **Local Whisper + local Coqui TTS** is the only architecture that trivially satisfies HIPAA without vendor agreements.

**Recording retention.** 12 US states have two-party consent laws; GDPR applies in EU. Define retention policies before shipping — typical enterprise: 90-day retention, deletion on customer request. Tag stored audio with consent metadata at ingest.

**Multi-tenant isolation.** Use session IDs as top-level partition keys. Never pass one tenant's history into another tenant's LLM context.

---

## Interview Soundbites

**Soundbite 1 — Latency anatomy**
"Voice agent latency has three components in a cascaded system: STT processing time, LLM first-token latency, and TTS time-to-first-audio. Each is roughly 300 to 600 milliseconds on public APIs at p50, so floor is around a second — borderline for natural conversation. Optimization levers: faster STT model like Whisper base instead of large-v3 if WER is acceptable, low-latency TTS like ElevenLabs Turbo or Cartesia Sonic, reduce LLM prompt size to shrink TTFT. Local GPU Whisper is the single biggest latency reduction in cascaded architecture."

**Soundbite 2 — When end-to-end beats cascaded**
"End-to-end models like OpenAI Realtime beat cascaded specifically when latency is the primary constraint and you tolerate vendor lock-in and reduced inspectability. End-to-end gets to 350ms p50 vs 900ms cascaded because it eliminates two network hops and can begin generating audio before producing complete text. That 550ms difference is meaningful for consumer products where abandonment correlates with perceived lag. But if you need transcripts for compliance, redact PII, or run on your own infrastructure for HIPAA, cascaded is the right default."

**Soundbite 3 — VAD is underestimated**
"VAD sounds trivial and breaks everything when wrong. Too aggressive: sending background noise to STT every 300ms, garbage transcripts, runaway API costs. Too conservative: 500ms added to every turn. The important insight: you need two separate VAD thresholds — one for end-of-utterance (conservative, 400-600ms) and one for barge-in (aggressive, 150-200ms). Most tutorials wire a single threshold and wonder why agent thinks user is done mid-sentence, or why interruptions feel broken."

---

## References

- OpenAI Realtime API: https://platform.openai.com/docs/guides/realtime
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live
- Vapi.ai (production voice infra): https://vapi.ai/
- Whisper paper (Radford et al., 2022): https://arxiv.org/abs/2212.04356
- Silero VAD: https://github.com/snakers4/silero-vad
- Faster-Whisper: https://github.com/SYSTRAN/faster-whisper
- ElevenLabs: https://elevenlabs.io/docs/models
- Cartesia Sonic: https://cartesia.ai/
- LiveKit / Daily.co (WebRTC infra)

---

## Cross-References

**Builds on: W4 ReAct.** Voice agent is a ReAct agent with audio I/O. Core loop (observe → think → act) identical to text ReAct. Added complexity: audio I/O layer + real-time latency constraints.

**Connects to: W11 System Design.** Voice is one deployment shape. W11 covers production architecture; voice adds the constraint that each inference path must complete in under 500ms.

**Distinguish from: W7 Tool Harness.** Voice itself is not a tool — it is the interface modality. Voice agent uses the same tool harness from W7, but the harness is invoked by an agent whose I/O happens to be audio. Confusing the two leads to architectural mistakes like trying to make speech synthesis a callable tool.
