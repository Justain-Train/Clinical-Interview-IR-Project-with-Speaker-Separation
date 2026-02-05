# Diarization Module

This module handles speaker diarization for offline audio using Pyannote.audio.

---

## Purpose

**Problem**: Given an audio file with multiple speakers, identify "who spoke when."

**Solution**: Use Pyannote.audio's pre-trained speaker diarization pipeline.

---

## Components

### `pyannote_runner.py`
Main diarization executor (implementation skeleton only)

### `config.py`
Configuration parameters for diarization

---

## Usage Example

```python
from diarization.pyannote_runner import run_diarization

result = run_diarization(
    audio_path="/data/audio/interview_001.wav",
    num_speakers=2  # Optional hint
)

# Output:
# DiarizationResult(
#   interview_id="interview_001",
#   segments=[
#     DiarizationSegment(start=0.0, end=5.2, speaker="SPEAKER_00"),
#     DiarizationSegment(start=5.2, end=10.1, speaker="SPEAKER_01"),
#     ...
#   ]
# )
```

---

## Configuration Options

- `min_duration_off`: Minimum silence duration to consider as speaker change
- `min_duration_on`: Minimum speech duration to consider as valid segment
- `embedding_model`: Which Pyannote embedding model to use
- `segmentation_model`: Which segmentation model to use

---

## Notes

- Requires HuggingFace token (set in `.env`)
- First run downloads models (~1GB)
- Processing time: ~0.5x real-time (10 min audio → 5 min processing)
