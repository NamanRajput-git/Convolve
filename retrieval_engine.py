"""
Retrieval-First Reasoning Engine for ASHA AI
CRITICAL: NO RESPONSE can be generated without Qdrant retrieval
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import config
from embeddings import embedding_encoder
from qdrant_manager import qdrant_client
from logger import log_retrieval


class RetrievalEngine:
    """
    Handles all retrieval operations across Qdrant collections
    Enforces retrieval-first reasoning
    """
    
    def __init__(self):
        self.embedding_encoder = embedding_encoder
        self.qdrant = qdrant_client
    
    def retrieve_for_query(
        self,
        query_text: str,
        user_id: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main retrieval pipeline - MANDATORY before LLM response
        
        Args:
            query_text: User's health query
            user_id: Anonymous user ID
            user_context: User metadata (age, pregnancy_stage, etc.)
            
        Returns:
            Retrieved evidence from all relevant collections
        """
        logger.info(f"Starting retrieval for user {user_id[:8]}...")
        
        # Step 1: Generate query embedding
        query_vector = self.embedding_encoder.encode_health_signal(
            query_text,
            context=user_context
        )
        
        # Step 2: Retrieve from user's health memory
        user_memories = self._retrieve_user_memories(
            query_vector, user_id, user_context
        )
        
        # Step 3: Retrieve medical knowledge
        medical_knowledge = self._retrieve_medical_knowledge(
            query_vector, query_text, user_context
        )
        
        # Step 4: Retrieve nutrition patterns (if relevant)
        nutrition_data = self._retrieve_nutrition_patterns(
            query_vector, query_text
        )
        
        # Step 5: Re-rank and filter results
        reranked_memories = self._rerank_by_risk_and_recency(user_memories)
        
        # Step 6: Aggregate results
        retrieval_results = {
            "query": query_text,
            "user_memories": reranked_memories[:config.RERANK_TOP_K],
            "medical_knowledge": medical_knowledge,
            "nutrition_patterns": nutrition_data,
            "total_evidence_count": len(user_memories) + len(medical_knowledge) + len(nutrition_data),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log for explainability
        log_retrieval(
            user_id=user_id,
            query=query_text,
            results=retrieval_results["user_memories"],
            collection="user_health_memory"
        )
        
        log_retrieval(
            user_id=user_id,
            query=query_text,
            results=medical_knowledge,
            collection="verified_medical_knowledge"
        )
        
        logger.info(f"Retrieval complete: {retrieval_results['total_evidence_count']} pieces of evidence")
        
        return retrieval_results
    
    def _retrieve_user_memories(
        self,
        query_vector: List[float],
        user_id: str,
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve similar health signals from user's history"""
        
        filters = {}
        
        # Filter by pregnancy stage if applicable
        if user_context.get("pregnancy_stage"):
            filters["pregnancy_stage"] = user_context["pregnancy_stage"]
        
        # Optional: filter by minimum risk
        # filters["min_risk_score"] = 0.3
        
        return self.qdrant.retrieve_similar_memories(
            query_vector=query_vector,
            user_id=user_id,
            filters=filters,
            limit=config.RETRIEVAL_TOP_K
        )
    
    def _retrieve_medical_knowledge(
        self,
        query_vector: List[float],
        query_text: str,
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve verified medical guidance"""
        
        # Remove strict keyword-based filtering which causes empty results
        # Rely on vector similarity for relevance
        filters = None
        
        return self.qdrant.retrieve_medical_knowledge(
            query_vector=query_vector,
            filters=filters,
            limit=5
        )
    
    def _retrieve_nutrition_patterns(
        self,
        query_vector: List[float],
        query_text: str
    ) -> List[Dict[str, Any]]:
        """Retrieve nutrition patterns if query is nutrition-related"""
        
        query_lower = query_text.lower()
        nutrition_keywords = ["nutrition", "food", "diet", "iron", "खाना", "आहार", "IFA"]
        
        if not any(keyword in query_lower for keyword in nutrition_keywords):
            return []
        
        # Search nutrition patterns collection
        try:
            results = self.qdrant.client.search(
                collection_name=config.COLLECTION_NUTRITION_PATTERNS,
                query_vector=query_vector,
                limit=3,
                with_payload=True
            )
            
            return [
                {
                    "score": result.score,
                    "food_item": result.payload.get("food_item"),
                    "iron_content": result.payload.get("iron_content"),
                    "local_name": result.payload.get("local_name")
                }
                for result in results
            ]
        except Exception as e:
            logger.warning(f"Nutrition pattern retrieval failed: {e}")
            return []
    
    def _rerank_by_risk_and_recency(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank memories by:
        1. Risk severity (higher = more important)
        2. Recency (more recent = more relevant)
        3. Original similarity score
        """
        
        def compute_rerank_score(memory: Dict[str, Any]) -> float:
            # Original similarity score (0-1)
            similarity = memory.get("score", 0.0)
            
            # Risk score (0-1)
            risk_score = memory.get("payload", {}).get("risk_score", 0.0)
            
            # Recency score (decay over time)
            timestamp_str = memory.get("payload", {}).get("timestamp")
            recency_score = 0.5  # Default
            
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    days_ago = (datetime.now() - timestamp).days
                    # Exponential decay: recent=1.0, older decays
                    recency_score = max(0.1, 1.0 - (days_ago / 365.0))
                except Exception:
                    pass
            
            # Weighted combination
            rerank_score = (
                0.4 * similarity +      # Similarity is important
                0.4 * risk_score +      # Risk is critical
                0.2 * recency_score     # Recency matters less
            )
            
            return rerank_score
        
        # Sort by rerank score descending
        reranked = sorted(
            memories,
            key=compute_rerank_score,
            reverse=True
        )
        
        # Add rerank score to results
        for memory in reranked:
            memory["rerank_score"] = compute_rerank_score(memory)
        
        return reranked
    
    def check_sufficient_evidence(self, retrieval_results: Dict[str, Any]) -> bool:
        """
        Check if retrieval returned sufficient evidence to generate response
        
        Returns:
            True if sufficient, False if fallback needed
        """
        total = retrieval_results.get("total_evidence_count", 0)
        
        # Need at least 1 piece of medical knowledge OR 2 user memories
        has_medical = len(retrieval_results.get("medical_knowledge", [])) > 0
        has_memories = len(retrieval_results.get("user_memories", [])) >= 2
        
        return has_medical or has_memories
    
    def get_high_risk_trajectory(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze user's risk trajectory over time
        Used for deterioration detection
        """
        # Get all recent memories
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Retrieve all user memories (no vector search, just filter)
        results, _ = self.qdrant.client.scroll(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            scroll_filter={
                "must": [
                    {"key": "user_id", "match": {"value": user_id}},
                    {"key": "timestamp", "range": {"gte": cutoff_date}}
                ]
            },
            limit=100,
            with_payload=True
        )
        
        if not results:
            return {"status": "no_data", "risk_trend": "stable"}
        
        # Sort by timestamp
        sorted_results = sorted(
            results,
            key=lambda x: x.payload.get("timestamp", "")
        )
        
        # Calculate trend
        risk_scores = [r.payload.get("risk_score", 0.0) for r in sorted_results]
        
        if len(risk_scores) < 2:
            return {"status": "insufficient_data", "risk_trend": "stable"}
        
        # Simple trend: compare recent average vs older average
        midpoint = len(risk_scores) // 2
        older_avg = sum(risk_scores[:midpoint]) / midpoint
        recent_avg = sum(risk_scores[midpoint:]) / (len(risk_scores) - midpoint)
        
        if recent_avg > older_avg + 0.15:
            trend = "deteriorating"
        elif recent_avg < older_avg - 0.15:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "status": "analyzed",
            "risk_trend": trend,
            "older_avg_risk": round(older_avg, 2),
            "recent_avg_risk": round(recent_avg, 2),
            "signal_count": len(risk_scores)
        }


# Global instance
retrieval_engine = RetrievalEngine()
