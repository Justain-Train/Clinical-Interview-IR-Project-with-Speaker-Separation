# Live Ingestion Workflow

**Purpose**: Process real-time clinical interviews from LiveKit with pre-separated speaker streams.

---

## Trigger

**Type**: Webhook from LiveKit  
**Event**: `participant.joined` or `track.published`  
**Input**:
```json
{
  "event": "track.published",
  "room_name": "clinical_interview_2024_002",
  "participant_id": "participant_001",
  "track_id": "audio_track_patient",
  "speaker_role": "PATIENT",
  "timestamp": "2024-03-15T14:30:00Z"
}
```

---

## Workflow Steps

### Step 1: Initialize Interview Session
- **Action**: Create interview record if new session
- **API**: `POST /api/interviews/init`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_002",
    "room_name": "clinical_interview_2024_002",
    "ingestion_mode": "LIVE",
    "started_at": "2024-03-15T14:30:00Z"
  }
  ```
- **Output**:
  ```json
  {
    "interview_id": "interview_2024_002",
    "status": "initialized"
  }
  ```
- **Idempotency**: If already exists, return existing record

---

### Step 2: Subscribe to Speaker Stream
- **Action**: Connect to LiveKit audio stream for this participant
- **API**: `POST /api/transcription/stream/subscribe`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_002",
    "participant_id": "participant_001",
    "track_id": "audio_track_patient",
    "speaker_role": "PATIENT"
  }
  ```
- **Output**:
  ```json
  {
    "stream_id": "stream_001",
    "status": "subscribed"
  }
  ```
- **Note**: This starts a background streaming transcription process

---

### Step 3: Real-time Transcription
- **Action**: Whisper processes audio chunks as they arrive
- **Implementation**: Runs asynchronously in backend (not n8n)
- **API**: Internal streaming pipeline (not HTTP)
- **Output**: Emits TranscriptSegment events to message queue

**Segment Event Example**:
```json
{
  "segment_id": "uuid-live-001",
  "interview_id": "interview_2024_002",
  "speaker_role": "PATIENT",
  "start_time": 12.5,
  "end_time": 18.3,
  "text": "I've been having trouble sleeping lately.",
  "confidence": 0.92,
  "ingestion_mode": "LIVE",
  "created_at": "2024-03-15T14:30:18Z"
}
```

---

### Step 4: Continuous Indexing
- **Trigger**: Message queue event (e.g., Redis Pub/Sub)
- **Action**: Write each segment to index as it's transcribed
- **API**: `POST /api/indexing/write`
- **Input**: TranscriptSegment from Step 3
- **Output**:
  ```json
  {
    "segment_id": "uuid-live-001",
    "status": "indexed"
  }
  ```
- **Error Handling**: Buffer failed segments, retry later

---

### Step 5: Session End Detection
- **Trigger**: LiveKit webhook `participant.left` or room closed
- **Input**:
  ```json
  {
    "event": "room.ended",
    "room_name": "clinical_interview_2024_002",
    "ended_at": "2024-03-15T15:00:00Z"
  }
  ```

---

### Step 6: Finalize Interview
- **Action**: Mark interview as complete, compute stats
- **API**: `POST /api/interviews/finalize`
- **Input**:
  ```json
  {
    "interview_id": "interview_2024_002",
    "ended_at": "2024-03-15T15:00:00Z"
  }
  ```
- **Output**:
  ```json
  {
    "interview_id": "interview_2024_002",
    "status": "completed",
    "total_segments": 87,
    "duration_seconds": 1800,
    "speakers": ["PATIENT", "CLINICIAN"]
  }
  ```

---

## Parallel Processing

Unlike offline ingestion, live mode processes **multiple speakers simultaneously**:

```
┌─────────────────┐
│  LiveKit Room   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐
│Patient│  │Clinician│
│Stream │  │Stream  │
└───┬──┘  └──┬────┘
    │         │
┌───▼──┐  ┌──▼────┐
│Whisper│ │Whisper│
│Process│ │Process│
└───┬──┘  └──┬────┘
    │         │
    └────┬────┘
         │
    ┌────▼────┐
    │ Indexing│
    └─────────┘
```

Each speaker stream has its own transcription process.

---

## Error Scenarios

### Scenario 1: Stream Connection Lost
- **Cause**: Network interruption
- **Action**: Attempt reconnection (3 retries)
- **Fallback**: Mark interview as "partial_data"

### Scenario 2: Transcription Lag
- **Cause**: Slow Whisper processing
- **Action**: Buffer audio chunks, warn if buffer > 30 seconds
- **Mitigation**: Use smaller Whisper model for real-time

### Scenario 3: Speaker Role Unknown
- **Cause**: LiveKit doesn't provide role metadata
- **Action**: Tag as "UNKNOWN", allow manual correction later

---

## Workflow Diagram

```
LiveKit Session Starts
    ↓
Initialize Interview Record
    ↓
┌──────────────┬──────────────┐
│              │              │
Patient Stream │  Clinician Stream
    ↓          │      ↓
Whisper (Real-time)  Whisper (Real-time)
    ↓          │      ↓
Segment Events │  Segment Events
    ↓          │      ↓
└──────────────┴──────────────┘
    ↓
Continuous Indexing (as segments arrive)
    ↓
Session Ends
    ↓
Finalize Interview
```

---

## Key Differences from Offline

| Aspect | Offline | Live |
|--------|---------|------|
| Trigger | Manual upload | Webhook |
| Diarization | Pyannote (required) | Not needed (pre-separated) |
| Transcription | Batch | Streaming |
| Alignment | Post-processing | Not needed |
| Latency | Minutes | Seconds |
| Indexing | After completion | Continuous |

---

## LiveKit Configuration

**Room Settings**:
- Enable speaker separation (`auto_subscribe_audio: true`)
- Require participant metadata (must include `speaker_role`)

**Webhook Settings**:
- Events to subscribe: `track.published`, `track.unpublished`, `room.ended`
- Webhook URL: `https://your-n8n-instance.com/webhook/livekit`

---

## Testing Checklist

- [ ] Start LiveKit room → Interview initialized
- [ ] Publish audio track → Transcription starts
- [ ] Verify segments appear in index within 5 seconds
- [ ] End session → Interview marked as completed
- [ ] Test with missing speaker_role metadata → Logs error
- [ ] Simulate network interruption → Reconnection succeeds
