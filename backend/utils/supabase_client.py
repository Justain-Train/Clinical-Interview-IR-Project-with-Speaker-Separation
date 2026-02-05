"""
Supabase client utility for Clinical Interview IR System.

Provides connection to Supabase with helper methods for:
- Vector search
- Hybrid search
- Segment insertion/updates
"""

import os
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Wrapper for Supabase operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
            )
        
        self.client: Client = create_client(url, key)
    
    def insert_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single segment into the database.
        
        Args:
            segment: Dictionary with segment data including embedding
            
        Returns:
            Inserted segment data
        """
        result = self.client.table("segments").insert(segment).execute()
        return result.data[0] if result.data else None
    
    def batch_insert_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert multiple segments in a batch.
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            List of inserted segment data
        """
        result = self.client.table("segments").insert(segments).execute()
        return result.data
    
    def upsert_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert or update segment (based on segment_id).
        
        Args:
            segment: Segment data
            
        Returns:
            Upserted segment data
        """
        result = self.client.table("segments").upsert(segment).execute()
        return result.data[0] if result.data else None
    
    def semantic_search(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.3,
        match_count: int = 10,
        filter_interview_id: Optional[str] = None,
        filter_speaker_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search.
        
        Args:
            query_embedding: Query vector (768-dim)
            match_threshold: Minimum similarity score
            match_count: Number of results
            filter_interview_id: Optional interview filter
            filter_speaker_role: Optional speaker filter (PATIENT/CLINICIAN)
            
        Returns:
            List of matching segments with similarity scores
        """
        result = self.client.rpc(
            "search_segments",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "filter_interview_id": filter_interview_id,
                "filter_speaker_role": filter_speaker_role
            }
        ).execute()
        
        return result.data
    
    def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        match_count: int = 10,
        filter_interview_id: Optional[str] = None,
        filter_speaker_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (semantic + keyword).
        
        Args:
            query_embedding: Query vector
            query_text: Query text for keyword matching
            semantic_weight: Weight for semantic score
            keyword_weight: Weight for keyword score
            match_count: Number of results
            filter_interview_id: Optional interview filter
            filter_speaker_role: Optional speaker filter
            
        Returns:
            List of matching segments with combined scores
        """
        result = self.client.rpc(
            "hybrid_search_segments",
            {
                "query_embedding": query_embedding,
                "query_text": query_text,
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
                "match_count": match_count,
                "filter_interview_id": filter_interview_id,
                "filter_speaker_role": filter_speaker_role
            }
        ).execute()
        
        return result.data
    
    def get_segments_by_interview(
        self,
        interview_id: str,
        speaker_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all segments for an interview.
        
        Args:
            interview_id: Interview identifier
            speaker_role: Optional speaker filter
            
        Returns:
            List of segments
        """
        query = self.client.table("segments").select("*").eq("interview_id", interview_id)
        
        if speaker_role:
            query = query.eq("speaker_role", speaker_role)
        
        result = query.order("start_time").execute()
        return result.data
    
    def delete_interview(self, interview_id: str) -> bool:
        """
        Delete an interview and all its segments (CASCADE).
        
        Args:
            interview_id: Interview to delete
            
        Returns:
            True if successful
        """
        result = self.client.table("interviews").delete().eq("interview_id", interview_id).execute()
        return len(result.data) > 0
    
    def get_interview_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts and stats
        """
        interviews = self.client.table("interviews").select("interview_id", count="exact").execute()
        segments = self.client.table("segments").select("segment_id", count="exact").execute()
        
        return {
            "total_interviews": interviews.count,
            "total_segments": segments.count
        }


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    """Get singleton Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
