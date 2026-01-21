"""
LLM Handler for ASHA AI
CRITICAL: All responses MUST be grounded in Qdrant retrieval results
"""

from typing import Dict, Any, Optional
from loguru import logger
import google.generativeai as genai
from config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE


# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)


class LLMHandler:
    """Handles LLM interactions with strict retrieval grounding"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(LLM_MODEL)
        logger.info(f"Initialized LLM: {LLM_MODEL}")
    
    def generate_response(
        self,
        user_query: str,
        retrieval_results: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate response grounded in retrieval results
        
        Args:
            user_query: User's original question
            retrieval_results: Evidence from Qdrant
            user_context: User metadata
            
        Returns:
            Response with answer, evidence, and safety flags
        """
        
        # CRITICAL CHECK: Must have retrieval results
        if retrieval_results["total_evidence_count"] == 0:
            return self._generate_fallback_response(
                user_query, 
                user_context,
                error_details="No evidence found in retrieval (Total Evidence: 0)"
            )
        
        # Build evidence-grounded prompt
        prompt = self._build_grounded_prompt(user_query, retrieval_results, user_context)
        
        try:
            # Generate response with safety settings
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=LLM_TEMPERATURE,
                    max_output_tokens=1000,  # Increased for complete bilingual responses
                ),
                safety_settings={
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",  # Medical content may trigger
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                }
            )
            
            answer = response.text
            
            # Post-process: ensure no diagnosis language
            answer = self._apply_safety_filters(answer)
            
            logger.info(f"Generated response: {len(answer)} chars")
            
            return {
                "answer": answer,
                "evidence_used": retrieval_results["total_evidence_count"],
                "should_escalate": self._check_escalation_needed(retrieval_results),
                "confidence": "grounded"
            }
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback_response(
                user_query, 
                user_context,
                error_details=f"LLM Error: {str(e)}"
            )
    
    def _build_grounded_prompt(
        self,
        user_query: str,
        retrieval_results: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> str:
        """Build prompt with retrieved evidence"""
        
        # Extract evidence
        medical_knowledge = retrieval_results.get("medical_knowledge", [])
        user_memories = retrieval_results.get("user_memories", [])
        nutrition_info = retrieval_results.get("nutrition_patterns", [])
        
        # User context
        age = user_context.get("age", "unknown")
        pregnancy_stage = user_context.get("pregnancy_stage", "not specified")
        language = user_context.get("language", "hi")
        
        # Build evidence context
        evidence_text = "### Medical Knowledge:\n"
        for i, item in enumerate(medical_knowledge[:3], 1):
            content = item.get("content", "")
            source = item.get("source", "WHO")
            evidence_text += f"{i}. {content} (Source: {source})\n"
        
        if user_memories:
            evidence_text += "\n### User's Health History:\n"
            for i, memory in enumerate(user_memories[:3], 1):
                signal_type = memory.get("payload", {}).get("signal_type", "symptom")
                risk = memory.get("payload", {}).get("risk_score", 0.0)
                evidence_text += f"{i}. Previous {signal_type} with risk score {risk:.2f}\n"
        
        if nutrition_info:
            evidence_text += "\n### Nutrition Information:\n"
            for i, item in enumerate(nutrition_info[:2], 1):
                food = item.get("food_item", "")
                local = item.get("local_name", "")
                evidence_text += f"{i}. {food} ({local})\n"
        
        # System prompt
        system_instructions = f"""You are ASHA AI, a helpful and caring healthcare assistant for rural Indian women.
        
        User Context:
        - Age: {age}
        - Pregnancy Stage: {pregnancy_stage}
        - Language: {language}
        
        EVIDENCE PROVIDED:
        {evidence_text}
        
        GUIDELINES:
        1. Use the Evidence provided to answer the user's question.
        2. If the exact answer is not in the evidence, use your general medical knowledge to provide *safe, basic guidance* (e.g., "Drink water," "Rest," "See a doctor").
        3. ALWAYS recommend visiting a ASHA worker or doctor for symptoms like fever, pain, or bleeding.
        4. Be warm, supportive, and speak simply (like a sister/didi).
        5. Keep response under 100 words.
        6. Address the user's specific symptom directly (e.g., "For fever...").
        
        User's Question: {user_query}
        
        Answer (in {language} if possible, or mixed Hindi-English):"""
        
        return system_instructions
    
    def _generate_fallback_response(
        self,
        user_query: str,
        user_context: Dict[str, Any],
        error_details: str = None
    ) -> Dict[str, Any]:
        """
        Generate safe fallback when retrieval is insufficient
        """
        
        pregnancy_stage = user_context.get("pregnancy_stage")
        
        fallback_messages = {
            "default": "मैं इस बारे में पक्की जानकारी नहीं दे सकती। कृपया अपने ASHA कार्यकर्ता या नज़दीकी स्वास्थ्य केंद्र से संपर्क करें। (I cannot provide confirmed information about this. Please contact your ASHA worker or nearest health center.)",
            
            "pregnancy": "गर्भावस्था के दौरान यह महत्वपूर्ण है। कृपया तुरंत अपने ASHA कार्यकर्ता या डॉक्टर से मिलें। (This is important during pregnancy. Please meet your ASHA worker or doctor immediately.)",
            
            "emergency": "यह गंभीर हो सकता है। कृपया तुरंत नज़दीकी स्वास्थ्य केंद्र जाएं। (This could be serious. Please go to the nearest health center immediately.)"
        }
        
        # Check for emergency keywords
        emergency_keywords = ["bleeding", "खून", "severe pain", "बहुत दर्द", "unconscious"]
        query_lower = user_query.lower()
        
        if any(kw in query_lower for kw in emergency_keywords):
            message = fallback_messages["emergency"]
        elif pregnancy_stage:
            message = fallback_messages["pregnancy"]
        else:
            message = fallback_messages["default"]
        
        return {
            "answer": message,
            "evidence_used": 0,
            "should_escalate": True,
            "confidence": "fallback",
            "debug_error": error_details  # Pass error to debug view
        }
    
    def _apply_safety_filters(self, answer: str) -> str:
        """Remove diagnosis language and ensure safety"""
        
        # Replace diagnosis language
        diagnosis_terms = [
            ("you have", "you may be experiencing"),
            ("diagnosed with", "showing symptoms of"),
            ("this is", "this could be"),
            ("definitely", "possibly"),
        ]
        
        for old, new in diagnosis_terms:
            answer = answer.replace(old, new)
        
        # Ensure escalation guidance is present for serious terms
        serious_terms = ["blood", "severe", "खून", "गंभीर"]
        if any(term in answer.lower() for term in serious_terms):
            if "doctor" not in answer.lower() and "डॉक्टर" not in answer:
                answer += " कृपया डॉक्टर से मिलें। (Please see a doctor.)"
        
        return answer
    
    def _check_escalation_needed(self, retrieval_results: Dict[str, Any]) -> bool:
        """Check if any evidence indicates escalation needed"""
        
        # Check user memories for high risk
        memories = retrieval_results.get("user_memories", [])
        for memory in memories[:3]:  # Check top 3
            risk = memory.get("payload", {}).get("risk_score", 0.0)
            if risk > 0.7:
                return True
        
        # Check medical knowledge for danger signs
        medical = retrieval_results.get("medical_knowledge", [])
        for item in medical:
            content = item.get("content", "").lower()
            if any(term in content for term in ["danger", "emergency", "immediate", "urgent"]):
                return True
        
        return False


# Global instance
llm_handler = LLMHandler()
