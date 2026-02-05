# System Architecture

## Hybrid Ingestion with Unified Retrieval (Option C)

---

## Design Philosophy

This system implements **convergent architecture**:
- Multiple ingestion methods (offline file upload, live streaming)
- Single source of truth (unified index)
- Shared retrieval and evaluation logic

**Key Insight**: Speaker separation happens at different stages depending on ingestion mode, but the result is always the same: speaker-labeled transcript segments.

---

## Component Layers

### Layer 1: Ingestion (Divergent)

**Offline Pipeline**
- Input: Audio file (MP3, WAV, etc.)
- Diarization: Pyannote.audio identifies speaker boundaries
- Transcription: Whisper processes entire audio
- Alignment: Merge diarization timestamps with transcript
- Output: Speaker-labeled segments

**Live Pipeline**
- Input: LiveKit real-time session
- Separation: LiveKit provides pre-separated speaker streams
- Transcription: Whisper processes each stream independently
- Output: Speaker-labeled segments (no alignment needed)

### Layer 2: Indexing (Unified)

Both pipelines feed into:
- Schema validation (ensures consistency)
- Embedding generation (semantic vectors)
- Index writing (vector DB + metadata store)

### Layer 3: Retrieval (Unified)

Single retrieval engine supports:
- Keyword search
- Semantic search
- Speaker-filtered search (patient-only, clinician-only)
- Hybrid ranking

### Layer 4: Explanation (Unified)

LLM receives:
- Original query
- Retrieved segments with speaker labels
- Generates grounded answer

### Layer 5: Evaluation (Unified)

Metrics computed identically for offline and live:
- Precision@K, Recall@K
- Speaker-specific metrics
- Temporal coherence (optional)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                      │
├──────────────────────────┬──────────────────────────────┤
│   OFFLINE PATH           │      LIVE PATH               │
│                          │                              │
│  Audio File              │   LiveKit Session            │
│      ↓                   │         ↓                    │
│  Pyannote Diarization    │   Pre-separated Streams      │
│      ↓                   │         ↓                    │
│  Whisper Transcription   │   Per-stream Whisper         │
│      ↓                   │         ↓                    │
│  Speaker Alignment       │   (No alignment needed)      │
│      ↓                   │         ↓                    │
└──────┼───────────────────┴─────────┼────────────────────┘
       │                             │
       └──────────┬──────────────────┘
                  ↓
         Speaker-labeled Segments
                  ↓
┌─────────────────────────────────────────────────────────┐
│               UNIFIED INDEXING LAYER                    │
│                                                         │
│  Schema Validation → Embedding → Index Write           │
└────────────────────┬────────────────────────────────────┘
                     ↓
              Unified Index
                     ↓
┌─────────────────────────────────────────────────────────┐
│              UNIFIED RETRIEVAL LAYER                    │
│                                                         │
│  Query → Retrieve → Rank → LLM Explain                 │
└────────────────────┬────────────────────────────────────┘
                     ↓
                  Results
                     ↓
┌─────────────────────────────────────────────────────────┐
│             UNIFIED EVALUATION LAYER                    │
│                                                         │
│  Precision@K | Recall@K | Speaker-specific Metrics     │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack (Free Tier)

| Component | Technology | Why |
|-----------|-----------|-----|
| Orchestration | n8n (self-hosted) | Visual workflow, easy debugging |
| Diarization | Pyannote.audio | State-of-art, free community models |
| Transcription | Whisper (local) | High accuracy, runs locally |
| Live Audio | LiveKit (free tier) | Speaker separation built-in |
| Database | Supabase (PostgreSQL + pgvector) | Unified DB + vector search, free tier |
| Embeddings | Sentence-BERT | Free, good for clinical text |
| LLM | Llama 3.x (local) | Free, runs on consumer GPU |
| Backend | FastAPI | Async, easy integration with n8n |
| Frontend | Streamlit | Rapid prototyping |

---

## Speaker Awareness Design

### Why Speaker Labels Matter

In clinical interviews:
- **Patient utterances** contain symptoms, history, concerns
- **Clinician utterances** contain questions, diagnoses, recommendations

Retrieval should allow:
- "What symptoms did the patient report?" → Patient-only search
- "What questions did the clinician ask?" → Clinician-only search
- "What was discussed about headaches?" → Both speakers

### Implementation

Each segment has:
```
speaker_role: PATIENT | CLINICIAN | UNKNOWN
```

Retrieval supports:
```
filter: { speaker_role: "PATIENT" }
```

Evaluation computes metrics separately:
- Overall P@K, R@K
- Patient-only P@K, R@K
- Clinician-only P@K, R@K

---

## Convergence Points

Both ingestion paths MUST produce segments with:
1. `interview_id` (unique identifier)
2. `speaker_role` (PATIENT/CLINICIAN)
3. `start_time`, `end_time` (seconds)
4. `text` (transcribed utterance)
5. `ingestion_mode` (offline/live) — for debugging only

This ensures:
- Indexing code is identical
- Retrieval code is identical
- Evaluation code is identical

---

## Why This Architecture Supports IR Research

1. **Ground Truth Flexibility**: Offline path allows careful annotation
2. **Real-world Testing**: Live path tests production scenarios
3. **Speaker-aware Retrieval**: Novel IR problem (not just keyword matching)
4. **Reproducibility**: Same evaluation pipeline for both modes
5. **Modularity**: Each component can be improved independently

---

## Scalability Considerations

Current design is for **single-machine deployment**:
- ~100 interviews
- ~10 concurrent live sessions
- Research and teaching use case

For production scale:
- Replace local Whisper with API
- Distribute indexing
- Add queue system (Celery/Redis)

This skeleton focuses on **correctness and clarity**, not scale.
