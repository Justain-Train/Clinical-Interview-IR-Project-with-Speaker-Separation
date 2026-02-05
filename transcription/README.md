# Transcription Module

This module handles speech-to-text transcription using OpenAI Whisper.

---

## Purpose

Convert audio to timestamped text transcripts.

---

## Modes

### Batch Mode (`batch_transcribe.py`)
- For offline audio files
- Processes entire file at once
- Returns complete transcript with timestamps

### Streaming Mode (`stream_transcribe.py`)
- For live audio from LiveKit
- Processes chunks in real-time
- Emits segments as events

---

## Usage Examples

### Batch Transcription

```python
from transcription.whisper_client import initialize_whisper
from transcription.batch_transcribe import transcribe_file

model = initialize_whisper(model_size="base")
segments = transcribe_file(
    audio_path="/data/audio/interview_001.wav",
    model=model
)

# Returns: List[TranscriptSegment]
```

### Streaming Transcription

```python
from transcription.stream_transcribe import subscribe_to_stream

await subscribe_to_stream(
    stream_id="patient_stream_001",
    speaker_role=SpeakerRole.PATIENT
)
# Continuously emits TranscriptSegment events
```

---

## Model Selection

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39M | ~10x real-time | Basic |
| base | 74M | ~5x real-time | Good |
| small | 244M | ~2x real-time | Better |
| medium | 769M | ~1x real-time | Best (free) |

**Recommendation**: `base` for development, `small` for production.

---

## Notes

- GPU acceleration recommended for faster processing
- Language auto-detection enabled by default
- Supports confidence scores for quality filtering
