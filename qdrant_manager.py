"""
Qdrant client and collection management for ASHA AI
CRITICAL: This is the CORE MEMORY BRAIN - removing this breaks the entire system
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, Range
)
from typing import List, Dict, Any, Optional
from loguru import logger
import config


class AshaQdrantClient:
    """Manages all Qdrant operations for ASHA AI"""
    
    def __init__(self):
        """Initialize Qdrant connection"""
        try:
            # Use HTTP explicitly for local Docker instance
            self.client = QdrantClient(
                url=f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}",
                timeout=30
            )
            logger.info(f"Connected to Qdrant at http://{config.QDRANT_HOST}:{config.QDRANT_PORT}")
            self._initialize_collections()
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise RuntimeError(
                "❌ QDRANT CONNECTION FAILED - System cannot function without vector database. "
                f"Please ensure Qdrant is running at {config.QDRANT_HOST}:{config.QDRANT_PORT}"
            )
    
    def _initialize_collections(self):
        """Create all required collections if they don't exist"""
        collections = [
            (config.COLLECTION_USER_HEALTH_MEMORY, "User health signals and symptoms"),
            (config.COLLECTION_MEDICAL_KNOWLEDGE, "Verified medical protocols and guidance"),
            (config.COLLECTION_NUTRITION_PATTERNS, "Nutrition patterns and IFA tracking"),
            (config.COLLECTION_ASHA_INSIGHTS, "Population-level health insights")
        ]
        
        for collection_name, description in collections:
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=config.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection_name} - {description}")
            else:
                logger.info(f"Collection exists: {collection_name}")
    
    def store_health_memory(self, vector: List[float], payload: Dict[str, Any]) -> str:
        """
        Store user health signal in memory
        
        Args:
            vector: Embedding of the health signal
            payload: Metadata (must be privacy-safe)
            
        Returns:
            Point ID
        """
        from privacy import privacy_manager
        
        # Validate no PII
        if not privacy_manager.validate_no_pii(payload):
            raise ValueError("PII detected in payload - cannot store")
        
        point_id = self._generate_point_id()
        
        self.client.upsert(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )]
        )
        
        logger.info(f"Stored health memory: {point_id} | Signal: {payload.get('signal_type')}")
        return str(point_id)
    
    def retrieve_similar_memories(
        self, 
        query_vector: List[float],
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar health memories for a user
        
        Args:
            query_vector: Query embedding
            user_id: Anonymous user ID
            filters: Additional filters (age, pregnancy_stage, etc.)
            limit: Number of results
            
        Returns:
            List of similar memories with scores
        """
        if limit is None:
            limit = config.RETRIEVAL_TOP_K
        
        # Build filter
        must_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        
        if filters:
            if "pregnancy_stage" in filters:
                must_conditions.append(
                    FieldCondition(
                        key="pregnancy_stage",
                        match=MatchValue(value=filters["pregnancy_stage"])
                    )
                )
            
            if "min_risk_score" in filters:
                must_conditions.append(
                    FieldCondition(
                        key="risk_score",
                        range=Range(gte=filters["min_risk_score"])
                    )
                )
        
        search_filter = Filter(must=must_conditions) if must_conditions else None
        
        results = self.client.query_points(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        ).points
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]
    
    def retrieve_medical_knowledge(
        self,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant medical knowledge"""
        
        search_filter = None
        if filters:
            must_conditions = []
            if "topic" in filters:
                must_conditions.append(
                    FieldCondition(key="topic", match=MatchValue(value=filters["topic"]))
                )
            if must_conditions:
                search_filter = Filter(must=must_conditions)
        
        results = self.client.query_points(
            collection_name=config.COLLECTION_MEDICAL_KNOWLEDGE,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        ).points
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "content": result.payload.get("content"),
                "source": result.payload.get("source"),
                "confidence": result.payload.get("confidence")
            }
            for result in results
        ]
    
    def update_memory_score(self, point_id: str, new_risk_score: float):
        """Update risk score for existing memory (reinforcement/decay)"""
        self.client.set_payload(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            payload={"risk_score": new_risk_score},
            points=[point_id]
        )
        logger.info(f"Updated memory {point_id} risk score: {new_risk_score}")
    
    def delete_user_data(self, user_id: str):
        """Delete all data for a user (privacy compliance)"""
        self.client.delete(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            points_selector=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            )
        )
        logger.info(f"Deleted all data for user: {user_id}")
    
    def get_high_risk_users(self, threshold: float = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve high-risk users for ASHA dashboard
        
        Args:
            threshold: Risk threshold (default from config)
            limit: Number of users to return
            
        Returns:
            List of high-risk user summaries
        """
        if threshold is None:
            threshold = config.RISK_THRESHOLD_HIGH
        
        # Scroll through high-risk records
        results, _ = self.client.scroll(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            scroll_filter=Filter(
                must=[FieldCondition(key="risk_score", range=Range(gte=threshold))]
            ),
            limit=limit,
            with_payload=True
        )
        
        # Group by user_id and get latest
        user_map = {}
        for point in results:
            user_id = point.payload.get("user_id")
            if user_id not in user_map:
                user_map[user_id] = point.payload
            else:
                # Keep most recent
                existing_time = user_map[user_id].get("timestamp", "")
                new_time = point.payload.get("timestamp", "")
                if new_time > existing_time:
                    user_map[user_id] = point.payload
        
        return list(user_map.values())
    
    def _generate_point_id(self) -> int:
        """Generate unique point ID"""
        from datetime import datetime
        return int(datetime.now().timestamp() * 1000000)
    
    def health_check(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global instance
qdrant_client = AshaQdrantClient()
