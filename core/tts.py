"""
JARVIS Text-to-Speech

Supports PiperTTS (primary) and pyttsx3 (fallback).
Provides async playback with barge-in support.
"""

import abc
import os
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd

from core.config import Settings
from core.logger import get_logger

logger = get_logger("tts")


class TTSEngine(abc.ABC):
    """Abstract base class for TTS engines."""
    
    @abc.abstractmethod
    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """Synthesize text to audio. Returns (audio_data, sample_rate)."""
        pass


class SystemTTS(TTSEngine):
    """Fallback TTS using the OS built-in engine via pyttsx3."""
    
    def __init__(self):
        import pyttsx3
        self._engine = pyttsx3.init()
        # Improve voice if on Windows
        voices = self._engine.getProperty('voices')
        for voice in voices:
            if "Zira" in voice.name or "Hazel" in voice.name:
                self._engine.setProperty('voice', voice.id)
                break
        
    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            
        try:
            self._engine.save_to_file(text, temp_path)
            self._engine.runAndWait()
            
            sample_rate, audio_data = wavfile.read(temp_path)
            # Ensure float32 for playback
            if audio_data.dtype != np.float32:
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
            
            return audio_data, sample_rate
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class PiperTTS(TTSEngine):
    """Local, natural TTS using piper-tts."""
    
    def __init__(self, voice_name: str):
        from piper import PiperVoice
        from piper.download import ensure_voice_exists
        
        # Piper requires model and config files
        data_dir = Path(os.path.expanduser("~/.local/share/piper"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = data_dir / f"{voice_name}.onnx"
        config_path = data_dir / f"{voice_name}.onnx.json"
        
        if not model_path.exists():
            logger.info(f"Downloading Piper voice: {voice_name}")
            ensure_voice_exists(
                voice_name,
                [str(data_dir)],
                [str(data_dir)]
            )
            
        logger.info(f"Loading Piper voice: {voice_name}")
        self._voice = PiperVoice.load(str(model_path), str(config_path))
        logger.info("Piper voice loaded.")
        
    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        # Synthesize returns an iterator of audio chunks
        audio_stream = self._voice.synthesize_stream_raw(text)
        
        chunks = []
        for chunk in audio_stream:
            # Piper outputs 16-bit PCM mono
            audio_array = np.frombuffer(chunk, dtype=np.int16)
            chunks.append(audio_array)
            
        if not chunks:
            return np.array([], dtype=np.float32), self._voice.config.sample_rate
            
        audio_data = np.concatenate(chunks)
        # Convert to float32 for sounddevice playback
        audio_data = audio_data.astype(np.float32) / 32768.0
        
        return audio_data, self._voice.config.sample_rate


class TTSManager:
    """Manages TTS generation and playback with barge-in support."""
    
    def __init__(self, settings: Settings):
        self._settings = settings
        self._engine: TTSEngine
        self._is_playing = False
        
        if settings.voice.tts_engine == "piper":
            try:
                self._engine = PiperTTS(settings.voice.tts_voice)
            except Exception as e:
                logger.error(f"Failed to load PiperTTS, falling back to SystemTTS: {e}")
                self._engine = SystemTTS()
        else:
            self._engine = SystemTTS()
            
    def speak(self, text: str, block: bool = True):
        """Synthesize and play speech."""
        # Simple cleanup to make TTS sound better
        text = text.replace("*", "").replace("#", "")
        
        logger.info(f"Synthesizing speech: {text[:50]}...")
        start_time = time.time()
        
        try:
            audio_data, sample_rate = self._engine.synthesize(text)
            elapsed = time.time() - start_time
            logger.info(f"Synthesis complete in {elapsed:.2f}s")
            
            if len(audio_data) > 0:
                self._play_audio(audio_data, sample_rate, block)
                
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            
    def _play_audio(self, audio_data: np.ndarray, sample_rate: int, block: bool):
        self._is_playing = True
        
        def _play():
            try:
                sd.play(audio_data, sample_rate)
                if block:
                    sd.wait()
            except sd.PortAudioError as e:
                logger.error(f"Audio playback error: {e}")
            finally:
                self._is_playing = False
                
        if block:
            _play()
        else:
            threading.Thread(target=_play, daemon=True).start()
            
    def stop(self):
        """Stop playback immediately (barge-in)."""
        if self._is_playing:
            logger.info("Stopping TTS playback (barge-in)...")
            sd.stop()
            self._is_playing = False
            
    @property
    def is_playing(self) -> bool:
        return self._is_playing
