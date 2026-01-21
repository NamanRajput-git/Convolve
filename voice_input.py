"""
Voice input processing for ASHA AI
Handles speech-to-text conversion with multilingual support
"""

import speech_recognition as sr
from typing import Optional, Tuple
from loguru import logger
import config
from pathlib import Path
import tempfile


class VoiceInput:
    """Handles voice input processing"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        logger.info("Voice input handler initialized")
    
    def process_audio_file(
        self,
        audio_file_path: str,
        language: str = "hi"
    ) -> Tuple[Optional[str], bool]:
        """
        Process uploaded audio file and convert to text
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (hi, en, ta, etc.)
            
        Returns:
            (transcribed_text, success)
        """
        try:
            # Get language code
            lang_code = config.LANGUAGE_CODES.get(language, "hi-IN")
            
            # Load audio file
            with sr.AudioFile(audio_file_path) as source:
                audio_data = self.recognizer.record(source)
            
            # Recognize speech using Google Speech Recognition
            text = self.recognizer.recognize_google(
                audio_data,
                language=lang_code
            )
            
            logger.info(f"Transcribed ({language}): {text[:100]}...")
            return text, True
            
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return None, False
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None, False
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return None, False
    
    def process_microphone_input(
        self,
        language: str = "hi",
        timeout: int = 10
    ) -> Tuple[Optional[str], bool]:
        """
        Record from microphone and convert to text
        
        Args:
            language: Language code
            timeout: Recording timeout in seconds
            
        Returns:
            (transcribed_text, success)
        """
        try:
            # Get language code
            lang_code = config.LANGUAGE_CODES.get(language, "hi-IN")
            
            with sr.Microphone() as source:
                logger.info("Listening...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Record audio
                audio_data = self.recognizer.listen(source, timeout=timeout)
            
            logger.info("Processing audio...")
            
            # Recognize speech
            text = self.recognizer.recognize_google(
                audio_data,
                language=lang_code
            )
            
            logger.info(f"Transcribed ({language}): {text[:100]}...")
            return text, True
            
        except sr.WaitTimeoutError:
            logger.warning("Recording timeout - no speech detected")
            return None, False
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return None, False
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None, False
        except Exception as e:
            logger.error(f"Microphone input failed: {e}")
            return None, False
    
    def save_uploaded_audio(self, uploaded_file) -> str:
        """
        Save Streamlit uploaded file to temporary location
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Path to saved file
        """
        # Create temp file
        suffix = Path(uploaded_file.name).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=config.TEMP_AUDIO_DIR
        )
        
        # Write uploaded content
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        
        logger.info(f"Saved uploaded audio: {temp_file.name}")
        return temp_file.name
    
    def cleanup_audio_file(self, file_path: str):
        """Delete temporary audio file (privacy compliance)"""
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete audio file: {e}")


# Global instance
voice_input = VoiceInput()
