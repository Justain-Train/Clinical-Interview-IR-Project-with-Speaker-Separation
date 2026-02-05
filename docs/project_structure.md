# Project Structure

Complete project skeleton for the Intelligent Clinical Interview IR System.

---

## 📁 Complete Directory Tree

```
Clinical-Interview-IR-Project-with-Speaker-Separation/
│
├── README.md                          # Main project overview
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
├── requirements.txt                   # Python dependencies
├── docker-compose.yml                 # Multi-container setup
│
├── docs/                              # 📚 Documentation
│   ├── architecture.md                # System design overview
│   ├── data_schemas.md                # Data structure definitions
│   ├── python_modules.md              # Module skeletons
│   ├── setup_guide.md                 # Installation instructions
│   ├── evaluation_protocol.md         # Evaluation procedures
│   └── system_flow_summary.md         # Flow explanation
│
├── n8n/                               # 🔄 Orchestration workflows
│   ├── README.md                      # n8n usage guide
│   └── workflows/
│       ├── offline_ingestion.md       # Offline pipeline flow
│       ├── live_ingestion.md          # Live pipeline flow
│       ├── unified_retrieval.md       # Retrieval workflow
│       └── evaluation.md              # Evaluation workflow
│
├── backend/                           # 🔧 Core Python backend
│   ├── README.md
│   ├── api/                           # FastAPI application
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   └── routes/
│   ├── models/                        # Domain models
│   │   └── schemas.py
│   └── utils/                         # Shared utilities
│       ├── audio_utils.py
│       ├── logging_config.py
│       └── db_utils.py
│
├── diarization/                       # 🎤 Speaker separation
│   ├── README.md
│   ├── pyannote_runner.py             # Diarization executor
│   └── config.py                      # Configuration
│
├── transcription/                     # 📝 Speech-to-text
│   ├── README.md
│   ├── whisper_client.py              # Whisper interface
│   ├── batch_transcribe.py            # Offline transcription
│   └── stream_transcribe.py           # Live transcription
│
├── alignment/                         # 🔗 Speaker-text alignment
│   ├── README.md
│   ├── speaker_aligner.py             # Alignment logic
│   └── segment_builder.py             # Segment creation
│
├── indexing/                          # 💾 Data indexing
│   ├── README.md
│   ├── index_writer.py                # Write to vector DB
│   ├── embedder.py                    # Embedding generation
│   └── schema_validator.py            # Data validation
│
├── retrieval/                         # 🔍 Query processing
│   ├── README.md
│   ├── retriever.py                   # Search logic
│   ├── ranker.py                      # Re-ranking
│   └── llm_explainer.py               # LLM explanations
│
├── evaluation/                        # 📊 Metrics & evaluation
│   ├── README.md
│   ├── metrics.py                     # IR metrics
│   ├── evaluator.py                   # Evaluation orchestrator
│   └── speaker_eval.py                # Speaker-specific metrics
│
├── frontend/                          # 🖥️ Web interface (optional)
│   ├── README.md
│   ├── app.py                         # Streamlit app
│   └── static/
│
├── tests/                             # ✅ Test suite
│   ├── README.md
│   ├── test_diarization/
│   ├── test_transcription/
│   ├── test_alignment/
│   ├── test_indexing/
│   ├── test_retrieval/
│   ├── test_evaluation/
│   ├── test_api/
│   ├── fixtures/
│   └── conftest.py
│
├── scripts/                           # 🛠️ Utility scripts
│   ├── README.md
│   ├── init_db.py                     # Database initialization
│   ├── create_collections.py          # Create vector collections
│   ├── download_sample_data.py        # Get sample data
│   ├── health_check.py                # System health check
│   ├── load_sample_data.py            # Load test data
│   ├── run_evaluation.py              # Run evaluation
│   └── reindex_all.py                 # Reindex all data
│
├── config/                            # ⚙️ Configuration files
│   ├── README.md
│   ├── diarization_config.yaml
│   ├── retrieval_config.yaml
│   ├── evaluation_config.yaml
│   └── livekit.yaml
│
└── data/                              # 💿 Local data (gitignored)
    ├── README.md
    ├── audio/                         # Uploaded audio files
    ├── postgres/                      # Local pgvector DB (dev only, not needed for Supabase cloud)
    ├── n8n/                           # n8n workflow data
    ├── ollama/                        # LLM models (if using local Ollama)
    ├── evaluation/                    # Test datasets and ground truth
    └── sample_audio/                  # Example files for testing
```

---

## 📦 Module Count

| Category | Count |
|----------|-------|
| Documentation files | 6 |
| Workflow descriptions | 4 |
| Python modules | ~25 |
| Configuration files | 4 |
| Test files | ~20 |
| Utility scripts | ~7 |

**Total Files (skeleton)**: ~70

---

## 🔄 Data Flow Summary

```
┌──────────────────────────────────────────────────┐
│         INGESTION LAYER (Divergent)              │
├─────────────────────┬────────────────────────────┤
│   OFFLINE PATH      │      LIVE PATH             │
│                     │                            │
│   Audio File        │   LiveKit Session          │
│       ↓             │         ↓                  │
│   Pyannote          │   Pre-separated Streams    │
│       ↓             │         ↓                  │
│   Whisper           │   Per-stream Whisper       │
│       ↓             │         ↓                  │
│   Alignment         │   (No alignment)           │
│       ↓             │         ↓                  │
└───────┼─────────────┴─────────┼──────────────────┘
        │                       │
        └───────────┬───────────┘
                    ↓
         TranscriptSegment (unified)
                    ↓
┌───────────────────────────────────────────────────┐
│         INDEXING LAYER (Unified)                  │
│   Validation → Embedding → Vector DB + Metadata   │
└─────────────────────┬─────────────────────────────┘
                      ↓
                Unified Index
                      ↓
┌───────────────────────────────────────────────────┐
│         RETRIEVAL LAYER (Unified)                 │
│   Query → Retrieve → Rank → Explain               │
└─────────────────────┬─────────────────────────────┘
                      ↓
                   Results
                      ↓
┌───────────────────────────────────────────────────┐
│         EVALUATION LAYER (Unified)                │
│   Metrics (Overall + Speaker-Specific)            │
└───────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Checklist

### Phase 1: Foundation
- [ ] Set up Python environment
- [ ] Install dependencies
- [ ] Start Docker containers (Qdrant, PostgreSQL, n8n)
- [ ] Initialize database schema

### Phase 2: Offline Pipeline
- [ ] Implement diarization module
- [ ] Implement transcription module
- [ ] Implement alignment module
- [ ] Test offline ingestion end-to-end

### Phase 3: Indexing
- [ ] Implement embedder
- [ ] Implement index writer
- [ ] Implement schema validator
- [ ] Index sample data

### Phase 4: Retrieval
- [ ] Implement semantic search
- [ ] Implement keyword search
- [ ] Implement hybrid search
- [ ] Add re-ranking
- [ ] (Optional) Add LLM explanation

### Phase 5: Evaluation
- [ ] Implement metrics (P@K, R@K, MAP, NDCG)
- [ ] Create test dataset
- [ ] Implement evaluator
- [ ] Generate evaluation report

### Phase 6: Live Pipeline (Optional)
- [ ] Set up LiveKit
- [ ] Implement streaming transcription
- [ ] Connect to unified indexing
- [ ] Test live ingestion

### Phase 7: Integration
- [ ] Create n8n workflows
- [ ] Connect all components via API
- [ ] Test full system
- [ ] Document results

---

## 📚 Documentation Reading Order

1. **README.md** - Project overview
2. **docs/architecture.md** - System design
3. **docs/data_schemas.md** - Data structures
4. **docs/setup_guide.md** - Get started
5. **docs/python_modules.md** - Module details
6. **n8n/workflows/*.md** - Workflow logic
7. **docs/evaluation_protocol.md** - How to evaluate
8. **docs/system_flow_summary.md** - Why this design

---

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd Clinical-Interview-IR-Project-with-Speaker-Separation

# 2. Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start services
docker-compose up -d

# 5. Initialize database
python scripts/init_db.py

# 6. Load sample data
python scripts/load_sample_data.py

# 7. Start backend API
cd backend
uvicorn api.main:app --reload

# 8. Run tests
pytest tests/

# 9. Run evaluation
python scripts/run_evaluation.py
```

---

## 📝 Next Steps

After reviewing this skeleton:

1. **Understand the architecture** (read docs/)
2. **Set up the environment** (follow setup_guide.md)
3. **Implement incrementally** (start with one module)
4. **Test continuously** (write tests alongside code)
5. **Evaluate regularly** (run evaluation after each major change)
6. **Iterate and improve** (use evaluation results to guide improvements)

---

## 🤝 Contributing

This is a course/research project. To contribute:

1. Create a feature branch
2. Implement the module (follow skeleton structure)
3. Add unit tests
4. Update documentation
5. Submit pull request

---

## 📧 Support

For questions or issues:
- Check documentation in `/docs`
- Review workflow descriptions in `/n8n/workflows`
- Consult module README files
- Open an issue on GitHub

---

**Last Updated**: 2024-03-15  
**Version**: 1.0.0-skeleton
