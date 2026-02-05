"""
Initialize Supabase database schema for Clinical Interview IR System.

This script creates:
- Tables (interviews, segments, evaluation_datasets, evaluation_results)
- Indexes (for performance)
- Vector search functions (for semantic + hybrid search)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def enable_pgvector():
    """Enable pgvector extension."""
    sql = "CREATE EXTENSION IF NOT EXISTS vector;"
    print("Enabling pgvector extension...")
    # Note: Extensions are typically enabled via dashboard
    # This may require admin privileges
    print("✓ Enable pgvector in Supabase Dashboard → Database → Extensions")


def create_tables():
    """Create all required tables."""
    
    # Interviews table
    interviews_sql = """
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
    """
    
    # Segments table with vector embeddings
    segments_sql = """
    CREATE TABLE IF NOT EXISTS segments (
        segment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        interview_id VARCHAR REFERENCES interviews(interview_id) ON DELETE CASCADE,
        speaker_role VARCHAR CHECK (speaker_role IN ('PATIENT', 'CLINICIAN', 'UNKNOWN')),
        start_time FLOAT NOT NULL,
        end_time FLOAT NOT NULL,
        text TEXT NOT NULL,
        embedding vector(768),
        confidence FLOAT,
        ingestion_mode VARCHAR CHECK (ingestion_mode IN ('OFFLINE', 'LIVE')),
        created_at TIMESTAMP DEFAULT NOW(),
        metadata JSONB,
        CONSTRAINT valid_time_range CHECK (end_time > start_time)
    );
    """
    
    # Evaluation datasets
    eval_datasets_sql = """
    CREATE TABLE IF NOT EXISTS evaluation_datasets (
        dataset_id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        test_queries JSONB NOT NULL
    );
    """
    
    # Evaluation results
    eval_results_sql = """
    CREATE TABLE IF NOT EXISTS evaluation_results (
        evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        dataset_id VARCHAR REFERENCES evaluation_datasets(dataset_id),
        timestamp TIMESTAMP DEFAULT NOW(),
        overall_metrics JSONB,
        speaker_metrics JSONB,
        per_query_results JSONB,
        config JSONB
    );
    """
    
    print("Creating tables...")
    for sql in [interviews_sql, segments_sql, eval_datasets_sql, eval_results_sql]:
        try:
            # Execute via Supabase RPC or direct SQL
            # Note: Table creation typically done via SQL Editor or migrations
            print(f"✓ Execute SQL in Supabase SQL Editor")
            print(sql)
        except Exception as e:
            print(f"✗ Error: {e}")


def create_indexes():
    """Create performance indexes."""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_segments_interview ON segments(interview_id);",
        "CREATE INDEX IF NOT EXISTS idx_segments_speaker ON segments(speaker_role);",
        "CREATE INDEX IF NOT EXISTS idx_segments_time ON segments(start_time, end_time);",
        "CREATE INDEX IF NOT EXISTS idx_segments_mode ON segments(ingestion_mode);",
        "CREATE INDEX IF NOT EXISTS idx_segments_created ON segments(created_at);",
        """
        CREATE INDEX IF NOT EXISTS idx_segments_embedding ON segments 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_segments_text_search ON segments 
        USING gin(to_tsvector('english', text));
        """
    ]
    
    print("\nCreating indexes...")
    for idx_sql in indexes:
        print(f"Execute: {idx_sql[:50]}...")


def create_search_functions():
    """Create vector search functions."""
    
    semantic_search = """
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
    """
    
    hybrid_search = """
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
    """
    
    print("\nCreating search functions...")
    print("Execute these in Supabase SQL Editor:")
    print(semantic_search)
    print(hybrid_search)


def main():
    """Main initialization flow."""
    print("=" * 60)
    print("Supabase Database Initialization")
    print("=" * 60)
    
    print("\n📋 Instructions:")
    print("1. Go to Supabase Dashboard → SQL Editor")
    print("2. Copy and execute the SQL statements printed below")
    print("3. Verify tables and functions are created")
    print("\n" + "=" * 60 + "\n")
    
    enable_pgvector()
    create_tables()
    create_indexes()
    create_search_functions()
    
    print("\n" + "=" * 60)
    print("✓ Initialization SQL generated!")
    print("Execute the SQL statements in Supabase SQL Editor")
    print("=" * 60)


if __name__ == "__main__":
    main()
