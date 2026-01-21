"""
Risk scoring logic for ASHA AI
Analyzes symptoms and assigns risk scores
"""

from typing import Dict, Any
from loguru import logger


class RiskScorer:
    """Calculates risk scores based on symptoms and context"""
    
    def __init__(self):
        # Symptom severity mapping
        self.symptom_severity = {
            # High risk symptoms (pregnancy)
            "bleeding": 0.9,
            "खून": 0.9,
            "severe pain": 0.8,
            "बहुत दर्द": 0.8,
            "unconscious": 1.0,
            "बेहोश": 1.0,
            "convulsion": 0.95,
            "दौरा": 0.95,
            "blurred vision": 0.75,
            "धुंधला दिखना": 0.75,
            "swelling": 0.6,
            "सूजन": 0.6,
            
            # Medium risk symptoms
            "headache": 0.5,
            "सिरदर्द": 0.5,
            "fever": 0.6,
            "बुखार": 0.6,
            "vomiting": 0.55,
            "उल्टी": 0.55,
            "dizziness": 0.5,
            "चक्कर": 0.5,
            "weakness": 0.4,
            "कमजोरी": 0.4,
            
            # Low risk symptoms
            "nausea": 0.3,
            "मतली": 0.3,
            "tired": 0.25,
            "थकान": 0.25,
            "back pain": 0.3,
            "पीठ दर्द": 0.3,
        }
        
        # Pregnancy stage risk multipliers
        self.pregnancy_multipliers = {
            "1st_trimester": 1.1,
            "2nd_trimester": 1.0,
            "3rd_trimester": 1.2,
            "postpartum": 1.15
        }
    
    def calculate_risk_score(
        self,
        query_text: str,
        user_context: Dict[str, Any],
        retrieval_results: Dict[str, Any] = None
    ) -> float:
        """
        Calculate composite risk score
        
        Args:
            query_text: User's symptom description
            user_context: User metadata
            retrieval_results: Optional retrieval context
            
        Returns:
            Risk score (0-1)
        """
        # Base risk from symptom matching
        symptom_risk = self._match_symptom_severity(query_text)
        
        # Adjust for pregnancy stage
        pregnancy_stage = user_context.get("pregnancy_stage")
        multiplier = self.pregnancy_multipliers.get(pregnancy_stage, 1.0)
        
        adjusted_risk = symptom_risk * multiplier
        
        # Boost if similar high-risk past signals exist
        if retrieval_results:
            memory_boost = self._calculate_memory_boost(retrieval_results)
            adjusted_risk = min(1.0, adjusted_risk + memory_boost)
        
        # Age adjustments (higher risk for very young or older mothers)
        age = user_context.get("age", 25)
        if age < 18 or age > 35:
            adjusted_risk = min(1.0, adjusted_risk * 1.15)
        
        # Cap at 1.0
        final_risk = min(1.0, max(0.1, adjusted_risk))
        
        logger.info(f"Risk score calculated: {final_risk:.2f} (base: {symptom_risk:.2f})")
        return final_risk
    
    def _match_symptom_severity(self, text: str) -> float:
        """Match symptoms in text to severity scores"""
        text_lower = text.lower()
        
        matched_risks = []
        for symptom, severity in self.symptom_severity.items():
            if symptom in text_lower:
                matched_risks.append(severity)
        
        if not matched_risks:
            # No specific symptoms matched - default low-moderate risk
            return 0.3
        
        # Use maximum severity found
        return max(matched_risks)
    
    def _calculate_memory_boost(self, retrieval_results: Dict[str, Any]) -> float:
        """Calculate risk boost from past similar high-risk memories"""
        memories = retrieval_results.get("user_memories", [])
        
        boost = 0.0
        for memory in memories[:3]:  # Check top 3
            past_risk = memory.get("payload", {}).get("risk_score", 0.0)
            similarity = memory.get("score", 0.0)
            
            # If similar memory was high risk, boost current risk
            if past_risk > 0.7 and similarity > 0.8:
                boost += 0.1
        
        return min(0.3, boost)  # Cap boost at 0.3
    
    def get_risk_category(self, risk_score: float) -> str:
        """Convert numeric risk to category"""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def get_risk_color(self, risk_score: float) -> str:
        """Get color for UI display"""
        category = self.get_risk_category(risk_score)
        return {
            "high": "🔴 High",
            "medium": "🟡 Medium",
            "low": "🟢 Low"
        }[category]


# Global instance
risk_scorer = RiskScorer()
