"""
JARVIS Speech-to-Text

Uses faster-whisper to transcribe audio locally.
"""

import time
import numpy as np
from faster_whisper import WhisperModel

from core.config import Settings
from core.logger import get_logger

logger = get_logger("stt")


class SpeechToText:
    """Wrapper around faster-whisper for local STT."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._model_size = settings.voice.stt_model
        
        logger.info(f"Loading faster-whisper model: {self._model_size}")
        # Run on CPU with int8 quantization for speed on typical desktop hardware
        # Users with GPUs can change device="cuda"
        self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        logger.info("Faster-whisper model loaded.")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio data from numpy array to text."""
        if len(audio_data) == 0:
            return ""

        # faster-whisper expects float32 normalized to [-1.0, 1.0]
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
            # If original was int16, normalize it
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / 32768.0

        start_time = time.time()
        try:
            # Transcribe the audio
            segments, info = self._model.transcribe(
                audio_data, 
                beam_size=5,
                language="en",
                condition_on_previous_text=False
            )
            
            # Reconstruct text from segments
            text = "".join([segment.text for segment in segments]).strip()
            
            elapsed = time.time() - start_time
            logger.info(f"Transcription complete in {elapsed:.2f}s (lang: {info.language}, prob: {info.language_probability:.2f})")
            
            return text
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}", exc_info=True)
            return ""
