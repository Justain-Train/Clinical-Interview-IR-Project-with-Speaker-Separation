# Data Schema Definitions

All schemas defined conceptually. Implement using Pydantic models in Python.

---

## Core Schemas

### 1. TranscriptSegment

**Purpose**: Atomic unit of speaker-labeled text. Output of both ingestion pipelines.

```
TranscriptSegment:
  segment_id: UUID                    # Unique identifier
  interview_id: String                # Links to interview session
  speaker_role: Enum                  # PATIENT | CLINICIAN | UNKNOWN
  start_time: Float                   # Seconds from interview start
  end_time: Float                     # Seconds from interview start
  text: String                        # Transcribed utterance
  confidence: Float                   # Transcription confidence (optional)
  ingestion_mode: Enum                # OFFLINE | LIVE
  created_at: Timestamp               # When segment was created
  metadata: Dict                      # Extensible (e.g., audio_path, model_version)
```

**Validation Rules**:
- `end_time > start_time`
- `text` is non-empty
- `speaker_role` must be valid enum value

**Example**:
```json
{
  "segment_id": "550e8400-e29b-41d4-a716-446655440000",
  "interview_id": "interview_2024_001",
  "speaker_role": "PATIENT",
  "start_time": 45.2,
  "end_time": 52.8,
  "text": "I've been experiencing headaches for the past two weeks.",
  "confidence": 0.95,
  "ingestion_mode": "OFFLINE",
  "created_at": "2024-03-15T10:30:00Z",
  "metadata": {
    "audio_file": "interview_001.wav",
    "whisper_model": "large-v2"
  }
}
```

---

### 2. DiarizationResult

**Purpose**: Intermediate output from Pyannote (offline only). NOT stored in final index.

```
DiarizationResult:
  interview_id: String
  segments: List[DiarizationSegment]
  
DiarizationSegment:
  start_time: Float
  end_time: Float
  speaker_label: String              # e.g., "SPEAKER_00", "SPEAKER_01"
  confidence: Float                  # Optional
```

**Note**: This gets merged with transcription to create TranscriptSegment.

---

### 3. RetrievalQuery

**Purpose**: Input to retrieval system.

```
RetrievalQuery:
  query_id: UUID                     # For tracking
  query_text: String                 # User's question
  interview_ids: List[String]        # Optional: search specific interviews
  speaker_filter: Enum               # ALL | PATIENT | CLINICIAN
  top_k: Integer                     # Number of results (default: 10)
  rerank: Boolean                    # Apply re-ranking (default: true)
  explain: Boolean                   # Generate LLM explanation (default: false)
  metadata: Dict                     # Optional filters
```

**Example**:
```json
{
  "query_id": "660e8400-e29b-41d4-a716-446655440001",
  "query_text": "What symptoms did the patient report about headaches?",
  "interview_ids": ["interview_2024_001", "interview_2024_002"],
  "speaker_filter": "PATIENT",
  "top_k": 5,
  "rerank": true,
  "explain": true
}
```

---

### 4. RetrievalResult

**Purpose**: Output from retrieval system.

```
RetrievalResult:
  query_id: UUID
  query_text: String
  results: List[RankedSegment]
  explanation: String                # Optional LLM-generated answer
  retrieval_time_ms: Integer
  
RankedSegment:
  segment: TranscriptSegment         # Full segment data
  score: Float                       # Relevance score
  rank: Integer                      # Position in results (1-indexed)
  retrieval_method: String           # e.g., "semantic", "keyword", "hybrid"
```

**Example**:
```json
{
  "query_id": "660e8400-e29b-41d4-a716-446655440001",
  "query_text": "What symptoms did the patient report?",
  "results": [
    {
      "segment": { /* TranscriptSegment object */ },
      "score": 0.92,
      "rank": 1,
      "retrieval_method": "hybrid"
    }
  ],
  "explanation": "The patient reported experiencing headaches for two weeks...",
  "retrieval_time_ms": 245
}
```

---

### 5. EvaluationDataset

**Purpose**: Ground truth for evaluation.

```
EvaluationDataset:
  dataset_id: String
  interview_ids: List[String]
  test_queries: List[TestQuery]
  
TestQuery:
  query_id: UUID
  query_text: String
  relevant_segment_ids: List[UUID]   # Ground truth relevant segments
  speaker_filter: Enum               # Expected filter (for testing)
  metadata: Dict                     # Optional (e.g., difficulty, category)
```

**Example**:
```json
{
  "dataset_id": "eval_set_v1",
  "interview_ids": ["interview_2024_001"],
  "test_queries": [
    {
      "query_id": "test_001",
      "query_text": "What headache symptoms were reported?",
      "relevant_segment_ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440005"
      ],
      "speaker_filter": "PATIENT",
      "metadata": {"category": "symptoms"}
    }
  ]
}
```

---

### 6. EvaluationResult

**Purpose**: Metrics computed by evaluation pipeline.

```
EvaluationResult:
  evaluation_id: UUID
  dataset_id: String
  timestamp: Timestamp
  overall_metrics: MetricSet
  speaker_specific_metrics: Dict[SpeakerRole, MetricSet]
  per_query_results: List[QueryMetrics]
  
MetricSet:
  precision_at_1: Float
  precision_at_3: Float
  precision_at_5: Float
  precision_at_10: Float
  recall_at_1: Float
  recall_at_3: Float
  recall_at_5: Float
  recall_at_10: Float
  mean_average_precision: Float
  ndcg_at_10: Float
  
QueryMetrics:
  query_id: UUID
  query_text: String
  precision_at_k: Dict[Integer, Float]
  recall_at_k: Dict[Integer, Float]
  retrieved_relevant: Integer
  total_relevant: Integer
```

**Example**:
```json
{
  "evaluation_id": "eval_run_001",
  "dataset_id": "eval_set_v1",
  "timestamp": "2024-03-15T14:00:00Z",
  "overall_metrics": {
    "precision_at_5": 0.85,
    "recall_at_5": 0.72,
    "mean_average_precision": 0.78
  },
  "speaker_specific_metrics": {
    "PATIENT": {
      "precision_at_5": 0.88,
      "recall_at_5": 0.75
    },
    "CLINICIAN": {
      "precision_at_5": 0.82,
      "recall_at_5": 0.68
    }
  }
}
```

---

## Database/Storage Schema

### Vector Database (Qdrant/Milvus)

**Collection**: `clinical_segments`

**Fields**:
- `segment_id` (primary key)
- `embedding` (768-dim vector for Sentence-BERT)
- `interview_id` (indexed)
- `speaker_role` (indexed)
- `start_time` (indexed)
- `end_time`
- `text` (stored, not indexed in vector DB)
- `ingestion_mode`
- `created_at`

**Filters Supported**:
- `interview_id == "interview_2024_001"`
- `speaker_role == "PATIENT"`
- `start_time >= 30.0 AND end_time <= 120.0`

---

### Metadata Store (SQLite/PostgreSQL)

**Table**: `interviews`

```sql
CREATE TABLE interviews (
  interview_id VARCHAR PRIMARY KEY,
  title VARCHAR,
  date TIMESTAMP,
  duration_seconds FLOAT,
  ingestion_mode VARCHAR,  -- OFFLINE | LIVE
  audio_path VARCHAR,       -- For offline only
  livekit_session_id VARCHAR,  -- For live only
  created_at TIMESTAMP
);
```

**Table**: `segments`

```sql
CREATE TABLE segments (
  segment_id UUID PRIMARY KEY,
  interview_id VARCHAR REFERENCES interviews(interview_id),
  speaker_role VARCHAR,
  start_time FLOAT,
  end_time FLOAT,
  text TEXT,
  confidence FLOAT,
  ingestion_mode VARCHAR,
  created_at TIMESTAMP,
  metadata JSONB
);
```

---

## Schema Consistency Rules

### Between Offline and Live Paths

Both MUST produce TranscriptSegment with:
1. Valid `speaker_role` (PATIENT/CLINICIAN/UNKNOWN)
2. Non-overlapping time ranges within same interview
3. Monotonically increasing timestamps
4. Non-empty text

### Validation at Indexing

Before writing to index:
1. Check schema completeness
2. Validate time ranges
3. Check for duplicates (same interview + time range)
4. Verify speaker_role is in allowed set

---

## Extension Points

### Future Schema Additions

**Sentiment Analysis**:
```
TranscriptSegment.metadata.sentiment = {
  "polarity": Float,  # -1 to 1
  "confidence": Float
}
```

**Entity Extraction**:
```
TranscriptSegment.metadata.entities = [
  {"type": "SYMPTOM", "text": "headache", "confidence": 0.9},
  {"type": "DURATION", "text": "two weeks", "confidence": 0.85}
]
```

**Topic Modeling**:
```
TranscriptSegment.metadata.topics = [
  {"topic_id": "pain_management", "probability": 0.75}
]
```

These are OPTIONAL and do not break core retrieval logic.
