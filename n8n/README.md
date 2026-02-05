# n8n Orchestration Workflows

This folder contains **logical workflow descriptions** for n8n.

---

## Purpose

n8n acts as the **orchestration layer** that:
- Triggers Python scripts at the right time
- Passes data between components
- Handles retries and error logging
- Provides visual debugging

**Important**: n8n does NOT contain ML logic. All heavy lifting happens in Python.

---

## Workflow Files

Each `.md` file describes a workflow's **logical structure**:

1. **`offline_ingestion.md`** - Audio file → Diarization → Transcription → Alignment → Index
2. **`live_ingestion.md`** - LiveKit webhook → Per-speaker transcription → Index
3. **`unified_retrieval.md`** - Query → Retrieve → Rank → LLM explanation
4. **`evaluation.md`** - Load test set → Run retrieval → Compute metrics

---

## How to Use These Workflows

### Step 1: Read the Logical Flow
Each markdown file shows:
- Trigger conditions
- API endpoints called
- Data transformations
- Error handling

### Step 2: Implement in n8n UI
For each step in the logical flow:
- Add a node (HTTP Request, Code, etc.)
- Configure endpoint URL and method
- Map input/output data
- Set error handling

### Step 3: Connect to Backend
All workflows call FastAPI endpoints:
- `POST /api/diarization/run`
- `POST /api/transcription/batch`
- `POST /api/indexing/write`
- `POST /api/retrieval/query`

---

## Workflow Design Principles

### 1. Stateless API Calls
Each n8n node calls a Python endpoint that:
- Receives input as JSON
- Processes synchronously (or returns task ID)
- Returns result or error

### 2. Error Propagation
If a Python endpoint fails:
- n8n logs the error
- Optionally retries
- Does NOT silently continue

### 3. Data Validation
n8n validates:
- Required fields are present
- File paths exist
- IDs are valid UUIDs

Python endpoints do deeper validation.

### 4. Modularity
Each workflow is independent:
- Can be tested separately
- Can be triggered manually
- Can be scheduled (for batch jobs)

---

## Local Development Setup

### Run n8n Locally
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

Access at: `http://localhost:5678`

### Configure Credentials
Add credentials for:
- FastAPI backend (base URL: `http://localhost:8000`)
- LiveKit webhooks (if using live ingestion)

### Import Workflows
Once implemented, workflows can be exported as JSON and shared.

---

## Testing Workflows

### Manual Trigger
- Open n8n UI
- Click "Execute Workflow"
- Provide test input JSON
- Check output at each node

### Automated Testing
- Use n8n CLI or API
- Trigger workflows programmatically
- Assert on output format

---

## Example: Calling a Python Endpoint from n8n

**Logical Step**: "Run Pyannote diarization"

**n8n Implementation**:
- Node type: HTTP Request
- Method: POST
- URL: `http://localhost:8000/api/diarization/run`
- Body:
  ```json
  {
    "interview_id": "interview_2024_001",
    "audio_path": "/data/audio/interview_001.wav"
  }
  ```
- Response format:
  ```json
  {
    "interview_id": "interview_2024_001",
    "segments": [
      {"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00"},
      {"start": 5.2, "end": 10.1, "speaker": "SPEAKER_01"}
    ]
  }
  ```

**Next Node**: Pass `interview_id` and `segments` to transcription endpoint.

---

## Workflow Versioning

As the system evolves:
- Keep old workflow versions in `workflows/archive/`
- Document changes in workflow descriptions
- Test new versions against sample data before production

---

## n8n Best Practices for This Project

1. **Use descriptive node names**: "Diarize Audio", not "HTTP Request 1"
2. **Add notes to complex nodes**: Explain non-obvious logic
3. **Set timeouts**: Transcription can take minutes
4. **Enable error workflows**: Log to file/DB on failure
5. **Use environment variables**: Don't hardcode URLs or API keys

---

## Future Enhancements

- **Monitoring**: Add n8n nodes to send metrics to Prometheus
- **Scheduling**: Trigger evaluation weekly on new test sets
- **Webhooks**: Let external systems trigger ingestion
- **Parallel processing**: Use n8n's split/merge nodes for batch jobs
