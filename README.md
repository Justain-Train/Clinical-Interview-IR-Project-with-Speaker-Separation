# Intelligent Clinical Interview Analysis, Summarization & Retrieval System
## with Speaker Separation (Hybrid Architecture - Option C)

An academic information retrieval system that processes clinical interviews through both offline and live ingestion paths, converging into a unified retrieval, ranking, and evaluation pipeline.

---

## 🏗️ Architectural Overview

### Core Principle: Two Ingestion Paths, One Unified Retrieval Core

**Offline Path:**
- Audio file upload → Pyannote diarization → Whisper transcription → Speaker alignment → Unified storage

**Live Path:**
- LiveKit real-time → Speaker-separated streams → Per-speaker Whisper → Unified storage

**Unified Backend:**
- Shared data schemas
- Single indexing logic
- Common retrieval/ranking algorithms
- Unified evaluation pipeline

---

## 📂 Repository Structure

```
/n8n/                       # Orchestration workflow definitions (logical flows, not full implementations)
  ├── workflows/
  │   ├── offline_ingestion.md
  │   ├── live_ingestion.md
  │   ├── unified_retrieval.md
  │   └── evaluation.md
  └── README.md

/backend/                   # Core Python-based ML/IR logic
  ├── api/                  # REST API endpoints for n8n integration
  ├── models/               # Data models and schema definitions
  ├── utils/                # Shared utilities
  └── README.md

/diarization/               # Speaker separation logic for offline audio
  ├── pyannote_runner.py    # Pyannote.audio wrapper
  ├── config.py             # Diarization configuration
  └── README.md

/transcription/             # Speech-to-text processing
  ├── whisper_client.py     # Whisper API/local wrapper
  ├── batch_transcribe.py   # Offline batch processing
  ├── stream_transcribe.py  # Live stream processing
  └── README.md

/alignment/                 # Speaker-text alignment for offline path
  ├── speaker_aligner.py    # Maps diarization output to transcripts
  ├── segment_builder.py    # Creates speaker-labeled segments
  └── README.md

/indexing/                  # Unified indexing for both ingestion paths
  ├── index_writer.py       # Write segments to vector/keyword index
  ├── embedder.py           # Sentence/semantic embeddings
  ├── schema_validator.py   # Ensures data consistency
  └── README.md

/retrieval/                 # Query processing and ranking
  ├── retriever.py          # Speaker-aware retrieval logic
  ├── ranker.py             # Re-ranking algorithms
  ├── llm_explainer.py      # LLM-based answer generation
  └── README.md

/evaluation/                # Metrics and benchmarking
  ├── metrics.py            # Precision@K, Recall@K, NDCG
  ├── evaluator.py          # Evaluation orchestrator
  ├── speaker_eval.py       # Patient-only/clinician-only evaluation
  └── README.md

/frontend/                  # (Optional) Simple query interface
  ├── static/
  ├── templates/
  └── README.md

/docs/                      # Documentation and design docs
  ├── architecture.md
  ├── data_schemas.md
  ├── setup_guide.md
  └── evaluation_protocol.md

/tests/                     # Unit and integration tests
  ├── test_diarization/
  ├── test_retrieval/
  └── test_evaluation/

/data/                      # Sample data and test fixtures (gitignored)
  ├── sample_audio/
  ├── ground_truth/
  └── README.md

/config/                    # Configuration files
  ├── diarization_config.yaml
  ├── retrieval_config.yaml
  └── evaluation_config.yaml

requirements.txt            # Python dependencies
docker-compose.yml          # Local development environment
.env.example                # Environment variables template
.gitignore
LICENSE
```

---

## 🎯 Folder Responsibilities

### `/n8n`
Orchestration layer. Contains logical workflow descriptions (NOT full JSON exports) showing how components are triggered and connected.

### `/backend`
Core API layer that n8n calls. Exposes endpoints for triggering diarization, transcription, indexing, and retrieval.

### `/diarization`
Offline-only. Runs Pyannote.audio to identify "who spoke when" from audio files.

### `/transcription`
Dual-mode. Batch processing for offline, streaming for live. Both use Whisper.

### `/alignment`
Offline-only. Merges diarization timestamps with transcription text to create speaker-labeled segments.

### `/indexing`
Unified. Receives speaker-labeled segments from BOTH paths and writes to shared index (vector DB + metadata).

### `/retrieval`
Unified. Handles queries, retrieves relevant segments, ranks them, and optionally generates LLM explanations.

### `/evaluation`
Unified. Computes IR metrics and speaker-specific performance on test sets.

### `/frontend`
Optional web UI for demonstrations and manual testing.

### `/docs`
Design documents, setup guides, and architectural decisions.

---

## 🔄 System Integration Flow

### Offline Ingestion
```
User uploads audio
    ↓
n8n triggers /api/diarization/run
    ↓
Pyannote identifies speaker segments
    ↓
n8n triggers /api/transcription/batch
    ↓
Whisper transcribes entire audio
    ↓
n8n triggers /api/alignment/align
    ↓
Speaker segments + transcript → labeled segments
    ↓
n8n triggers /api/indexing/write
    ↓
Segments stored in unified index
```

### Live Ingestion
```
LiveKit session starts
    ↓
Webhook → n8n triggers /api/transcription/stream
    ↓
Per-speaker audio → Whisper (already separated)
    ↓
Direct speaker-labeled segments
    ↓
n8n triggers /api/indexing/write
    ↓
Segments stored in unified index
```

### Retrieval (Same for Both)
```
User query
    ↓
n8n triggers /api/retrieval/query
    ↓
Retrieve K candidates (speaker-aware filters optional)
    ↓
Rank by relevance
    ↓
LLM generates explanation grounded in segments
    ↓
Return results
```

---

## 📋 Next Steps

1. Review `/docs/architecture.md` for detailed design
2. Check `/docs/data_schemas.md` for data structures
3. Follow `/docs/setup_guide.md` for environment setup
4. Implement skeletons incrementally per module
5. Run evaluation pipeline on sample data

---

## ⚠️ Important Constraints

- **FREE tier only**: Whisper local/API free tier, Pyannote community model, open-source vector DB
- **No medical advice**: System is for IR research and education only
- **n8n for orchestration only**: ML logic lives in Python
- **Reproducible**: Fixed configs, seeded evaluation, documented protocols

---

## 📊 Why This Architecture?

**Modularity**: Each component has one clear responsibility  
**Unification**: Offline and live paths share 80% of code  
**Evaluation-friendly**: Single evaluation pipeline tests both modes  
**Course-ready**: Clear separation allows incremental teaching  
**Speaker-aware**: First-class support for patient/clinician distinction  

---

## 📝 License

MIT License - For academic and educational use
