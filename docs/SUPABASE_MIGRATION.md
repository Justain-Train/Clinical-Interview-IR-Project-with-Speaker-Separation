# Supabase Integration Summary

**Updated**: The project now uses **Supabase** as the unified database solution.

---

## What Changed?

### Before (Original Skeleton)
- **Vector Store**: Qdrant/Milvus (separate service)
- **Metadata Store**: PostgreSQL (separate service)
- **Architecture**: Two databases to sync

### After (Supabase)
- **Unified Database**: Supabase (PostgreSQL with pgvector)
- **Vector Search**: Built-in via pgvector extension
- **Architecture**: Single database, ACID transactions

---

## Benefits of Supabase

✅ **Simpler Architecture**: One database instead of two  
✅ **ACID Transactions**: Segments + embeddings updated atomically  
✅ **Built-in Features**: Auth, real-time subscriptions, RESTful API  
✅ **Free Tier**: 500MB DB, unlimited API requests  
✅ **Easy Deployment**: Cloud-hosted or self-hosted  
✅ **SQL Interface**: Familiar query language  
✅ **Hybrid Search**: Native full-text + vector search  

---

## Key Files Updated

1. **`.env.example`** - Supabase credentials instead of Qdrant/PostgreSQL
2. **`requirements.txt`** - Added `supabase`, `pgvector`
3. **`docker-compose.yml`** - Local dev uses `ankane/pgvector` image
4. **`docs/supabase_setup.md`** - Complete setup guide (NEW)
5. **`scripts/init_supabase_db.py`** - Database initialization (NEW)
6. **`backend/utils/supabase_client.py`** - Python client wrapper (NEW)
7. **Module READMEs** - Updated to reference Supabase

---

## Quick Start with Supabase

### 1. Cloud Setup (Production)

```bash
# Sign up at https://supabase.com
# Create project, get credentials
# Update .env with:
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key

# Initialize schema
python scripts/init_supabase_db.py
```

### 2. Local Setup (Development)

```bash
# Start local PostgreSQL with pgvector
docker-compose up -d postgres

# Use local connection
DATABASE_URL=postgresql://postgres:dev_password@localhost:5432/clinical_interviews

# Initialize schema
python scripts/init_supabase_db.py
```

---

## Database Schema

### Tables

**`segments`** (main table with vectors)
- `segment_id` (UUID, PK)
- `interview_id` (VARCHAR, FK)
- `speaker_role` (VARCHAR: PATIENT/CLINICIAN)
- `text` (TEXT - for full-text search)
- `embedding` (vector(768) - for semantic search)
- `start_time`, `end_time` (FLOAT)
- `metadata` (JSONB - extensible)

**`interviews`**
- `interview_id` (VARCHAR, PK)
- `title`, `date`, `duration_seconds`
- `ingestion_mode` (OFFLINE/LIVE)

**`evaluation_datasets`** & **`evaluation_results`**
- For storing test sets and metrics

---

## Search Functions

Supabase provides custom SQL functions for efficient search:

### Semantic Search
```sql
SELECT * FROM search_segments(
    query_embedding := '[0.1, 0.2, ...]',
    match_threshold := 0.3,
    match_count := 10,
    filter_speaker_role := 'PATIENT'
);
```

### Hybrid Search
```sql
SELECT * FROM hybrid_search_segments(
    query_embedding := '[0.1, 0.2, ...]',
    query_text := 'headache symptoms',
    semantic_weight := 0.7,
    keyword_weight := 0.3
);
```

---

## Python Usage

```python
from backend.utils.supabase_client import get_supabase_client

client = get_supabase_client()

# Insert segment
client.insert_segment({
    "interview_id": "interview_001",
    "speaker_role": "PATIENT",
    "text": "I've been experiencing headaches.",
    "embedding": embedding_vector,  # 768-dim list
    "start_time": 0.0,
    "end_time": 5.2
})

# Search
results = client.hybrid_search(
    query_embedding=query_vector,
    query_text="headache symptoms",
    filter_speaker_role="PATIENT"
)
```

---

## Migration Notes

### If You Started with Qdrant

**No code changes needed in:**
- Diarization module
- Transcription module
- Alignment module

**Update these modules:**
- `indexing/index_writer.py` - Use Supabase client instead of Qdrant
- `retrieval/retriever.py` - Call Supabase RPC functions
- `backend/utils/db_utils.py` - Use Supabase connection

**Benefits of migration:**
- Simpler deployment (one service)
- No sync issues between vector DB and metadata DB
- Better transaction support

---

## Resources

📖 **Setup Guide**: `/docs/supabase_setup.md`  
🔧 **Init Script**: `/scripts/init_supabase_db.py`  
💻 **Python Client**: `/backend/utils/supabase_client.py`  
📊 **Supabase Docs**: https://supabase.com/docs  
🔍 **pgvector Docs**: https://github.com/pgvector/pgvector  

---

## Still Works Locally

The `docker-compose.yml` now uses `ankane/pgvector` for local development:
- Same PostgreSQL, just with pgvector extension
- No Supabase cloud needed for development
- Switch to Supabase cloud for production deployment

---

**Next**: Read `/docs/supabase_setup.md` for complete setup instructions!
