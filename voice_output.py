"""
Voice output processing for ASHA AI
Converts text responses to speech
"""

from gtts import gTTS
from typing import Optional
from loguru import logger
import config
from pathlib import Path
import tempfile


class VoiceOutput:
    """Handles text-to-speech conversion"""
    
    def __init__(self):
        logger.info("Voice output handler initialized")
    
    def generate_speech(
        self,
        text: str,
        language: str = "hi",
        slow: bool = False
    ) -> Optional[str]:
        """
        Convert text to speech audio file
        
        Args:
            text: Text to convert
            language: Language code (hi, en, ta, etc.)
            slow: Whether to speak slowly
            
        Returns:
            Path to generated audio file, or None on failure
        """
        try:
            # Map our language codes to gTTS codes
            gtts_lang_map = {
                "hi": "hi",
                "en": "en",
                "ta": "ta",
                "bn": "bn",
                "te": "te",
                "mr": "mr"
            }
            
            gtts_lang = gtts_lang_map.get(language, "hi")
            
            # Generate speech
            tts = gTTS(text=text, lang=gtts_lang, slow=slow)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3",
                dir=config.TEMP_AUDIO_DIR
            )
            
            tts.save(temp_file.name)
            temp_file.close()
            
            logger.info(f"Generated speech audio ({language}): {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            return None
    
    def cleanup_audio_file(self, file_path: str):
        """Delete temporary audio file"""
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete audio file: {e}")


# Global instance
voice_output = VoiceOutput()
