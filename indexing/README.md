# Indexing Module

This module writes speaker-labeled segments to the unified index.

---

## Purpose

Store `TranscriptSegment` objects in **Supabase** (PostgreSQL with pgvector):
- Embeddings stored as `vector(768)` column for semantic search
- Metadata stored in same row for fast filtering
- Single database (no separate vector store needed)

---

## Components

### `index_writer.py`
Writes segments to both stores

### `embedder.py`
Generates semantic embeddings for segment text

### `schema_validator.py`
Validates segments before writing

---

## Indexing Pipeline

```
TranscriptSegment
    ↓
Schema Validation
    ↓
Generate Embedding
    ↓
Write to Vector DB (Qdrant)
    ↓
Write to Metadata Store (PostgreSQL)
    ↓
Success
```

---

## Usage

```python
from indexing.index_writer import write_segments

result = write_segments(segments=[
    TranscriptSegment(...),
    TranscriptSegment(...),
])

# Returns: WriteResult(indexed_segments=2, errors=[])
```

---

## Supabase Schema

**Table**: `segments`

**Columns**:
- `segment_id` (UUID, primary key)
- `embedding` (vector(768) - for semantic search)
- `interview_id` (VARCHAR, indexed, foreign key)
- `speaker_role` (VARCHAR, indexed)
- `text` (TEXT - for keyword search)
- `start_time`, `end_time` (FLOAT, indexed)
- `ingestion_mode`, `confidence`, `created_at`
- `metadata` (JSONB - extensible)

---

## Error Handling

- **Duplicate segments**: Upsert (update if exists using ON CONFLICT)
- **Invalid schema**: PostgreSQL constraint violations with details
- **Connection failure**: Retry 3 times, then fail

---

## Notes

- Batch writing (100 segments at a time) for efficiency
- Single database transaction (ACID guarantees)
- Vector + metadata + text stored together (no data inconsistency)
- Indexing is idempotent (can re-run safely)
