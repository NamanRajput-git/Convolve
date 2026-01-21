"""
Configuration management for ASHA AI
Loads environment variables and provides system-wide settings
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# Collection Names (NON-NEGOTIABLE)
COLLECTION_USER_HEALTH_MEMORY = "user_health_memory"
COLLECTION_MEDICAL_KNOWLEDGE = "verified_medical_knowledge"
COLLECTION_NUTRITION_PATTERNS = "nutrition_patterns"
COLLECTION_ASHA_INSIGHTS = "asha_population_insights"

# Embedding Configuration (Google Gemini)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
EMBEDDING_DIMENSION = 768  # Google embedding-001 produces 768-dim vectors

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL = "models/gemini-2.5-flash"  # Verified available model
LLM_TEMPERATURE = 0.3  # Lower for more consistent medical advice

# Voice Configuration
GOOGLE_SPEECH_API_KEY = os.getenv("GOOGLE_SPEECH_API_KEY")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "hi")  # Hindi default
SUPPORTED_LANGUAGES = os.getenv("SUPPORTED_LANGUAGES", "hi,en").split(",")

# Language codes for speech recognition
LANGUAGE_CODES = {
    "hi": "hi-IN",  # Hindi
    "en": "en-IN",  # English (India)
    "ta": "ta-IN",  # Tamil
    "bn": "bn-IN",  # Bengali
    "te": "te-IN",  # Telugu
    "mr": "mr-IN",  # Marathi
}

# Privacy Settings
HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "sha256")
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
AUTO_WIPE_ENABLED = os.getenv("AUTO_WIPE_ENABLED", "true").lower() == "true"

# Memory Settings
MAX_MEMORY_DAYS = int(os.getenv("MAX_MEMORY_DAYS", "365"))
MEMORY_DECAY_RATE = 0.95  # Decay factor for old low-risk signals
MEMORY_REINFORCEMENT_BOOST = 1.5  # Boost factor for repeated symptoms

# Risk Thresholds
RISK_THRESHOLD_HIGH = float(os.getenv("RISK_THRESHOLD_HIGH", "0.7"))
RISK_THRESHOLD_MEDIUM = float(os.getenv("RISK_THRESHOLD_MEDIUM", "0.4"))

# Retrieval Configuration
RETRIEVAL_TOP_K = 10  # Number of similar memories to retrieve
RERANK_TOP_K = 5  # Number of top results after re-ranking

# System Paths
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
TEMP_AUDIO_DIR = BASE_DIR / "temp_audio"

# Create necessary directories
LOGS_DIR.mkdir(exist_ok=True)
TEMP_AUDIO_DIR.mkdir(exist_ok=True)

# Validation
def validate_config():
    """Validate critical configuration"""
    errors = []
    
    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY not set in environment")
    
    if QDRANT_HOST == "localhost" and QDRANT_PORT != 6333:
        print(f"Warning: Using non-standard Qdrant port {QDRANT_PORT}")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Run validation on import
validate_config()
