"""
Embedding generation for ASHA AI
Converts text to vectors for Qdrant storage and retrieval
Using sklearn TF-IDF (no PyTorch required - lightweight fallback)
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import numpy as np
from typing import List, Union
from loguru import logger
import config
import hashlib


class EmbeddingEncoder:
    """Handles all text-to-vector conversions using TF-IDF (PyTorch-free)"""
    
    def __init__(self):
        """Initialize TF-IDF vectorizer"""
        try:
            logger.info("Initializing TF-IDF embedding encoder (PyTorch-free)")
            # Use a fixed vocabulary size to get consistent 768-dim vectors
            self.vectorizer = TfidfVectorizer(
                max_features=768,  # Match Google's embedding dimension
                ngram_range=(1, 2),
                sublinear_tf=True
            )
            # Pre-fit with some medical/health terms to establish vocabulary
            medical_corpus = [
                "fever headache nausea vomiting diarrhea",
                "pregnancy pregnant trimester delivery postpartum",
                "anemia iron deficiency weakness fatigue dizzy",
                "bleeding spotting discharge pain cramps",
                "nutrition diet food eating vitamins supplements",
               "consultation doctor hospital clinic emergency",
                "symptoms health medical condition illness disease"
            ]
            self.vectorizer.fit(medical_corpus)
            logger.info(f"TF-IDF encoder initialized with {len(self.vectorizer.vocabulary_)} features")
        except Exception as e:
            logger.error(f"Failed to initialize embedding encoder: {e}")
            raise RuntimeError(f"Cannot initialize embedding encoder: {e}")
    
    def encode(self, text: Union[str, List[str]], normalize_vecs: bool = True) -> Union[List[float], List[List[float]]]:
        """
        Convert text to embedding vector(s)
        
        Args:
            text: Single text string or list of strings
            normalize_vecs: Whether to normalize vectors
            
        Returns:
            Single vector or list of vectors
        """
        try:
            if isinstance(text, str):
                # Single text
                vec = self.vectorizer.transform([text]).toarray()[0]
                if normalize_vecs:
                    vec = normalize([vec])[0]
                # Pad or truncate to exactly 768 dimensions
                if len(vec) < 768:
                    vec = np.pad(vec, (0, 768 - len(vec)))
                elif len(vec) > 768:
                    vec = vec[:768]
                return vec.tolist()
            else:
                # Batch of texts
                vecs = self.vectorizer.transform(text).toarray()
                if normalize_vecs:
                    vecs = normalize(vecs)
                # Pad or truncate each vector
                result = []
                for vec in vecs:
                    if len(vec) < 768:
                        vec = np.pad(vec, (0, 768 - len(vec)))
                    elif len(vec) > 768:
                        vec = vec[:768]
                    result.append(vec.tolist())
                return result
        
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def encode_health_signal(self, symptom_text: str, context: dict = None) -> List[float]:
        """
        Encode health signal with optional context
        
        Args:
            symptom_text: User's symptom description
            context: Optional context (age, pregnancy stage, etc.)
            
        Returns:
            Embedding vector
        """
        # Enrich text with context for better retrieval
        enriched_text = symptom_text
        
        if context:
            if context.get("pregnancy_stage"):
                enriched_text = f"Pregnancy {context['pregnancy_stage']}: {symptom_text}"
            
            if context.get("age"):
                enriched_text = f"Age {context['age']} {enriched_text}"
        
        return self.encode(enriched_text)
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Batch encode multiple texts efficiently
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        return self.encode(texts)


# Global instance
embedding_encoder = EmbeddingEncoder()
