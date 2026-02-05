# Evaluation Module

This module computes IR metrics and generates evaluation reports.

---

## Purpose

Measure retrieval quality using standard IR metrics.

---

## Components

### `metrics.py`
Precision@K, Recall@K, MAP, NDCG implementations

### `evaluator.py`
Orchestrates evaluation runs

### `speaker_eval.py`
Speaker-specific metric breakdown

---

## Metrics

### Precision@K
Of the K results returned, how many were relevant?

### Recall@K
Of all relevant segments, how many were found in top K?

### MAP (Mean Average Precision)
Average precision across all queries

### NDCG@K
Normalized ranking quality (position-aware)

---

## Usage

```python
from evaluation.evaluator import run_evaluation

result = run_evaluation(
    dataset_id="test_set_v1",
    config=EvalConfig(
        top_k=[1, 3, 5, 10],
        speaker_modes=["ALL", "PATIENT", "CLINICIAN"]
    )
)

# Returns: EvaluationResult with all metrics
```

---

## Evaluation Workflow

1. Load test dataset (queries + ground truth)
2. Run retrieval for each query
3. Compare results with ground truth
4. Compute metrics per query
5. Aggregate overall metrics
6. Generate report

---

## Speaker-Specific Evaluation

```python
from evaluation.speaker_eval import evaluate_by_speaker

speaker_metrics = evaluate_by_speaker(
    queries=test_queries,
    results=retrieval_results
)

# Returns:
# {
#   "PATIENT": MetricSet(P@5=0.72, R@5=0.78, ...),
#   "CLINICIAN": MetricSet(P@5=0.64, R@5=0.69, ...)
# }
```

---

## Output

### Console Summary
```
Evaluation: test_set_v1
Queries: 50
Overall P@5: 0.68
Overall R@5: 0.74
Patient P@5: 0.72
Clinician P@5: 0.64
```

### JSON Report
Complete results saved to `/results/eval_{timestamp}.json`

### Markdown Report
Human-readable report in `/results/eval_{timestamp}.md`

---

## Notes

- Deterministic (fixed random seeds for reproducibility)
- Fast (parallel query processing)
- Extensible (easy to add custom metrics)
