# Setup Guide

Complete guide to set up the development environment from scratch.

---

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows (WSL recommended)
- **Python**: 3.10 or higher
- **RAM**: Minimum 8GB, 16GB recommended (for local Whisper)
- **GPU**: Optional, but recommended for faster transcription (CUDA-compatible)
- **Disk**: ~10GB for models and sample data

### Software Dependencies
- Docker & Docker Compose
- Git
- Node.js 18+ (for n8n)
- ffmpeg (for audio processing)

---

## Step 1: Clone Repository

```bash
git clone https://github.com/your-org/clinical-interview-ir.git
cd clinical-interview-ir
```

---

## Step 2: Python Environment Setup

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Requirements.txt Contents
```txt
# Core ML/NLP
torch>=2.0.0
transformers>=4.30.0
sentence-transformers>=2.2.0
openai-whisper>=20230314

# Diarization
pyannote.audio>=3.1.0

# Vector Database
qdrant-client>=1.5.0
# OR
# pymilvus>=2.3.0

# Backend
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0  # PostgreSQL driver
aiosqlite>=0.19.0  # SQLite async support

# LiveKit
livekit>=0.10.0
livekit-api>=0.5.0

# Evaluation
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
httpx>=0.24.0
```

---

## Step 3: Download Models

### Pyannote Models (Requires HuggingFace Token)

1. Create account at https://huggingface.co
2. Accept model terms:
   - https://huggingface.co/pyannote/speaker-diarization
   - https://huggingface.co/pyannote/segmentation
3. Get access token from https://huggingface.co/settings/tokens
4. Set environment variable:
   ```bash
   export HUGGINGFACE_TOKEN="your_token_here"
   ```

5. Download models (done automatically on first run)

### Whisper Models

```python
# Run in Python to download
import whisper
whisper.load_model("base")  # ~140MB
# OR
whisper.load_model("small")  # ~460MB (better accuracy)
```

### Sentence-BERT Models

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')  # Auto-downloads
```

---

## Step 4: Database Setup with Supabase

### Option A: Supabase Cloud (Recommended for Production)

1. **Sign up at https://supabase.com**
2. **Create new project**:
   - Name: `clinical-interview-ir`
   - Database password: (save securely)
   - Region: Choose closest
3. **Get credentials** from Project Settings → API
4. **Enable pgvector** in Database → Extensions
5. **Run initialization**:
   ```bash
   python scripts/init_supabase_db.py
   ```

See detailed guide: `/docs/supabase_setup.md`

### Option B: Local PostgreSQL with pgvector (Development)

**Using Docker**:
```bash
docker-compose up -d postgres
```

This starts PostgreSQL with pgvector extension.

**Create Schema**:
```bash
python scripts/init_supabase_db.py
```

**Note**: For local development, set:
```bash
DATABASE_URL=postgresql://postgres:dev_password@localhost:5432/clinical_interviews
```

---

## Step 5: n8n Setup

### Using Docker

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=admin123 \
  -v $(pwd)/data/n8n:/home/node/.n8n \
  n8nio/n8n
```

Access at: http://localhost:5678

### Configure Credentials

1. Go to Settings → Credentials
2. Add HTTP Request credential:
   - Name: "Backend API"
   - Authentication: None (or Basic if needed)
   - Base URL: `http://host.docker.internal:8000`

---

## Step 6: LiveKit Setup (Optional)

### For Live Ingestion Only

```bash
docker run -d \
  --name livekit \
  -p 7880:7880 \
  -p 7881:7881/udp \
  -e LIVEKIT_KEYS="devkey: secret" \
  -v $(pwd)/config/livekit.yaml:/livekit.yaml \
  livekit/livekit-server \
  --config /livekit.yaml
```

---

## Step 7: Environment Configuration

### Create `.env` File

```bash
cp .env.example .env
```

### Edit `.env`

```bash
# Python
PYTHONPATH=./backend

# Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
POSTGRES_URI=postgresql://clinical_ir:dev_password@localhost:5432/clinical_interviews

# Models
HUGGINGFACE_TOKEN=your_token_here
WHISPER_MODEL=base
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# API
API_HOST=0.0.0.0
API_PORT=8000

# LiveKit (optional)
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_WS_URL=ws://localhost:7880

# LLM (optional, for explanations)
LLM_MODEL=llama-3.1-8b
LLM_API_URL=http://localhost:11434  # Ollama endpoint
```

---

## Step 8: Initialize Database Schema

```bash
python scripts/init_supabase_db.py
```

This creates:
- Tables: `interviews`, `segments`, `evaluation_datasets`, `evaluation_results`
- Vector indexes for fast similarity search
- Full-text search indexes for keyword search
- Search functions for semantic and hybrid search

---

## Step 9: Start Backend API

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Verify at: http://localhost:8000/docs (FastAPI Swagger UI)

---

## Step 10: Test Installation

### Run Health Checks

```bash
python scripts/health_check.py
```

Expected output:
```
✓ Python environment: OK
✓ Supabase connection: OK
✓ pgvector extension: OK
✓ Pyannote model: OK
✓ Whisper model: OK
✓ Sentence-BERT model: OK
✓ Backend API: OK
✓ n8n: OK
```

---

## Step 11: Load Sample Data

```bash
python scripts/load_sample_data.py
```

This will:
1. Download sample clinical interview audio
2. Run offline ingestion pipeline
3. Index ~5 sample interviews
4. Create evaluation test set

---

## Verify Setup

### Test Offline Ingestion

```bash
curl -X POST http://localhost:8000/api/diarization/run \
  -H "Content-Type: application/json" \
  -d '{
    "interview_id": "test_001",
    "audio_path": "/data/sample_audio/interview_001.wav"
  }'
```

### Test Retrieval

```bash
curl -X POST http://localhost:8000/api/retrieval/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What symptoms did the patient report?",
    "speaker_filter": "PATIENT",
    "top_k": 5
  }'
```

---

## Common Issues

### Issue: Pyannote model not loading
**Solution**: Ensure HuggingFace token is set and model terms accepted

### Issue: Whisper CUDA not detected
**Solution**: Install PyTorch with CUDA support:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Supabase connection refused
**Solution**: 
- Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
- Verify project is active in Supabase dashboard
- Check if IP is allowed (Database Settings → Connection Pooling)

### Issue: n8n can't reach backend API
**Solution**: Use `host.docker.internal` instead of `localhost` in n8n HTTP nodes

---

## Development Workflow

1. **Make changes** to Python code in `/backend`
2. **API auto-reloads** (if using `--reload`)
3. **Test in n8n** by triggering workflows
4. **Check logs** in terminal or `/logs` directory
5. **Run tests**: `pytest tests/`

---

## Production Deployment Notes

This setup is for **development only**. For production:

- Use managed databases (not Docker containers)
- Set up proper authentication (not basic auth)
- Use HTTPS for all endpoints
- Deploy n8n separately (n8n Cloud or self-hosted)
- Use production-grade Whisper (API or optimized deployment)
- Add monitoring (Prometheus + Grafana)
- Set up backup/restore procedures

---

## Next Steps

1. Read `/docs/architecture.md` to understand system design
2. Review `/n8n/workflows/*.md` to understand data flow
3. Implement skeletons in `/docs/python_modules.md`
4. Create evaluation test set
5. Run first evaluation
