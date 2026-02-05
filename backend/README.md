# Backend API

FastAPI-based REST API for all system components.

---

## Purpose

Provide HTTP endpoints for n8n workflows and external clients.

---

## Structure

```
/backend/
  ├── api/
  │   ├── main.py              # FastAPI app
  │   ├── models.py            # Pydantic request/response models
  │   ├── dependencies.py      # DI and configuration
  │   ├── routes/
  │   │   ├── diarization.py
  │   │   ├── transcription.py
  │   │   ├── alignment.py
  │   │   ├── indexing.py
  │   │   ├── retrieval.py
  │   │   └── evaluation.py
  ├── models/
  │   └── schemas.py           # Domain models (TranscriptSegment, etc.)
  └── utils/
      ├── audio_utils.py
      ├── logging_config.py
      └── db_utils.py
```

---

## Key Endpoints

### Diarization
- `POST /api/diarization/run` - Run speaker diarization

### Transcription
- `POST /api/transcription/batch` - Batch transcription
- `POST /api/transcription/stream/subscribe` - Subscribe to live stream

### Alignment
- `POST /api/alignment/align` - Align speakers with transcript
- `POST /api/alignment/assign_roles` - Map speakers to roles

### Indexing
- `POST /api/indexing/write` - Write segments to index
- `GET /api/indexing/status` - Check indexing status

### Retrieval
- `POST /api/retrieval/query` - Query for segments
- `POST /api/retrieval/batch` - Batch queries

### Evaluation
- `POST /api/evaluation/run` - Run evaluation
- `GET /api/evaluation/results/{eval_id}` - Get results

---

## Running

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs at: `http://localhost:8000/docs`

---

## Notes

- All endpoints return JSON
- Async support for long-running tasks
- Error handling with proper HTTP status codes
- CORS enabled for frontend development
