# System Flow Summary

This document explains how offline and live pipelines converge and why this architecture supports conversational IR.

---

## Pipeline Convergence

### The Core Insight

**Problem**: Clinical interviews can be captured two ways:
1. **Offline**: Record audio, process later
2. **Live**: Stream audio, process in real-time

**Challenge**: How to maintain consistency while supporting both modes?

**Solution**: Converge at the data schema level.

---

## Convergence Points

### Point 1: Data Schema
Both pipelines produce **identical output**:
```python
TranscriptSegment(
    segment_id=UUID,
    interview_id=str,
    speaker_role=SpeakerRole,  # PATIENT | CLINICIAN
    start_time=float,
    end_time=float,
    text=str,
    ingestion_mode=str  # OFFLINE | LIVE (for tracking only)
)
```

**Implication**: Indexing code doesn't know (or care) which pipeline created the segment.

---

### Point 2: Indexing Logic
Single `index_writer.py` handles both:
- Offline segments (with diarization + alignment)
- Live segments (direct from LiveKit)

**Validation**: Schema validator ensures consistency before writing.

---

### Point 3: Retrieval Logic
Single `retriever.py` searches across:
- Offline-indexed interviews
- Live-indexed interviews
- Mixed (both in same query)

**Filters work identically**:
```python
query = RetrievalQuery(
    query_text="What symptoms were reported?",
    speaker_filter="PATIENT",  # Works for both modes
    interview_ids=["offline_001", "live_002"]  # Can mix!
)
```

---

### Point 4: Evaluation Logic
Single `evaluator.py` computes metrics:
- On offline-ingested data
- On live-ingested data
- On combined datasets

**Why this matters**: Proves the system works regardless of ingestion method.

---

## Divergence Points (By Design)

### Diarization
- **Offline**: Required (Pyannote separates speakers)
- **Live**: Not needed (LiveKit already separates)

**Convergence**: After this step, both have speaker labels.

---

### Transcription
- **Offline**: Batch processing (entire audio at once)
- **Live**: Streaming (chunks as they arrive)

**Convergence**: Both use Whisper, both produce timestamped text.

---

### Alignment
- **Offline**: Required (merge diarization + transcription)
- **Live**: Not needed (already aligned)

**Convergence**: After this step, both have `(speaker, time, text)` tuples.

---

## Why This Supports Conversational IR

### 1. Speaker Awareness is First-Class

Traditional IR treats documents as atomic units.  
This system treats **speaker turns** as atomic units.

**Benefit**: Can answer questions like:
- "What did the **patient** say about pain?" (not just "what was said")
- "What questions did the **clinician** ask?" (role-specific retrieval)

---

### 2. Temporal Grounding

Each segment has `start_time` and `end_time`.

**Benefit**: Can support queries like:
- "What was discussed in the first 5 minutes?" (future extension)
- "What did the patient say after the diagnosis?" (temporal reasoning)

---

### 3. Turn-Level Granularity

Segments correspond to **conversational turns**, not arbitrary chunks.

**Benefit**: Retrieved segments are semantically coherent (complete thoughts).

**Example**:
```
❌ Bad chunking: "...I've been experiencing severe head"
✓ Good segmentation: "I've been experiencing severe headaches for two weeks."
```

---

### 4. Multi-Modal Extension Ready

Schema includes `metadata` field, allowing future extensions:
```python
metadata = {
    "sentiment": {"polarity": -0.5, "confidence": 0.8},
    "entities": [{"type": "SYMPTOM", "text": "headache"}],
    "audio_features": {"pitch_mean": 220.5, "energy": 0.65}
}
```

**Benefit**: Can incorporate non-textual signals (tone, emotion, prosody).

---

## Why This Design is Easy to Evaluate

### 1. Single Evaluation Pipeline
No need to write separate eval code for offline vs. live.

**Workflow**:
```
Create test set → Run evaluation → Compare modes
```

**Metric**: If P@5 (offline) ≈ P@5 (live), architecture is validated.

---

### 2. Reproducible Experiments
All configuration is externalized:
- `diarization_config.yaml`
- `retrieval_config.yaml`
- `eval_config.yaml`

**Benefit**: Re-run exact same experiment months later.

---

### 3. Modular Improvement
Each component can be improved independently:
- Swap Pyannote for better diarization → Re-evaluate
- Try different embeddings → Re-evaluate
- Improve re-ranking → Re-evaluate

**Benefit**: Isolate the impact of each change.

---

### 4. Speaker-Specific Metrics
Built-in support for:
```python
metrics = {
    "overall": {"P@5": 0.68},
    "PATIENT": {"P@5": 0.72},
    "CLINICIAN": {"P@5": 0.64}
}
```

**Benefit**: Identify which speaker's content is harder to retrieve.

---

## Why This is Course-Ready

### 1. Clear Separation of Concerns
Each folder has one responsibility:
- `/diarization`: Speaker separation
- `/transcription`: Speech-to-text
- `/retrieval`: Query processing

**Teaching**: Each module can be a separate lecture/assignment.

---

### 2. Incremental Complexity
Students can implement in stages:
1. **Week 1**: Transcription only (no speakers)
2. **Week 2**: Add diarization (offline path)
3. **Week 3**: Add retrieval (keyword search)
4. **Week 4**: Add semantic search
5. **Week 5**: Add evaluation

**Benefit**: Buildable step-by-step.

---

### 3. Real-World Complexity (But Simplified)
- Uses production tools (Whisper, Pyannote, FastAPI)
- Simplified architecture (single machine, no distributed systems)

**Teaching**: Realistic without being overwhelming.

---

### 4. Visible Results
Students can:
- Upload audio → See diarization
- Run query → See ranked results
- Compare metrics → See improvements

**Benefit**: Immediate feedback loop.

---

## Comparison to Alternatives

### Alternative A: Separate Systems (Offline & Live)

❌ **Problems**:
- Duplicate code for indexing, retrieval, evaluation
- Hard to compare performance
- Maintenance burden

✓ **Our Approach**: Unified backend, different ingestion frontends

---

### Alternative B: Always Use Diarization

❌ **Problems**:
- LiveKit already separates speakers (wasted computation)
- Adds latency to live pipeline
- More points of failure

✓ **Our Approach**: Use diarization only when needed (offline)

---

### Alternative C: No Speaker Labels

❌ **Problems**:
- Can't filter by speaker role
- Loses conversational structure
- Reduces retrieval precision

✓ **Our Approach**: Speaker labels are mandatory schema fields

---

## System Health Indicators

### Good Signs (System is Working)

✓ Offline and live P@5 within 0.05 of each other  
✓ Patient and clinician metrics both > 0.6  
✓ No schema validation errors in production  
✓ Retrieval latency < 500ms  

---

### Warning Signs (Needs Attention)

⚠️ Large gap between offline and live metrics (>0.1)  
⚠️ One speaker mode performs much worse (<0.4)  
⚠️ Frequent indexing errors  
⚠️ Retrieval latency > 1 second  

---

## Future Extensions

### 1. Multi-Turn Reasoning
Query: "What did the patient say after the clinician asked about sleep?"
→ Requires temporal + speaker reasoning

### 2. Dialogue Act Classification
Tag segments with acts: QUESTION, ANSWER, CLARIFICATION, DIAGNOSIS

### 3. Cross-Interview Retrieval
"Find similar symptom reports across all patients"
→ Requires patient de-identification and aggregation

### 4. Active Learning
Use low-confidence retrievals to improve training data

---

## Conclusion

This hybrid architecture achieves:

✓ **Flexibility**: Supports both offline and live ingestion  
✓ **Consistency**: Same retrieval/evaluation for both modes  
✓ **Speaker Awareness**: First-class support for conversational IR  
✓ **Modularity**: Easy to teach, test, and improve  
✓ **Reproducibility**: Fixed configs, deterministic evaluation  

**Core Philosophy**: Diverge early (ingestion), converge quickly (schema), share everything else (indexing, retrieval, evaluation).
