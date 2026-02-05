# Evaluation Protocol

Standardized procedures for evaluating retrieval performance.

---

## Purpose

This document defines:
- How to create test datasets
- How to run evaluations
- How to interpret results
- How to ensure reproducibility

---

## Test Dataset Structure

### Dataset Components

1. **Interview Audio/Transcripts**: Pre-indexed clinical interviews
2. **Test Queries**: Questions about the interviews
3. **Ground Truth**: Manually labeled relevant segments for each query
4. **Metadata**: Query difficulty, category, expected speaker filter

### Dataset Format

See `data_schemas.md` for `EvaluationDataset` schema.

---

## Creating a Test Dataset

### Step 1: Select Interviews

Choose diverse interviews:
- Different lengths (5 min, 15 min, 30 min)
- Different topics (pain, mental health, chronic conditions)
- Both offline and live ingestion modes
- Clear speaker separation

**Recommended**: Start with 10 interviews, ~50 queries

---

### Step 2: Generate Queries

#### Query Categories

| Category | Description | Example |
|----------|-------------|---------|
| Symptom | Patient-reported symptoms | "What pain symptoms were reported?" |
| History | Medical history questions | "What prior treatments were mentioned?" |
| Diagnosis | Clinician's assessments | "What diagnosis did the clinician suggest?" |
| Treatment | Treatment recommendations | "What medications were prescribed?" |
| Social | Social/lifestyle factors | "What lifestyle changes were discussed?" |

#### Query Distribution

- 40% Symptom queries
- 20% History queries
- 20% Diagnosis queries
- 10% Treatment queries
- 10% Social queries

#### Speaker Filters

- 50% PATIENT-only queries
- 30% CLINICIAN-only queries
- 20% ALL (both speakers)

---

### Step 3: Label Ground Truth

For each query, manually identify **all relevant segments**.

**Relevance Criteria**:
- **Highly Relevant (HR)**: Directly answers the query
- **Partially Relevant (PR)**: Contains related information
- **Not Relevant (NR)**: Off-topic

**For Evaluation**: Use only HR segments as ground truth.

**Example**:

Query: "What headache symptoms did the patient report?"

Ground Truth Segments:
```json
{
  "query_id": "q001",
  "relevant_segment_ids": [
    "uuid-001",  // "I've been experiencing severe headaches"
    "uuid-015",  // "The headaches started two weeks ago"
    "uuid-032"   // "They occur mostly in the morning"
  ]
}
```

---

### Step 4: Validate Dataset

**Quality Checks**:
- Each query has at least 1 relevant segment
- No query has >20 relevant segments (too broad)
- Queries are clear and unambiguous
- Ground truth labels are consistent (inter-annotator agreement if multiple labelers)

**Inter-Annotator Agreement**:
If using multiple annotators:
- Calculate Cohen's Kappa or Fleiss' Kappa
- Target: κ > 0.7 (substantial agreement)

---

## Running Evaluations

### Standard Evaluation Run

```bash
python scripts/run_evaluation.py \
  --dataset test_set_v1 \
  --config config/eval_config.yaml \
  --output results/eval_2024_03_15.json
```

### Configuration (`eval_config.yaml`)

```yaml
retrieval:
  search_mode: hybrid
  rerank: true
  top_k: [1, 3, 5, 10]

metrics:
  - precision@k
  - recall@k
  - mean_average_precision
  - ndcg@k

speaker_modes:
  - ALL
  - PATIENT
  - CLINICIAN

output:
  format: json
  save_per_query_results: true
  generate_report: true
```

---

## Metrics Interpretation

### Precision@K

**Definition**: Of the K results returned, how many were relevant?

**Good Values**:
- P@1 > 0.8 (first result usually relevant)
- P@5 > 0.6 (more than half of top 5 are relevant)
- P@10 > 0.4

**When Low**: System returns too many irrelevant results

---

### Recall@K

**Definition**: Of all relevant segments, how many were found in top K?

**Good Values**:
- R@5 > 0.5 (at least half of relevant segments in top 5)
- R@10 > 0.7

**When Low**: System misses relevant segments

---

### Mean Average Precision (MAP)

**Definition**: Average precision across all relevant results

**Good Values**:
- MAP > 0.6 is acceptable
- MAP > 0.75 is good
- MAP > 0.85 is excellent

**When Low**: Relevant results are ranked poorly

---

### NDCG@K

**Definition**: Normalized ranking quality (accounts for position)

**Good Values**:
- NDCG@10 > 0.7

**When Low**: Relevant results appear late in rankings

---

## Speaker-Specific Analysis

### Why It Matters

Clinical IR has asymmetric information:
- **Patient utterances**: Rich in symptoms, history, concerns
- **Clinician utterances**: Rich in questions, diagnoses, recommendations

Performance may differ by speaker.

### Expected Patterns

- **Patient queries**: Often have MORE relevant segments (patients talk more)
- **Clinician queries**: Often more precise (fewer but more specific segments)

### Red Flags

- Patient P@5 < 0.5: Poor at finding symptom information
- Clinician P@5 < 0.5: Poor at finding clinical assessments
- Large gap (>0.15) between speakers: System is biased

---

## Comparing Ingestion Modes

### Offline vs. Live

Run evaluation separately on:
1. Interviews ingested via offline pipeline
2. Interviews ingested via live pipeline

**Expected**: Similar performance (validates convergent architecture)

**If Different**:
- Check alignment quality (offline)
- Check transcription confidence (live streaming may have lower quality)

---

## Reproducibility Checklist

To ensure reproducible results:

### ✓ Fixed Random Seeds
```python
import random
import numpy as np
random.seed(42)
np.random.seed(42)
```

### ✓ Model Versions
Document:
- Whisper model: `whisper-base-v20230314`
- Sentence-BERT: `all-MiniLM-L6-v2`
- Pyannote: `pyannote/speaker-diarization@3.1`

### ✓ Configuration Files
Store all configs in version control:
- `eval_config.yaml`
- `retrieval_config.yaml`
- `diarization_config.yaml`

### ✓ Dataset Version
Tag datasets:
- `test_set_v1` (initial)
- `test_set_v2` (after fixes)

### ✓ Environment
Document:
- Python version
- CUDA version (if using GPU)
- OS

---

## Evaluation Schedule

### During Development
- Run after each major change
- Use small test set (10 queries) for speed

### Before Release
- Full evaluation on complete test set
- Document results in `/results` folder

### Production Monitoring
- Monthly evaluation on live data
- Track metrics over time

---

## Result Storage

### File Structure

```
/results/
  ├── eval_2024_03_01/
  │   ├── config.yaml
  │   ├── results.json
  │   ├── report.md
  │   └── per_query_details.csv
  ├── eval_2024_03_15/
  │   ├── config.yaml
  │   ├── results.json
  │   ├── report.md
  │   └── per_query_details.csv
```

### Results JSON Schema

```json
{
  "evaluation_id": "eval_2024_03_15",
  "dataset_id": "test_set_v1",
  "config": { /* eval config */ },
  "timestamp": "2024-03-15T16:00:00Z",
  "overall_metrics": { /* MetricSet */ },
  "speaker_metrics": { /* Dict[Speaker, MetricSet] */ },
  "per_query_results": [ /* List[QueryMetrics] */ ]
}
```

---

## Baseline Comparisons

### Baseline 1: BM25 Only
- No semantic search
- Keyword matching only
- Expected: Lower recall, higher precision on exact matches

### Baseline 2: Random
- Return random segments
- Expected: P@K ≈ (num_relevant / total_segments)

### Baseline 3: No Re-ranking
- Disable cross-encoder re-ranking
- Measures re-ranking contribution

**Goal**: Main system should outperform all baselines.

---

## Error Analysis

### Low-Performing Queries

For queries with P@5 < 0.3:
1. Manually inspect retrieved segments
2. Check if ground truth is complete (missed annotations?)
3. Check if query is ambiguous
4. Analyze failure mode:
   - **Vocabulary mismatch**: "cephalalgia" vs "headache"
   - **Negation**: "no pain" vs "pain"
   - **Temporal**: "current symptoms" vs "past symptoms"

### Fix Strategies

- **Vocabulary**: Add synonym expansion
- **Negation**: Improve text preprocessing
- **Temporal**: Add time-aware filters

---

## Reporting Template

```markdown
# Evaluation Report: [Date]

## Configuration
- Dataset: test_set_v1 (50 queries, 10 interviews)
- Retrieval Mode: Hybrid (semantic + keyword)
- Re-ranking: Enabled

## Overall Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| P@5 | 0.68 | >0.65 | ✓ Pass |
| R@5 | 0.74 | >0.70 | ✓ Pass |
| MAP | 0.71 | >0.65 | ✓ Pass |

## Speaker-Specific Results

| Speaker | P@5 | R@5 | Queries |
|---------|-----|-----|---------|
| PATIENT | 0.72 | 0.78 | 25 |
| CLINICIAN | 0.64 | 0.69 | 20 |
| ALL | 0.68 | 0.75 | 5 |

## Insights
- Patient queries perform 8% better (more data available)
- All targets met ✓
- 3 queries have P@5 < 0.3 (see error analysis)

## Recommendations
- Investigate low-performing queries
- Consider adding medical synonym expansion
```

---

## Next Steps After Evaluation

1. **If targets met**: Document results, move to production
2. **If targets not met**:
   - Analyze errors
   - Improve retrieval/ranking
   - Re-run evaluation
3. **Iterate**: Evaluation → Analysis → Improvement → Evaluation
