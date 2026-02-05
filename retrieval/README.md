# Retrieval Module

This module handles query processing, retrieval, ranking, and explanation generation.

---

## Purpose

Given a user query, return the most relevant speaker-labeled segments.

---

## Components

### `retriever.py`
Core search logic (semantic + keyword + hybrid)

### `ranker.py`
Re-ranking with cross-encoder models

### `llm_explainer.py`
LLM-based answer generation

---

## Search Modes

### 1. Semantic Search
- Embed query → Find nearest neighbors using pgvector cosine similarity
- SQL: `ORDER BY embedding <=> query_embedding`
- Best for: Paraphrased queries, conceptual matching

### 2. Keyword Search
- PostgreSQL full-text search (ts_rank)
- SQL: `to_tsvector('english', text) @@ plainto_tsquery(query)`
- Best for: Exact term matching

### 3. Hybrid Search (Default)
- Combine semantic + keyword scores in SQL
- Uses custom `hybrid_search_segments()` function
- Fusion formula: `0.7 * semantic + 0.3 * keyword`

---

## Usage

```python
from retrieval.retriever import retrieve

results = retrieve(
    query=RetrievalQuery(
        query_text="What symptoms did the patient report?",
        speaker_filter="PATIENT",
        top_k=5
    ),
    mode="hybrid"
)

# Returns: List[RankedSegment]
```

---

## Speaker Filtering

Built-in support for:
- `speaker_filter="PATIENT"`: Only patient segments
- `speaker_filter="CLINICIAN"`: Only clinician segments
- `speaker_filter="ALL"`: Both (default)

---

## Re-ranking

Optional second-stage ranking:

```python
from retrieval.ranker import rerank

ranked = rerank(
    query_text="What symptoms were reported?",
    candidates=retrieval_results,
    top_k=5
)

# Uses cross-encoder for more accurate ranking
```

---

## LLM Explanation

Generate grounded answers:

```python
from retrieval.llm_explainer import explain

explanation = explain(
    query_text="What symptoms were reported?",
    segments=top_5_results
)

# Returns: "The patient reported experiencing headaches..."
```

---

## Performance

- Typical latency: 200-500ms
- Bottleneck: Vector search (most queries)
- Optimization: Use GPU for embedding generation

---

## Notes

- All searches use same index (offline + live data)
- Filters are applied at query time (not re-indexing needed)
- Supports multi-interview search (pass list of interview IDs)
