# Unified Retrieval Workflow

**Purpose**: Handle queries against indexed clinical interviews, supporting speaker-aware retrieval and LLM-based explanations.

---

## Trigger

**Type**: Webhook or API Call  
**Input**:
```json
{
  "query_id": "query_001",
  "query_text": "What symptoms did the patient report about headaches?",
  "interview_ids": ["interview_2024_001", "interview_2024_002"],
  "speaker_filter": "PATIENT",
  "top_k": 5,
  "rerank": true,
  "explain": true
}
```

---

## Workflow Steps

### Step 1: Validate Query
- **Action**: Check query parameters
- **API**: `POST /api/retrieval/validate`
- **Validations**:
  - `query_text` is non-empty
  - `top_k` is between 1 and 100
  - `speaker_filter` is valid enum
  - `interview_ids` exist in database (if provided)
- **Output**: `{"valid": true}` or error details
- **Error Handling**: Return 400 Bad Request with details

---

### Step 2: Embed Query
- **Action**: Convert query text to semantic vector
- **API**: `POST /api/retrieval/embed`
- **Input**:
  ```json
  {
    "query_text": "What symptoms did the patient report about headaches?"
  }
  ```
- **Output**:
  ```json
  {
    "embedding": [0.123, -0.456, 0.789, ...],  // 768-dim vector
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  }
  ```

---

### Step 3: Retrieve Candidate Segments
- **Action**: Search vector database with filters
- **API**: `POST /api/retrieval/search`
- **Input**:
  ```json
  {
    "query_embedding": [0.123, -0.456, ...],
    "query_text": "What symptoms did the patient report?",
    "filters": {
      "interview_ids": ["interview_2024_001"],
      "speaker_role": "PATIENT"
    },
    "top_k": 20,  // Retrieve more for re-ranking
    "search_mode": "hybrid"  // Combines semantic + keyword
  }
  ```
- **Output**:
  ```json
  {
    "candidates": [
      {
        "segment": { /* Full TranscriptSegment */ },
        "score": 0.85,
        "method": "semantic"
      },
      {
        "segment": { /* Full TranscriptSegment */ },
        "score": 0.78,
        "method": "hybrid"
      }
    ],
    "total_found": 20
  }
  ```

---

### Step 4: Re-rank Results (Optional)
- **Action**: Apply cross-encoder or custom ranking
- **API**: `POST /api/retrieval/rerank`
- **Input**:
  ```json
  {
    "query_text": "What symptoms did the patient report?",
    "candidates": [ /* From Step 3 */ ],
    "top_k": 5
  }
  ```
- **Output**:
  ```json
  {
    "ranked_results": [
      {
        "segment": { /* TranscriptSegment */ },
        "score": 0.92,
        "rank": 1
      },
      {
        "segment": { /* TranscriptSegment */ },
        "score": 0.88,
        "rank": 2
      }
    ]
  }
  ```
- **Skip Condition**: If `rerank: false`, skip this step

---

### Step 5: Generate LLM Explanation (Optional)
- **Action**: Use LLM to synthesize answer from retrieved segments
- **API**: `POST /api/retrieval/explain`
- **Input**:
  ```json
  {
    "query_text": "What symptoms did the patient report?",
    "retrieved_segments": [ /* Top K segments */ ]
  }
  ```
- **Prompt Template**:
  ```
  You are a clinical information assistant. Answer the question based ONLY on the provided interview segments.
  
  Question: {query_text}
  
  Interview Segments:
  1. [PATIENT, 45.2s-52.8s]: "I've been experiencing headaches for the past two weeks."
  2. [PATIENT, 68.5s-75.2s]: "The headaches usually occur in the morning."
  
  Answer:
  ```
- **Output**:
  ```json
  {
    "explanation": "The patient reported experiencing headaches for the past two weeks, primarily occurring in the morning.",
    "grounded_segments": [1, 2],  // Which segments were used
    "model": "llama-3.1-8b"
  }
  ```
- **Skip Condition**: If `explain: false`, skip this step

---

### Step 6: Format and Return Results
- **Action**: Combine retrieval + ranking + explanation into final response
- **API**: Internal formatting (not an endpoint)
- **Output**:
  ```json
  {
    "query_id": "query_001",
    "query_text": "What symptoms did the patient report?",
    "results": [
      {
        "segment": {
          "segment_id": "uuid-1",
          "interview_id": "interview_2024_001",
          "speaker_role": "PATIENT",
          "start_time": 45.2,
          "end_time": 52.8,
          "text": "I've been experiencing headaches for the past two weeks."
        },
        "score": 0.92,
        "rank": 1
      }
    ],
    "explanation": "The patient reported experiencing headaches...",
    "retrieval_time_ms": 245,
    "total_results": 5
  }
  ```

---

### Step 7: Log Query
- **Action**: Store query and results for analytics
- **API**: `POST /api/retrieval/log`
- **Input**:
  ```json
  {
    "query_id": "query_001",
    "query_text": "What symptoms did the patient report?",
    "filters": {"speaker_role": "PATIENT"},
    "results_count": 5,
    "retrieval_time_ms": 245,
    "timestamp": "2024-03-15T15:30:00Z"
  }
  ```

---

## Search Modes

### Semantic Search
- Uses query embedding + cosine similarity
- Best for: Paraphrased or conceptual queries
- Example: "pain complaints" matches "I'm experiencing discomfort"

### Keyword Search
- Uses BM25 or similar keyword matching
- Best for: Exact term queries
- Example: "headache" matches "headache" but not "cephalgia"

### Hybrid Search
- Combines semantic + keyword with score fusion
- Best for: General use (default)
- Formula: `final_score = 0.7 * semantic_score + 0.3 * keyword_score`

---

## Speaker Filtering Logic

### No Filter (Default)
```python
# Retrieve from all speakers
filters = {}
```

### Patient-Only
```python
filters = {"speaker_role": "PATIENT"}
```

### Clinician-Only
```python
filters = {"speaker_role": "CLINICIAN"}
```

### Multi-Interview Search
```python
filters = {
    "interview_ids": ["interview_001", "interview_002"],
    "speaker_role": "PATIENT"
}
```

---

## Error Scenarios

### Scenario 1: No Results Found
- **Cause**: Query too specific or poor embedding match
- **Response**:
  ```json
  {
    "results": [],
    "message": "No segments matched your query.",
    "suggestions": ["Try broader terms", "Remove speaker filter"]
  }
  ```

### Scenario 2: LLM Explanation Fails
- **Cause**: LLM timeout or API error
- **Fallback**: Return retrieved segments without explanation
- **Response**: Include `"explanation": null, "explanation_error": "LLM timeout"`

### Scenario 3: Invalid Speaker Filter
- **Cause**: User provides `speaker_role: "DOCTOR"` (not in schema)
- **Response**: 400 Bad Request with valid options

---

## Workflow Diagram

```
Query Input
    ↓
Validate Query
    ↓
Embed Query (Semantic Vector)
    ↓
Retrieve Candidates (Vector DB + Filters)
    ↓
Re-rank Results (Optional)
    ↓
Generate LLM Explanation (Optional)
    ↓
Format Final Response
    ↓
Log Query
    ↓
Return to User
```

---

## Performance Optimization

### Caching
- Cache query embeddings (deduplication)
- Cache frequent queries (e.g., "common symptoms")

### Batch Queries
- If multiple queries in one request, embed in batch
- Reduces latency by ~50%

### Async Re-ranking
- If re-ranking is slow, run async and return preliminary results first

---

## Testing Checklist

- [ ] Query with patient filter → Only patient segments returned
- [ ] Query with no filter → Both speakers returned
- [ ] Query non-existent interview_id → Returns empty results
- [ ] Test semantic search: "pain" matches "discomfort"
- [ ] Test keyword search: Exact term matching works
- [ ] Verify LLM explanation references correct segments
- [ ] Test with top_k=1 vs top_k=10 → Correct number returned
- [ ] Measure latency: Should be < 500ms for simple queries
