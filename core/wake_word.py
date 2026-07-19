"""
JARVIS Wake Word Detection

Uses openwakeword to detect 'hey_jarvis' locally.
Continuously processes audio chunks and triggers a callback.
"""

from __future__ import annotations

import queue
from typing import Callable

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

from core.config import Settings
from core.logger import get_logger

logger = get_logger("wake_word")


class WakeWordDetector:
    """Continuously listens for the wake word using an audio stream."""

    def __init__(self, settings: Settings, on_detected: Callable[[], None]):
        self._settings = settings
        self._on_detected = on_detected
        self._running = False
        self._audio_queue = queue.Queue()
        self._threshold = settings.voice.wake_word_threshold
        
        # openwakeword requires 16000Hz, 1 channel, 16-bit PCM
        self._sample_rate = 16000
        self._chunk_size = 1280
        
        logger.info(f"Loading wake word model: {settings.voice.wake_word}")
        # Use onnx framework for Windows
        self._model = Model(wakeword_models=[settings.voice.wake_word], inference_framework="onnx")
        logger.info("Wake word model loaded.")

    def _audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio block."""
        if status:
            logger.warning(f"Sounddevice status: {status}")
        # openwakeword expects int16 arrays
        self._audio_queue.put(indata.copy())

    def start_listening(self):
        """Start the microphone stream and processing loop."""
        self._running = True
        
        try:
            with sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self._chunk_size,
                callback=self._audio_callback
            ):
                logger.info("Listening for wake word...")
                while self._running:
                    try:
                        audio_chunk = self._audio_queue.get(timeout=0.5)
                        # Flatten to 1D array
                        audio_data = audio_chunk.flatten()
                        
                        # Process audio
                        prediction = self._model.predict(audio_data)
                        
                        # Check confidence
                        model_name = self._settings.voice.wake_word
                        confidence = prediction.get(model_name, 0.0)
                        
                        if confidence > self._threshold:
                            logger.info(f"Wake word detected! (confidence: {confidence:.2f})")
                            # Clear queue to avoid double-triggers
                            while not self._audio_queue.empty():
                                self._audio_queue.get_nowait()
                            
                            self._on_detected()
                            
                    except queue.Empty:
                        continue
        except Exception as e:
            logger.error(f"Error in wake word listener: {e}", exc_info=True)
            self._running = False

    def stop(self):
        """Stop the listening loop."""
        self._running = False
        logger.info("Wake word listener stopped.")
