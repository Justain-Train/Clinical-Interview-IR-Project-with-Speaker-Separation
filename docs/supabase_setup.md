# Supabase Setup Guide

This project uses Supabase as the unified database and vector store.

---

## Why Supabase?

**Supabase provides:**
- PostgreSQL database with pgvector extension (for vector search)
- Built-in authentication (if needed for production)
- Real-time subscriptions (for live updates)
- RESTful API and Python SDK
- Free tier with generous limits
- Easy deployment and scaling

**Single service replaces:**
- ✅ PostgreSQL (metadata storage)
- ✅ Qdrant/Milvus (vector storage)
- ✅ Both now unified in one database

---

## Step 1: Create Supabase Project

### Sign Up
1. Go to https://supabase.com
2. Sign up for free account
3. Create new project:
   - Project name: `clinical-interview-ir`
   - Database password: (save this securely)
   - Region: Choose closest to you
   - Pricing plan: Free tier

### Wait for Provisioning
- Takes ~2 minutes
- You'll get a project URL and API keys

---

## Step 2: Get Credentials

### From Project Settings → API

Copy these values:
```
Project URL: https://xxxxxxxxxxxxx.supabase.co
anon/public key: eyJhbGc...
service_role key: eyJhbGc... (keep secret!)
```

### From Project Settings → Database

Copy the connection string:
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

---

## Step 3: Configure Environment Variables

Update your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Database URL (for direct SQL access if needed)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

---

## Step 4: Enable pgvector Extension

### Via Supabase Dashboard

1. Go to **Database → Extensions**
2. Search for `vector`
3. Enable `pgvector`
4. Click "Enable"

### Via SQL Editor

Alternatively, run in SQL Editor:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Step 5: Create Database Schema

Run the initialization script:

```bash
python scripts/init_supabase_db.py
```

Or manually execute the SQL schema:

### Tables Schema

```sql
-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    interview_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    date TIMESTAMP,
    duration_seconds FLOAT,
    ingestion_mode VARCHAR CHECK (ingestion_mode IN ('OFFLINE', 'LIVE')),
    audio_path VARCHAR,
    livekit_session_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Segments table with vector embeddings
CREATE TABLE IF NOT EXISTS segments (
    segment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id VARCHAR REFERENCES interviews(interview_id) ON DELETE CASCADE,
    speaker_role VARCHAR CHECK (speaker_role IN ('PATIENT', 'CLINICIAN', 'UNKNOWN')),
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(768),  -- 768 dimensions for all-MiniLM-L6-v2
    confidence FLOAT,
    ingestion_mode VARCHAR CHECK (ingestion_mode IN ('OFFLINE', 'LIVE')),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- Evaluation datasets table
CREATE TABLE IF NOT EXISTS evaluation_datasets (
    dataset_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    test_queries JSONB NOT NULL
);

-- Evaluation results table
CREATE TABLE IF NOT EXISTS evaluation_results (
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id VARCHAR REFERENCES evaluation_datasets(dataset_id),
    timestamp TIMESTAMP DEFAULT NOW(),
    overall_metrics JSONB,
    speaker_metrics JSONB,
    per_query_results JSONB,
    config JSONB
);
```

### Indexes for Performance

```sql
-- Indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_segments_interview ON segments(interview_id);
CREATE INDEX IF NOT EXISTS idx_segments_speaker ON segments(speaker_role);
CREATE INDEX IF NOT EXISTS idx_segments_time ON segments(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_segments_mode ON segments(ingestion_mode);
CREATE INDEX IF NOT EXISTS idx_segments_created ON segments(created_at);

-- Vector similarity search index (HNSW for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_segments_embedding ON segments 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (good for smaller datasets)
-- CREATE INDEX IF NOT EXISTS idx_segments_embedding ON segments 
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- Full-text search index for keyword search
CREATE INDEX IF NOT EXISTS idx_segments_text_search ON segments 
USING gin(to_tsvector('english', text));
```

### Functions for Vector Search

```sql
-- Function: Semantic search with filters
CREATE OR REPLACE FUNCTION search_segments(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 10,
    filter_interview_id varchar DEFAULT NULL,
    filter_speaker_role varchar DEFAULT NULL
)
RETURNS TABLE (
    segment_id uuid,
    interview_id varchar,
    speaker_role varchar,
    start_time float,
    end_time float,
    text text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.segment_id,
        s.interview_id,
        s.speaker_role,
        s.start_time,
        s.end_time,
        s.text,
        1 - (s.embedding <=> query_embedding) as similarity
    FROM segments s
    WHERE 
        (filter_interview_id IS NULL OR s.interview_id = filter_interview_id)
        AND (filter_speaker_role IS NULL OR s.speaker_role = filter_speaker_role)
        AND 1 - (s.embedding <=> query_embedding) > match_threshold
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Hybrid search (semantic + keyword)
CREATE OR REPLACE FUNCTION hybrid_search_segments(
    query_embedding vector(768),
    query_text text,
    semantic_weight float DEFAULT 0.7,
    keyword_weight float DEFAULT 0.3,
    match_count int DEFAULT 10,
    filter_interview_id varchar DEFAULT NULL,
    filter_speaker_role varchar DEFAULT NULL
)
RETURNS TABLE (
    segment_id uuid,
    interview_id varchar,
    speaker_role varchar,
    start_time float,
    end_time float,
    text text,
    semantic_score float,
    keyword_score float,
    combined_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT 
            s.segment_id,
            s.interview_id,
            s.speaker_role,
            s.start_time,
            s.end_time,
            s.text,
            1 - (s.embedding <=> query_embedding) as sem_score
        FROM segments s
        WHERE 
            (filter_interview_id IS NULL OR s.interview_id = filter_interview_id)
            AND (filter_speaker_role IS NULL OR s.speaker_role = filter_speaker_role)
    ),
    keyword_results AS (
        SELECT 
            s.segment_id,
            ts_rank(to_tsvector('english', s.text), plainto_tsquery('english', query_text)) as kw_score
        FROM segments s
        WHERE 
            (filter_interview_id IS NULL OR s.interview_id = filter_interview_id)
            AND (filter_speaker_role IS NULL OR s.speaker_role = filter_speaker_role)
            AND to_tsvector('english', s.text) @@ plainto_tsquery('english', query_text)
    )
    SELECT 
        sr.segment_id,
        sr.interview_id,
        sr.speaker_role,
        sr.start_time,
        sr.end_time,
        sr.text,
        sr.sem_score,
        COALESCE(kr.kw_score, 0.0) as kw_score,
        (semantic_weight * sr.sem_score + keyword_weight * COALESCE(kr.kw_score, 0.0)) as combined
    FROM semantic_results sr
    LEFT JOIN keyword_results kr ON sr.segment_id = kr.segment_id
    ORDER BY combined DESC
    LIMIT match_count;
END;
$$;
```

---

## Step 6: Set Up Row Level Security (Optional)

For production, enable RLS to secure data:

```sql
-- Enable RLS on segments table
ALTER TABLE segments ENABLE ROW LEVEL SECURITY;

-- Policy: Public read access (for demo)
CREATE POLICY "Enable read access for all users" ON segments
    FOR SELECT USING (true);

-- Policy: Service role can do anything
CREATE POLICY "Enable all access for service role" ON segments
    FOR ALL USING (auth.role() = 'service_role');
```

**Note**: For development, you can skip RLS and use service_role key.

---

## Step 7: Test Connection

### Using Python

```python
from supabase import create_client, Client

url = "https://xxxxxxxxxxxxx.supabase.co"
key = "your-anon-key"
supabase: Client = create_client(url, key)

# Test query
result = supabase.table("segments").select("*").limit(5).execute()
print(f"Found {len(result.data)} segments")
```

### Using SQL Editor

In Supabase Dashboard → SQL Editor:

```sql
SELECT COUNT(*) FROM segments;
```

---

## Step 8: Python Integration

### Install Dependencies

```bash
pip install supabase pgvector
```

### Example Usage

```python
from supabase import create_client
import numpy as np

# Initialize client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Insert segment with embedding
embedding = np.random.rand(768).tolist()  # Your actual embedding

supabase.table("segments").insert({
    "interview_id": "interview_001",
    "speaker_role": "PATIENT",
    "start_time": 0.0,
    "end_time": 5.2,
    "text": "I've been experiencing headaches.",
    "embedding": embedding,
    "ingestion_mode": "OFFLINE"
}).execute()

# Vector search using RPC
query_embedding = np.random.rand(768).tolist()

results = supabase.rpc(
    "search_segments",
    {
        "query_embedding": query_embedding,
        "match_threshold": 0.3,
        "match_count": 5,
        "filter_speaker_role": "PATIENT"
    }
).execute()

print(f"Found {len(results.data)} similar segments")
```

---

## Supabase Free Tier Limits

| Resource | Limit |
|----------|-------|
| Database size | 500 MB |
| Storage | 1 GB |
| Bandwidth | 2 GB/month |
| API requests | Unlimited |
| Active connections | 60 |

**Note**: Plenty for development and small-scale academic projects.

---

## Local Development Alternative

For offline development, use Docker with pgvector:

```bash
docker-compose up -d postgres
```

This runs a local PostgreSQL with pgvector extension.

Then connect using:
```
DATABASE_URL=postgresql://postgres:dev_password@localhost:5432/clinical_interviews
```

---

## Migration from Qdrant

If you started with Qdrant, migration is straightforward:

1. **Schema**: Segments are now rows in PostgreSQL (not separate vector DB)
2. **Embeddings**: Store in `vector(768)` column (not separate collection)
3. **Metadata**: Use JSONB columns (native JSON support)
4. **Search**: Use SQL functions instead of Qdrant client

**Benefits**:
- Simpler architecture (one database instead of two)
- ACID transactions (segments + metadata updated together)
- Familiar SQL interface
- Built-in full-text search

---

## Troubleshooting

### Issue: pgvector extension not found
**Solution**: Enable it in Dashboard → Database → Extensions

### Issue: Connection timeout
**Solution**: Check if your IP is allowed in Database Settings → Connection Pooling

### Issue: Vector index creation slow
**Solution**: Normal for HNSW index. Use IVFFlat for faster creation on small datasets

### Issue: Row Level Security blocks queries
**Solution**: Use service_role key for backend operations

---

## Production Recommendations

1. **Use connection pooling** (Supabase provides this)
2. **Monitor database usage** in Supabase Dashboard
3. **Set up backups** (automatic in Supabase)
4. **Use prepared statements** to prevent SQL injection
5. **Upgrade to Pro plan** if exceeding free tier limits

---

## Next Steps

1. Run `python scripts/init_supabase_db.py` to create tables
2. Update `backend/utils/db_utils.py` to use Supabase client
3. Update `indexing/index_writer.py` to write to Supabase
4. Update `retrieval/retriever.py` to query Supabase
5. Test with sample data

---

## Resources

- **Supabase Docs**: https://supabase.com/docs
- **pgvector Docs**: https://github.com/pgvector/pgvector
- **Python Client**: https://supabase.com/docs/reference/python/introduction
- **Vector Search Guide**: https://supabase.com/docs/guides/ai/vector-search
