"""
Memory management system for ASHA AI
Handles memory decay, reinforcement, and temporal reasoning
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import config
from qdrant_manager import qdrant_client
from embeddings import embedding_encoder


class MemoryManager:
    """Manages long-term memory evolution"""
    
    def __init__(self):
        self.qdrant = qdrant_client
        self.encoder = embedding_encoder
    
    def store_health_signal(
        self,
        signal_text: str,
        user_id: str,
        user_context: Dict[str, Any],
        risk_score: float
    ) -> str:
        """
        Store new health signal with automatic memory management
        
        Args:
            signal_text: Description of health signal/symptom
            user_id: Anonymous user ID
            user_context: User metadata
            risk_score: Computed risk score (0-1)
            
        Returns:
            Point ID of stored memory
        """
        # Generate embedding
        vector = self.encoder.encode_health_signal(signal_text, context=user_context)
        
        # Build payload
        payload = {
            "user_id": user_id,
            "age": user_context.get("age"),
            "pregnancy_stage": user_context.get("pregnancy_stage"),
            "risk_score": risk_score,
            "language": user_context.get("language", "hi"),
            "signal_type": user_context.get("signal_type", "symptom"),
            "timestamp": datetime.now().isoformat(),
            "reinforcement_count": 0  # Track how many times similar signal appears
        }
        
        # Add optional geographic data
        if "district" in user_context:
            payload["district"] = user_context["district"]
        
        # Store in Qdrant
        point_id = self.qdrant.store_health_memory(vector, payload)
        
        # Check for similar past signals (memory reinforcement)
        self._check_and_reinforce(vector, user_id, point_id)
        
        logger.info(f"Stored health signal: {point_id} | Risk: {risk_score:.2f}")
        return point_id
    
    def _check_and_reinforce(
        self,
        query_vector: List[float],
        user_id: str,
        current_point_id: str
    ):
        """
        Check for similar past signals and boost their importance (reinforcement)
        """
        # Search for similar memories
        similar = self.qdrant.retrieve_similar_memories(
            query_vector=query_vector,
            user_id=user_id,
            limit=5
        )
        
        # Boost risk scores for highly similar past signals
        for memory in similar:
            similarity_score = memory.get("score", 0.0)
            mem_id = memory.get("id")
            
            # Skip current point
            if str(mem_id) == str(current_point_id):
                continue
            
            # If very similar (>0.85), boost the risk score
            if similarity_score > 0.85:
                current_risk = memory.get("payload", {}).get("risk_score", 0.0)
                reinforcement_count = memory.get("payload", {}).get("reinforcement_count", 0)
                
                # Apply reinforcement boost
                boosted_risk = min(1.0, current_risk * config.MEMORY_REINFORCEMENT_BOOST)
                
                # Update memory
                self.qdrant.client.set_payload(
                    collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
                    payload={
                        "risk_score": boosted_risk,
                        "reinforcement_count": reinforcement_count + 1
                    },
                    points=[mem_id]
                )
                
                logger.info(f"Reinforced memory {mem_id}: {current_risk:.2f} → {boosted_risk:.2f}")
    
    def apply_memory_decay(self, user_id: str, days_threshold: int = 90):
        """
        Apply decay to old low-risk memories
        
        Args:
            user_id: User to process
            days_threshold: Age threshold for decay
        """
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        
        # Get old memories
        from qdrant_client.models import Filter, FieldCondition, Range
        
        results, _ = self.qdrant.client.scroll(
            collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="user_id", match={"value": user_id}),
                    FieldCondition(key="timestamp", range={"lt": cutoff_date}),
                    FieldCondition(key="risk_score", range={"lt": config.RISK_THRESHOLD_MEDIUM})
                ]
            ),
            limit=100,
            with_payload=True
        )
        
        # Apply decay
        for point in results:
            current_risk = point.payload.get("risk_score", 0.0)
            decayed_risk = current_risk * config.MEMORY_DECAY_RATE
            
            self.qdrant.client.set_payload(
                collection_name=config.COLLECTION_USER_HEALTH_MEMORY,
                payload={"risk_score": decayed_risk},
                points=[point.id]
            )
        
        logger.info(f"Applied decay to {len(results)} old memories for user {user_id[:8]}")
    
    def detect_deterioration(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Detect if user's health is deteriorating over time
        
        Args:
            user_id: User to analyze
            days: Time window to analyze
            
        Returns:
            Deterioration analysis
        """
        from retrieval_engine import retrieval_engine
        
        trajectory = retrieval_engine.get_high_risk_trajectory(user_id, days)
        
        # Determine if intervention needed
        if trajectory.get("risk_trend") == "deteriorating":
            recent_avg = trajectory.get("recent_avg_risk", 0.0)
            
            if recent_avg > config.RISK_THRESHOLD_HIGH:
                return {
                    "alert": "high_priority",
                    "message": "Silent deterioration detected - high risk",
                    "trajectory": trajectory
                }
            else:
                return {
                    "alert": "monitor",
                    "message": "Mild deterioration - continue monitoring",
                    "trajectory": trajectory
                }
        
        return {
            "alert": "none",
            "message": "Health stable or improving",
            "trajectory": trajectory
        }
    
    def create_population_insight(
        self,
        district: str,
        insight_text: str,
        insight_type: str = "trend"
    ) -> str:
        """
        Store population-level insight for ASHA dashboard
        
        Args:
            district: Geographic area
            insight_text: Description of insight
            insight_type: Type (trend, alert, pattern)
            
        Returns:
            Point ID
        """
        vector = self.encoder.encode(insight_text)
        
        payload = {
            "district": district,
            "insight_type": insight_type,
            "content": insight_text,
            "timestamp": datetime.now().isoformat()
        }
        
        point_id = self.qdrant.client.upsert(
            collection_name=config.COLLECTION_ASHA_INSIGHTS,
            points=[{
                "id": self.qdrant._generate_point_id(),
                "vector": vector,
                "payload": payload
            }]
        ).operation_id
        
        logger.info(f"Created population insight: {district} - {insight_type}")
        return str(point_id)


# Global instance
memory_manager = MemoryManager()
