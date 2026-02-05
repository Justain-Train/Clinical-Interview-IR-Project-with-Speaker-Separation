# Evaluation Workflow

**Purpose**: Compute IR metrics (Precision@K, Recall@K, etc.) on test datasets to validate retrieval quality.

---

## Trigger

**Type**: Manual or Scheduled (e.g., weekly)  
**Input**:
```json
{
  "evaluation_id": "eval_run_001",
  "dataset_id": "test_set_v1",
  "retrieval_config": {
    "top_k": [1, 3, 5, 10],
    "rerank": true,
    "search_mode": "hybrid"
  },
  "speaker_modes": ["ALL", "PATIENT", "CLINICIAN"]
}
```

---

## Workflow Steps

### Step 1: Load Evaluation Dataset
- **Action**: Retrieve test queries and ground truth
- **API**: `GET /api/evaluation/dataset/{dataset_id}`
- **Output**:
  ```json
  {
    "dataset_id": "test_set_v1",
    "interview_ids": ["interview_001", "interview_002"],
    "test_queries": [
      {
        "query_id": "test_q1",
        "query_text": "What headache symptoms were reported?",
        "relevant_segment_ids": ["uuid-1", "uuid-5", "uuid-12"],
        "speaker_filter": "PATIENT"
      },
      {
        "query_id": "test_q2",
        "query_text": "What questions did the clinician ask about sleep?",
        "relevant_segment_ids": ["uuid-20", "uuid-21"],
        "speaker_filter": "CLINICIAN"
      }
    ],
    "total_queries": 50
  }
  ```

---

### Step 2: Run Retrieval for Each Query
- **Action**: Execute retrieval workflow for each test query
- **API**: `POST /api/retrieval/batch`
- **Input**:
  ```json
  {
    "queries": [
      {
        "query_id": "test_q1",
        "query_text": "What headache symptoms were reported?",
        "speaker_filter": "PATIENT",
        "top_k": 10
      }
    ],
    "config": {
      "rerank": true,
      "search_mode": "hybrid"
    }
  }
  ```
- **Output**: Array of RetrievalResult objects
- **Note**: Process in batches of 10 to avoid timeout

---

### Step 3: Compute Metrics Per Query
- **Action**: Calculate Precision@K and Recall@K for each query
- **API**: `POST /api/evaluation/compute_metrics`
- **Input**:
  ```json
  {
    "query_id": "test_q1",
    "retrieved_segment_ids": ["uuid-1", "uuid-3", "uuid-5", "uuid-8", "uuid-12"],
    "relevant_segment_ids": ["uuid-1", "uuid-5", "uuid-12"],
    "k_values": [1, 3, 5, 10]
  }
  ```
- **Output**:
  ```json
  {
    "query_id": "test_q1",
    "metrics": {
      "precision_at_1": 1.0,      // uuid-1 is relevant
      "precision_at_3": 0.67,     // 2 out of 3 are relevant
      "precision_at_5": 0.60,     // 3 out of 5 are relevant
      "precision_at_10": 0.30,    // Would compute if we had 10 results
      "recall_at_1": 0.33,        // 1 out of 3 relevant found
      "recall_at_3": 0.67,        // 2 out of 3 relevant found
      "recall_at_5": 1.0,         // All 3 relevant found
      "recall_at_10": 1.0
    },
    "retrieved_relevant": 3,
    "total_relevant": 3
  }
  ```

---

### Step 4: Aggregate Overall Metrics
- **Action**: Compute mean metrics across all queries
- **API**: `POST /api/evaluation/aggregate`
- **Input**: Array of per-query metrics from Step 3
- **Output**:
  ```json
  {
    "overall_metrics": {
      "precision_at_1": 0.82,    // Mean across all queries
      "precision_at_3": 0.75,
      "precision_at_5": 0.68,
      "precision_at_10": 0.55,
      "recall_at_1": 0.35,
      "recall_at_3": 0.62,
      "recall_at_5": 0.78,
      "recall_at_10": 0.89,
      "mean_average_precision": 0.72,
      "ndcg_at_10": 0.81
    },
    "total_queries": 50
  }
  ```

---

### Step 5: Compute Speaker-Specific Metrics
- **Action**: Break down metrics by speaker filter
- **API**: `POST /api/evaluation/speaker_breakdown`
- **Input**: Per-query metrics + speaker filter labels
- **Output**:
  ```json
  {
    "speaker_specific_metrics": {
      "PATIENT": {
        "precision_at_5": 0.72,
        "recall_at_5": 0.81,
        "num_queries": 25
      },
      "CLINICIAN": {
        "precision_at_5": 0.64,
        "recall_at_5": 0.75,
        "num_queries": 20
      },
      "ALL": {
        "precision_at_5": 0.68,
        "recall_at_5": 0.78,
        "num_queries": 5
      }
    }
  }
  ```

---

### Step 6: Generate Evaluation Report
- **Action**: Create human-readable report
- **API**: `POST /api/evaluation/report`
- **Input**: All metrics from Steps 4 and 5
- **Output**:
  ```markdown
  # Evaluation Report: eval_run_001
  
  **Dataset**: test_set_v1  
  **Date**: 2024-03-15  
  **Total Queries**: 50
  
  ## Overall Metrics
  
  | Metric | Value |
  |--------|-------|
  | Precision@5 | 0.68 |
  | Recall@5 | 0.78 |
  | MAP | 0.72 |
  | NDCG@10 | 0.81 |
  
  ## Speaker-Specific Performance
  
  | Speaker | P@5 | R@5 | Queries |
  |---------|-----|-----|---------|
  | PATIENT | 0.72 | 0.81 | 25 |
  | CLINICIAN | 0.64 | 0.75 | 20 |
  | ALL | 0.68 | 0.78 | 5 |
  
  ## Insights
  
  - Patient-focused queries perform better (+8% P@5)
  - Clinician queries have lower recall (possibly fewer segments)
  - Overall system meets target of P@5 > 0.65 ✓
  ```

---

### Step 7: Store Evaluation Results
- **Action**: Save results to database for tracking over time
- **API**: `POST /api/evaluation/save`
- **Input**: Full EvaluationResult object
- **Output**:
  ```json
  {
    "evaluation_id": "eval_run_001",
    "status": "saved",
    "timestamp": "2024-03-15T16:00:00Z"
  }
  ```

---

## Metric Definitions

### Precision@K
```
Number of relevant segments in top K results / K
```
Measures: "What fraction of retrieved results are actually relevant?"

### Recall@K
```
Number of relevant segments in top K results / Total relevant segments
```
Measures: "What fraction of all relevant segments were retrieved?"

### Mean Average Precision (MAP)
```
Average of Precision@K for each relevant result position
```
Measures: Overall ranking quality

### NDCG@K (Normalized Discounted Cumulative Gain)
```
DCG@K / Ideal DCG@K
```
Measures: Ranking quality with position weighting

---

## Evaluation Modes

### Mode 1: Overall Evaluation
- Run all queries without filters
- Measures general retrieval quality

### Mode 2: Patient-Only Evaluation
- Run only queries with `speaker_filter: "PATIENT"`
- Measures performance on patient-focused questions

### Mode 3: Clinician-Only Evaluation
- Run only queries with `speaker_filter: "CLINICIAN"`
- Measures performance on clinician-focused questions

### Mode 4: Cross-Mode Evaluation
- Compare offline vs. live ingested data
- Filter by `ingestion_mode` in retrieval

---

## Error Scenarios

### Scenario 1: Missing Ground Truth
- **Cause**: Query has no `relevant_segment_ids`
- **Action**: Skip query, log warning
- **Impact**: Exclude from metric computation

### Scenario 2: Retrieval Returns Zero Results
- **Cause**: Query too restrictive or no matching data
- **Action**: Record as 0 precision, 0 recall
- **Impact**: Lowers overall metrics (expected behavior)

### Scenario 3: Timeout on Large Dataset
- **Cause**: 500+ queries takes too long
- **Action**: Process in smaller batches, save intermediate results
- **Fallback**: Run overnight as background job

---

## Workflow Diagram

```
Load Test Dataset
    ↓
For Each Test Query:
    ↓
    Run Retrieval
    ↓
    Compare with Ground Truth
    ↓
    Compute Per-Query Metrics
    ↓
Aggregate Overall Metrics
    ↓
Compute Speaker-Specific Metrics
    ↓
Generate Report
    ↓
Save Results
```

---

## Comparison Over Time

Track evaluation runs to monitor improvement:

```python
evaluation_runs = [
  {"date": "2024-03-01", "P@5": 0.62, "R@5": 0.70},
  {"date": "2024-03-08", "P@5": 0.65, "R@5": 0.74},
  {"date": "2024-03-15", "P@5": 0.68, "R@5": 0.78}  # Latest
]
```

**Goal**: P@5 and R@5 should trend upward as system improves.

---

## Testing Checklist

- [ ] Run evaluation on small dataset (5 queries) → Completes successfully
- [ ] Verify Precision@5 calculation manually for one query
- [ ] Test with all-relevant query → Recall@K = 1.0
- [ ] Test with no-relevant query → Precision@K = 0.0
- [ ] Compare patient vs. clinician metrics → Different values
- [ ] Re-run same dataset → Deterministic results (no randomness)
- [ ] Check report generation → Markdown renders correctly
