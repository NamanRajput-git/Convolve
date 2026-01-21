"""
Main processing pipeline for ASHA AI
Orchestrates the entire flow from voice input to response
"""

from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

# Import all components
from privacy import privacy_manager
from embeddings import embedding_encoder
from qdrant_manager import qdrant_client
from retrieval_engine import retrieval_engine
from llm_handler import llm_handler
from memory_manager import memory_manager
from risk_scorer import risk_scorer
from voice_input import voice_input
from voice_output import voice_output
from logger import log_health_signal


class AshaAIPipeline:
    """Main orchestration pipeline"""
    
    def __init__(self):
        self.privacy = privacy_manager
        self.encoder = embedding_encoder
        self.qdrant = qdrant_client
        self.retrieval = retrieval_engine
        self.llm = llm_handler
        self.memory = memory_manager
        self.risk = risk_scorer
        logger.info("ASHA AI Pipeline initialized")
    
    def process_voice_query(
        self,
        audio_file_path: str,
        user_context: Dict[str, Any],
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Complete pipeline: voice → response
        
        Args:
            audio_file_path: Path to audio file
            user_context: User metadata (age, pregnancy_stage, etc.)
            language: Language code
            
        Returns:
            Complete response with answer, audio, risk analysis
        """
        try:
            # Step 1: Voice → Text
            logger.info("=== STEP 1: Voice Input ===")
            transcribed_text, success = voice_input.process_audio_file(
                audio_file_path, language
            )
            
            if not success or not transcribed_text:
                return {
                    "success": False,
                    "error": "Could not understand speech. Please try again."
                }
            
            # Cleanup audio immediately (privacy)
            voice_input.cleanup_audio_file(audio_file_path)
            
            # Step 2: Process text query
            return self.process_text_query(transcribed_text, user_context, language)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "success": False,
                "error": f"System error: {str(e)}"
            }
    
    def process_text_query(
        self,
        query_text: str,
        user_context: Dict[str, Any],
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Process text query through full pipeline
        
        Args:
            query_text: User's health query
            user_context: User metadata
            language: Language code
            
        Returns:
            Complete response
        """
        try:
            # Get or create anonymous user ID
            user_id = self.privacy.generate_anonymous_id(
                phone_number=user_context.get("phone")
            )
            user_context["user_id"] = user_id
            user_context["language"] = language
            
            logger.info(f"=== Processing query for user {user_id[:8]}... ===")
            
            # Step 2: Sanitize text (remove PII)
            logger.info("=== STEP 2: Privacy Sanitization ===")
            sanitized_text = self.privacy.sanitize_text(query_text)
            
            # Step 3: MANDATORY QDRANT RETRIEVAL
            logger.info("=== STEP 3: Qdrant Retrieval (MANDATORY) ===")
            retrieval_results = self.retrieval.retrieve_for_query(
                sanitized_text, user_id, user_context
            )
            
            if not retrieval_results:
                raise RuntimeError("CRITICAL: Retrieval failed - cannot proceed without Qdrant")
            
            # Step 4: Calculate risk score
            logger.info("=== STEP 4: Risk Assessment ===")
            risk_score = self.risk.calculate_risk_score(
                sanitized_text, user_context, retrieval_results
            )
            
            # Step 5: LLM Response (grounded in retrieval)
            logger.info("=== STEP 5: LLM Response Generation ===")
            llm_response = self.llm.generate_response(
                sanitized_text, retrieval_results, user_context
            )
            
            # Step 6: Store in memory (write back to Qdrant)
            logger.info("=== STEP 6: Memory Update ===")
            memory_id = self.memory.store_health_signal(
                signal_text=sanitized_text,
                user_id=user_id,
                user_context=user_context,
                risk_score=risk_score
            )
            
            log_health_signal(user_id, user_context.get("signal_type", "symptom"), risk_score)
            
            # Step 7: Generate voice output
            logger.info("=== STEP 7: Voice Output ===")
            response_text = llm_response["answer"]
            audio_path = voice_output.generate_speech(response_text, language)
            
            # Step 8: Check for deterioration
            deterioration = self.memory.detect_deterioration(user_id)
            
            # Return complete response
            result = {
                "success": True,
                "query": sanitized_text,
                "answer": response_text,
                "audio_path": audio_path,
                "risk_score": risk_score,
                "risk_category": self.risk.get_risk_category(risk_score),
                "risk_display": self.risk.get_risk_color(risk_score),
                "should_escalate": llm_response["should_escalate"],
                "evidence_count": retrieval_results["total_evidence_count"],
                "memory_id": memory_id,
                "deterioration_alert": deterioration.get("alert"),
                "deterioration_message": deterioration.get("message"),
                "timestamp": datetime.now().isoformat(),
                "debug_error": llm_response.get("debug_error")  # Forward debug error
            }
            
            logger.info(f"=== Pipeline Complete | Risk: {risk_score:.2f} | Evidence: {result['evidence_count']} ===")
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"System error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def health_check(self) -> Dict[str, bool]:
        """Check if all components are working"""
        return {
            "qdrant": self.qdrant.health_check(),
            "embeddings": True,  # Loaded at init
            "llm": GOOGLE_API_KEY is not None,
            "privacy": True
        }


# Global instance
pipeline = AshaAIPipeline()


# For imports
from config import GOOGLE_API_KEY
