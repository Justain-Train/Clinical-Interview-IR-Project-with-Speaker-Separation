# Alignment Module

This module aligns speaker diarization outputs with transcription outputs.

---

## Purpose

**Problem**: Diarization gives us `(speaker, time)`, transcription gives us `(text, time)`.  
**Solution**: Merge them to get `(speaker, text, time)`.

---

## Process

1. **Input**: 
   - Diarization segments: `[(SPEAKER_00, 0.0-5.2), (SPEAKER_01, 5.2-10.1), ...]`
   - Transcription segments: `[("Hello...", 0.0-5.5), ("I've been...", 5.5-10.0), ...]`

2. **Alignment**: Match based on time overlap

3. **Output**: 
   - `[(SPEAKER_00, "Hello...", 0.0-5.2), (SPEAKER_01, "I've been...", 5.2-10.1), ...]`

---

## Challenges

### Time Misalignment
- Diarization: `0.0 - 5.2`
- Transcription: `0.0 - 5.5`

**Solution**: Use overlap threshold (e.g., 70% overlap required)

### Ambiguous Segments
- One transcript segment overlaps two speaker segments

**Solution**: Assign to speaker with largest overlap

---

## Usage

```python
from alignment.speaker_aligner import align_speakers_to_transcript
from alignment.segment_builder import build_segments

aligned = align_speakers_to_transcript(
    diarization=diarization_result,
    transcription=transcription_result
)

segments = build_segments(
    aligned=aligned,
    speaker_mapping={"SPEAKER_00": "CLINICIAN", "SPEAKER_01": "PATIENT"}
)

# Returns: List[TranscriptSegment] ready for indexing
```

---

## Notes

- Only used in offline pipeline (live doesn't need alignment)
- Critical for quality: Poor alignment → wrong speaker labels
- Validation: Check for segments with <50% overlap (potential errors)
