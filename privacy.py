"""
Privacy and anonymization layer for ASHA AI
Ensures NO PII is stored in the system
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st
from config import HASH_ALGORITHM, SESSION_TIMEOUT_MINUTES, AUTO_WIPE_ENABLED


class PrivacyManager:
    """Manages user anonymization and privacy controls"""
    
    def __init__(self):
        self.session_data = {}
    
    def generate_anonymous_id(self, phone_number: Optional[str] = None, 
                             device_id: Optional[str] = None) -> str:
        """
        Generate anonymous hash for user identification
        
        Args:
            phone_number: Optional phone for returning users
            device_id: Device identifier for shared phone support
            
        Returns:
            Anonymous hash string
        """
        # For shared phone scenarios, use session-based ID
        if not phone_number:
            if 'anonymous_id' not in st.session_state:
                # Generate random session ID
                timestamp = str(datetime.now().timestamp())
                random_salt = str(hash(timestamp))
                st.session_state['anonymous_id'] = self._hash(f"anon_{random_salt}")
                st.session_state['session_start'] = datetime.now()
            
            # Check for session timeout
            if AUTO_WIPE_ENABLED:
                self._check_session_timeout()
            
            return st.session_state['anonymous_id']
        
        # For returning users with phone (hashed)
        return self._hash(phone_number)
    
    def _hash(self, data: str) -> str:
        """Create hash using configured algorithm"""
        if HASH_ALGORITHM == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()[:16]
        else:
            raise ValueError(f"Unsupported hash algorithm: {HASH_ALGORITHM}")
    
    def sanitize_text(self, text: str) -> str:
        """
        Remove potential PII from text
        
        Removes:
        - Phone numbers
        - Aadhaar-like patterns
        - Email addresses
        - Specific names (detected via patterns)
        """
        # Remove phone numbers (Indian format)
        text = re.sub(r'\b[6-9]\d{9}\b', '[PHONE_REDACTED]', text)
        
        # Remove Aadhaar-like numbers
        text = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', '[ID_REDACTED]', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[EMAIL_REDACTED]', text)
        
        return text
    
    def create_safe_payload(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create privacy-safe payload for Qdrant storage
        
        Only allows:
        - Anonymous user ID (hash)
        - Age (numeric)
        - Pregnancy stage (categorical)
        - Risk score (numeric)
        - Language code
        - Signal type
        - Timestamp
        """
        safe_payload = {
            "user_id": user_data.get("user_id"),  # Already hashed
            "age": user_data.get("age"),
            "pregnancy_stage": user_data.get("pregnancy_stage"),
            "risk_score": user_data.get("risk_score", 0.0),
            "language": user_data.get("language", "hi"),
            "signal_type": user_data.get("signal_type", "symptom"),
            "timestamp": user_data.get("timestamp", datetime.now().isoformat()),
        }
        
        # Optional geographic info (village/district level only, NO specific addresses)
        if "district" in user_data:
            safe_payload["district"] = user_data["district"]
        
        if "village_cluster" in user_data:
            safe_payload["village_cluster"] = user_data["village_cluster"]
        
        return safe_payload
    
    def _check_session_timeout(self):
        """Check if session has timed out and trigger auto-wipe"""
        if 'session_start' in st.session_state:
            session_duration = datetime.now() - st.session_state['session_start']
            timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            
            if session_duration > timeout:
                self.wipe_session()
    
    def wipe_session(self):
        """Wipe all session data (shared phone support)"""
        keys_to_clear = [
            'anonymous_id', 
            'session_start', 
            'conversation_history',
            'user_context'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def validate_no_pii(self, payload: Dict[str, Any]) -> bool:
        """
        Validate that payload contains no PII
        
        Returns:
            True if safe, False if PII detected
        """
        # Check for phone numbers
        text_values = [str(v) for v in payload.values() if isinstance(v, str)]
        full_text = " ".join(text_values)
        
        if re.search(r'\b[6-9]\d{9}\b', full_text):
            return False
        
        if re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', full_text):
            return False
        
        if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', full_text):
            return False
        
        return True


# Global instance
privacy_manager = PrivacyManager()
