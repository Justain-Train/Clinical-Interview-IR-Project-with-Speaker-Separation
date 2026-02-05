# Offline Ingestion Workflow

**Purpose**: Process uploaded audio files through diarization, transcription, alignment, and indexing.

---

## Trigger

**Type**: Webhook or Manual  
**Input**:
```json
{
  "interview_id": "interview_2024_001",
  "audio_path": "/data/audio/interview_001.wav",
  "metadata": {
    "title": "Initial Consultation",
    "date": "2024-03-15"
  }
}
```

---

## Workflow Steps

### Step 1: Validate Input
- **Action**: Check if audio file exists
- **API**: `GET /api/files/validate`
- **Input**: `audio_path`
- **Output**: `{"valid": true}` or error
- **Error Handling**: Stop workflow if invalid

---

### Step 2: Run Diarization
- **Action**: Identify speaker segments using Pyannote
- **API**: `POST /api/diarization/run`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "audio_path": "/data/audio/interview_001.wav"
  }
  ```
- **Output**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "segments": [
      {"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00"},
      {"start": 5.2, "end": 10.1, "speaker": "SPEAKER_01"},
      {"start": 10.1, "end": 15.3, "speaker": "SPEAKER_00"}
    ],
    "num_speakers": 2
  }
  ```
- **Error Handling**: Retry once on failure, then abort

---

### Step 3: Run Transcription
- **Action**: Transcribe entire audio using Whisper
- **API**: `POST /api/transcription/batch`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "audio_path": "/data/audio/interview_001.wav",
    "language": "en"
  }
  ```
- **Output**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "text": "Hello, how are you feeling today?"
      },
      {
        "start": 5.2,
        "end": 10.1,
        "text": "I've been experiencing headaches."
      }
    ],
    "language": "en",
    "duration": 300.5
  }
  ```
- **Timeout**: 10 minutes (transcription can be slow)
- **Error Handling**: Retry once, then abort

---

### Step 4: Align Speakers with Transcript
- **Action**: Merge diarization and transcription outputs
- **API**: `POST /api/alignment/align`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "diarization": { /* output from Step 2 */ },
    "transcription": { /* output from Step 3 */ }
  }
  ```
- **Output**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "aligned_segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "speaker": "SPEAKER_00",
        "text": "Hello, how are you feeling today?"
      },
      {
        "start": 5.2,
        "end": 10.1,
        "speaker": "SPEAKER_01",
        "text": "I've been experiencing headaches."
      }
    ]
  }
  ```
- **Error Handling**: Abort on failure (alignment is critical)

---

### Step 5: Assign Speaker Roles
- **Action**: Map SPEAKER_00/SPEAKER_01 to PATIENT/CLINICIAN
- **API**: `POST /api/alignment/assign_roles`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "aligned_segments": [ /* from Step 4 */ ],
    "speaker_mapping": {
      "SPEAKER_00": "CLINICIAN",
      "SPEAKER_01": "PATIENT"
    }
  }
  ```
- **Note**: Mapping can be manual (UI prompt) or heuristic-based
- **Output**:
  ```json
  {
    "segments": [
      {
        "segment_id": "uuid-1",
        "speaker_role": "CLINICIAN",
        "start": 0.0,
        "end": 5.2,
        "text": "Hello, how are you feeling today?"
      },
      {
        "segment_id": "uuid-2",
        "speaker_role": "PATIENT",
        "start": 5.2,
        "end": 10.1,
        "text": "I've been experiencing headaches."
      }
    ]
  }
  ```

---

### Step 6: Write to Index
- **Action**: Store speaker-labeled segments in unified index
- **API**: `POST /api/indexing/write`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "segments": [ /* from Step 5 */ ],
    "ingestion_mode": "OFFLINE"
  }
  ```
- **Output**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "indexed_segments": 45,
    "status": "success"
  }
  ```
- **Error Handling**: Retry up to 3 times

---

### Step 7: Log Success
- **Action**: Record completion in database
- **API**: `POST /api/ingestion/log`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_001",
    "status": "completed",
    "timestamp": "2024-03-15T14:30:00Z",
    "metadata": {
      "num_segments": 45,
      "duration_seconds": 300.5
    }
  }
  ```

---

## Error Scenarios

### Scenario 1: Diarization Fails
- **Cause**: Audio quality too poor
- **Action**: Mark interview as "failed_diarization"
- **User Notification**: "Could not identify speakers. Please check audio quality."

### Scenario 2: Transcription Fails
- **Cause**: Unsupported language
- **Action**: Retry with auto-detect language
- **Fallback**: Mark as "failed_transcription"

### Scenario 3: Alignment Mismatch
- **Cause**: Diarization and transcription timestamps don't align
- **Action**: Use best-effort overlap matching
- **Warning**: Flag segments with low confidence

---

## Workflow Diagram

```
Audio File Upload
    ↓
Validate File
    ↓
Run Diarization (Pyannote)
    ↓
Run Transcription (Whisper)
    ↓
Align Speakers + Transcript
    ↓
Assign Speaker Roles (PATIENT/CLINICIAN)
    ↓
Write to Unified Index
    ↓
Log Success
```

---

## Estimated Runtime

- Diarization: ~0.5x real-time (10 min audio → 5 min processing)
- Transcription: ~1x real-time (10 min audio → 10 min processing)
- Alignment: <10 seconds
- Indexing: <5 seconds

**Total**: ~15 minutes for 10-minute audio

---

## Testing Checklist

- [ ] Upload valid audio file → Full workflow completes
- [ ] Upload corrupted file → Validation fails gracefully
- [ ] Simulate diarization failure → Error logged, workflow stops
- [ ] Verify indexed segments have correct speaker roles
- [ ] Check duplicate prevention (re-uploading same file)
