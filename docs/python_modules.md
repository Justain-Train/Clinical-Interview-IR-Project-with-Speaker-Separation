# Python Module Skeletons

This document lists all Python modules with their purpose. **No implementations provided** - only names and responsibilities.

---

## Diarization Module (`/diarization`)

### `pyannote_runner.py`
**Purpose**: Wrapper for Pyannote.audio speaker diarization  
**Responsibilities**:
- Load audio file
- Run Pyannote pipeline
- Return speaker segments with timestamps
- Handle multi-speaker scenarios

**Key Function Signatures**:
```python
def run_diarization(audio_path: str, num_speakers: Optional[int] = None) -> DiarizationResult
def load_model(model_name: str = "pyannote/speaker-diarization") -> Pipeline
def optimize_for_clinical_audio(pipeline: Pipeline) -> Pipeline
```

---

### `config.py`
**Purpose**: Configuration for diarization parameters  
**Responsibilities**:
- Model selection (community vs. research)
- Minimum segment duration
- Speaker separation thresholds

---

## Transcription Module (`/transcription`)

### `whisper_client.py`
**Purpose**: Interface to Whisper (local or API)  
**Responsibilities**:
- Abstract local vs. cloud Whisper
- Handle authentication if using API
- Manage model loading/caching

**Key Function Signatures**:
```python
def initialize_whisper(model_size: str = "base") -> WhisperModel
def transcribe_audio(audio_path: str, language: str = "en") -> TranscriptionResult
def get_available_models() -> List[str]
```

---

### `batch_transcribe.py`
**Purpose**: Offline batch transcription  
**Responsibilities**:
- Process entire audio file
- Return timestamped segments
- Handle long audio files (chunking if needed)

**Key Function Signatures**:
```python
def transcribe_file(audio_path: str, model: WhisperModel) -> List[TranscriptSegment]
def chunk_audio(audio_path: str, chunk_size_seconds: int = 300) -> List[AudioChunk]
```

---

### `stream_transcribe.py`
**Purpose**: Real-time streaming transcription  
**Responsibilities**:
- Connect to LiveKit audio stream
- Transcribe chunks as they arrive
- Emit segment events to message queue

**Key Function Signatures**:
```python
async def subscribe_to_stream(stream_id: str, speaker_role: SpeakerRole) -> None
async def process_audio_chunk(chunk: bytes) -> Optional[TranscriptSegment]
def emit_segment_event(segment: TranscriptSegment) -> None
```

---

## Alignment Module (`/alignment`)

### `speaker_aligner.py`
**Purpose**: Merge diarization timestamps with transcription text  
**Responsibilities**:
- Match speaker segments to transcript segments
- Handle overlapping timestamps
- Resolve ambiguities (use overlap threshold)

**Key Function Signatures**:
```python
def align_speakers_to_transcript(
    diarization: DiarizationResult,
    transcription: TranscriptionResult
) -> List[AlignedSegment]

def compute_overlap(seg1: TimeRange, seg2: TimeRange) -> float
def resolve_conflicts(segments: List[AlignedSegment]) -> List[AlignedSegment]
```

---

### `segment_builder.py`
**Purpose**: Create final TranscriptSegment objects  
**Responsibilities**:
- Combine aligned data into schema-compliant segments
- Assign speaker roles (PATIENT/CLINICIAN)
- Generate segment IDs

**Key Function Signatures**:
```python
def build_segments(
    aligned: List[AlignedSegment],
    speaker_mapping: Dict[str, SpeakerRole]
) -> List[TranscriptSegment]

def assign_speaker_role(speaker_label: str, mapping: Dict) -> SpeakerRole
def generate_segment_id() -> UUID
```

---

## Indexing Module (`/indexing`)

### `index_writer.py`
**Purpose**: Write segments to vector database and metadata store  
**Responsibilities**:
- Insert into Qdrant/Milvus vector collection
- Insert into SQL metadata table
- Handle duplicates (upsert logic)
- Batch writing for efficiency

**Key Function Signatures**:
```python
def write_segments(segments: List[TranscriptSegment]) -> WriteResult
def batch_write(segments: List[TranscriptSegment], batch_size: int = 100) -> WriteResult
def check_duplicates(segment_ids: List[UUID]) -> List[UUID]
```

---

### `embedder.py`
**Purpose**: Generate semantic embeddings for text  
**Responsibilities**:
- Load sentence-transformer model
- Embed segment text into vectors
- Cache embeddings for efficiency

**Key Function Signatures**:
```python
def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer
def embed_text(text: str, model: SentenceTransformer) -> np.ndarray
def batch_embed(texts: List[str], model: SentenceTransformer) -> np.ndarray
```

---

### `schema_validator.py`
**Purpose**: Ensure data consistency before indexing  
**Responsibilities**:
- Validate TranscriptSegment schema
- Check required fields
- Verify time ranges are logical
- Validate speaker roles

**Key Function Signatures**:
```python
def validate_segment(segment: TranscriptSegment) -> ValidationResult
def validate_batch(segments: List[TranscriptSegment]) -> List[ValidationResult]
def raise_on_invalid(segment: TranscriptSegment) -> None
```

---

## Retrieval Module (`/retrieval`)

### `retriever.py`
**Purpose**: Core retrieval logic (semantic + keyword)  
**Responsibilities**:
- Query vector database
- Apply speaker/interview filters
- Support multiple search modes (semantic, keyword, hybrid)
- Return ranked candidates

**Key Function Signatures**:
```python
def retrieve(
    query: RetrievalQuery,
    mode: SearchMode = "hybrid"
) -> List[RankedSegment]

def semantic_search(query_embedding: np.ndarray, top_k: int, filters: Dict) -> List[Candidate]
def keyword_search(query_text: str, top_k: int, filters: Dict) -> List[Candidate]
def hybrid_search(query: RetrievalQuery) -> List[Candidate]
```

---

### `ranker.py`
**Purpose**: Re-ranking retrieved candidates  
**Responsibilities**:
- Apply cross-encoder models
- Custom ranking heuristics (e.g., temporal coherence)
- Score fusion for hybrid modes

**Key Function Signatures**:
```python
def rerank(query_text: str, candidates: List[Candidate], top_k: int) -> List[RankedSegment]
def load_cross_encoder(model_name: str) -> CrossEncoder
def fuse_scores(semantic_scores: List[float], keyword_scores: List[float]) -> List[float]
```

---

### `llm_explainer.py`
**Purpose**: Generate LLM-based explanations grounded in retrieved segments  
**Responsibilities**:
- Build prompt with segments
- Call LLM (local or API)
- Extract grounded answer
- Handle errors (timeouts, nonsensical outputs)

**Key Function Signatures**:
```python
def explain(query_text: str, segments: List[TranscriptSegment]) -> ExplanationResult
def build_prompt(query: str, segments: List[TranscriptSegment]) -> str
def call_llm(prompt: str, model: str = "llama-3.1-8b") -> str
def validate_explanation(explanation: str, segments: List[TranscriptSegment]) -> bool
```

---

## Evaluation Module (`/evaluation`)

### `metrics.py`
**Purpose**: Compute IR metrics  
**Responsibilities**:
- Precision@K
- Recall@K
- Mean Average Precision (MAP)
- NDCG@K

**Key Function Signatures**:
```python
def precision_at_k(retrieved: List[UUID], relevant: List[UUID], k: int) -> float
def recall_at_k(retrieved: List[UUID], relevant: List[UUID], k: int) -> float
def mean_average_precision(retrieved: List[UUID], relevant: List[UUID]) -> float
def ndcg_at_k(retrieved: List[UUID], relevant: List[UUID], k: int) -> float
```

---

### `evaluator.py`
**Purpose**: Orchestrate evaluation pipeline  
**Responsibilities**:
- Load test datasets
- Run retrieval for each query
- Compute metrics per query
- Aggregate overall results

**Key Function Signatures**:
```python
def run_evaluation(dataset_id: str, config: EvalConfig) -> EvaluationResult
def load_dataset(dataset_id: str) -> EvaluationDataset
def evaluate_query(query: TestQuery, retrieval_config: Dict) -> QueryMetrics
def aggregate_metrics(per_query: List[QueryMetrics]) -> MetricSet
```

---

### `speaker_eval.py`
**Purpose**: Speaker-specific evaluation  
**Responsibilities**:
- Filter queries by speaker role
- Compute separate metrics for PATIENT vs. CLINICIAN
- Generate comparative reports

**Key Function Signatures**:
```python
def evaluate_by_speaker(
    queries: List[TestQuery],
    results: List[RetrievalResult]
) -> Dict[SpeakerRole, MetricSet]

def filter_queries_by_speaker(queries: List[TestQuery], speaker: SpeakerRole) -> List[TestQuery]
def compare_speaker_performance(metrics: Dict[SpeakerRole, MetricSet]) -> ComparisonReport
```

---

## Backend API Module (`/backend/api`)

### `main.py`
**Purpose**: FastAPI application entry point  
**Responsibilities**:
- Define API routes
- Handle CORS
- Error handling middleware

**Routes**:
```python
@app.post("/api/diarization/run")
@app.post("/api/transcription/batch")
@app.post("/api/transcription/stream/subscribe")
@app.post("/api/alignment/align")
@app.post("/api/indexing/write")
@app.post("/api/retrieval/query")
@app.post("/api/evaluation/run")
```

---

### `models.py`
**Purpose**: Pydantic models for API request/response  
**Responsibilities**:
- Define all schemas from `data_schemas.md`
- Request validation
- Response serialization

---

### `dependencies.py`
**Purpose**: Dependency injection for FastAPI  
**Responsibilities**:
- Database connections
- Model loading (lazy initialization)
- Configuration loading

---

## Utilities Module (`/backend/utils`)

### `audio_utils.py`
**Purpose**: Audio file handling utilities  
**Responsibilities**:
- Load audio files
- Convert formats (MP3 → WAV)
- Validate audio duration/quality

---

### `logging_config.py`
**Purpose**: Centralized logging configuration  
**Responsibilities**:
- Configure log levels
- Set up file/console handlers
- Structured logging (JSON format)

---

### `db_utils.py`
**Purpose**: Database connection helpers  
**Responsibilities**:
- Connect to vector DB
- Connect to SQL metadata store
- Connection pooling

---

## Summary

**Total Modules**: ~25  
**Lines of Code (estimated when implemented)**: ~5,000-7,000  
**Dependencies**: Pyannote, Whisper, Sentence-Transformers, FastAPI, Qdrant/Milvus, SQLAlchemy  

All modules follow:
- Type hints for all functions
- Docstrings for public APIs
- Error handling with custom exceptions
- Unit tests in `/tests` directory
