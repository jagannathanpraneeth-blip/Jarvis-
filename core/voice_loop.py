"""
JARVIS Voice Orchestrator

Coordinates Wake Word -> STT -> LLM -> TTS pipeline.
Handles push-to-talk and barge-in.
"""

import math
import queue
import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd

from core.brain import Brain
from core.config import Settings
from core.logger import get_logger
from core.stt import SpeechToText
from core.tts import TTSManager
from core.wake_word import WakeWordDetector

logger = get_logger("voice")


class VoiceLoop:
    def __init__(self, settings: Settings, brain: Brain):
        self.settings = settings
        self.brain = brain
        self._running = False
        
        # Audio capturing state
        self._is_recording = False
        self._audio_buffer = []
        self._silence_start = None
        self._audio_queue = queue.Queue()
        
        # Initialize modules
        self.stt = SpeechToText(settings)
        self.tts = TTSManager(settings)
        
        # We start wake word detector later to avoid conflicts with other audio usage
        self.wake_word = WakeWordDetector(settings, self._on_wake_word_detected)
        
        # Push-to-talk state
        self._ptt_pressed = False
        self._ptt_listener = None
        self._setup_ptt()
        
    def _setup_ptt(self):
        """Set up push-to-talk keyboard listener."""
        key_name = self.settings.voice.push_to_talk_key.lower()
        if not key_name:
            return
            
        try:
            from pynput import keyboard
            
            # Map common key names to pynput keys
            key_map = {
                "space": keyboard.Key.space,
                "alt": keyboard.Key.alt,
                "ctrl": keyboard.Key.ctrl,
                "shift": keyboard.Key.shift,
            }
            target_key = key_map.get(key_name)
            
            def on_press(key):
                if target_key and key == target_key or getattr(key, 'char', None) == key_name:
                    if not self._ptt_pressed:
                        self._ptt_pressed = True
                        self._on_ptt_pressed()
                        
            def on_release(key):
                if target_key and key == target_key or getattr(key, 'char', None) == key_name:
                    self._ptt_pressed = False
                    self._on_ptt_released()
                    
            self._ptt_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._ptt_listener.start()
            logger.info(f"Push-to-talk enabled (Key: {key_name})")
        except ImportError:
            logger.warning("pynput not installed. Push-to-talk disabled.")
        except Exception as e:
            logger.warning(f"Failed to setup push-to-talk: {e}")
            
    def _on_wake_word_detected(self):
        """Callback from WakeWordDetector."""
        if self._is_recording:
            return
            
        logger.info("Wake word triggered.")
        self._barge_in()
        self._start_recording()
        
    def _on_ptt_pressed(self):
        """Callback from pynput."""
        if self._is_recording:
            return
            
        logger.info("Push-to-talk triggered.")
        self._barge_in()
        self._start_recording()
        
    def _on_ptt_released(self):
        """Callback from pynput."""
        if self._is_recording:
            logger.info("Push-to-talk released.")
            self._stop_recording()
            
    def _barge_in(self):
        """Stop TTS playback if active."""
        if self.tts.is_playing:
            self.tts.stop()
            logger.info("Barge-in: TTS stopped.")
            
    def _play_chime(self):
        """Play a short beep to indicate listening."""
        try:
            # Generate a short 440Hz beep
            fs = 44100
            duration = 0.1
            t = np.linspace(0, duration, int(fs * duration), False)
            audio = np.sin(440 * 2 * np.pi * t) * 0.3
            # Fade out to avoid click
            audio[-441:] *= np.linspace(1, 0, 441)
            sd.play(audio, fs)
            sd.wait()
        except Exception:
            pass

    def _calculate_rms(self, indata: np.ndarray) -> float:
        """Calculate Root Mean Square (audio energy level)."""
        if len(indata) == 0:
            return 0.0
        # Convert to float for calculation to avoid overflow
        data = indata.astype(np.float32) / 32768.0
        return math.sqrt(np.mean(data**2))

    def _audio_callback(self, indata, frames, time_info, status):
        """sounddevice callback during active recording."""
        if status:
            logger.warning(f"Audio callback status: {status}")
            
        if not self._is_recording:
            return
            
        data = indata.copy()
        self._audio_buffer.append(data)
        
        # Check for silence (only if not holding PTT)
        if not self._ptt_pressed:
            rms = self._calculate_rms(data)
            
            if rms < self.settings.voice.silence_threshold:
                if self._silence_start is None:
                    self._silence_start = time.time()
                elif time.time() - self._silence_start > self.settings.voice.silence_duration:
                    # Queue a message to stop recording on the main thread
                    self._audio_queue.put("SILENCE_TIMEOUT")
            else:
                self._silence_start = None

    def _start_recording(self):
        """Transition from wake-word listening to active recording."""
        # Stop wake word detector temporarily
        self.wake_word.stop()
        
        self._is_recording = True
        self._audio_buffer = []
        self._silence_start = None
        
        self._play_chime()
        logger.info("Listening...")
        
        # Start recording stream
        # STT models expect 16kHz mono
        try:
            self.stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype="int16",
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as e:
            logger.error(f"Failed to start recording stream: {e}")
            self._is_recording = False
            self.wake_word.start_listening()

    def _stop_recording(self):
        """Stop active recording and process audio."""
        if not self._is_recording:
            return
            
        self._is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            
        logger.info("Processing speech...")
        
        if not self._audio_buffer:
            logger.warning("No audio recorded.")
            self.wake_word.start_listening()
            return
            
        # Combine chunks
        audio_data = np.concatenate(self._audio_buffer).flatten()
        self._audio_buffer = []
        
        # Start processing thread
        threading.Thread(target=self._process_audio, args=(audio_data,), daemon=True).start()

    def _process_audio(self, audio_data: np.ndarray):
        """STT -> Brain -> TTS pipeline."""
        try:
            # 1. Speech to Text
            text = self.stt.transcribe(audio_data)
            
            if not text or len(text.strip()) < 2:
                logger.info("No speech detected or transcription too short.")
                self.wake_word.start_listening()
                return
                
            print(f"\nUser: {text}")
            
            # 2. Brain processing
            # We don't want to block voice interface completely if we hit a quota limit,
            # but we'll let the Brain's built-in retry logic handle temporary 429s.
            try:
                response = self.brain.think(text)
                print(f"JARVIS: {response}\n")
                
                # 3. Text to Speech
                # Play asynchronously so barge-in works
                if response:
                    self.tts.speak(response, block=False)
                    
                    # Wait for TTS to finish OR barge-in to happen
                    while self.tts.is_playing and self._running:
                        time.sleep(0.1)
                        
            except Exception as e:
                logger.error(f"Brain processing failed: {e}")
                self.tts.speak("I'm sorry, I encountered an error processing your request.", block=False)
                while self.tts.is_playing:
                    time.sleep(0.1)
                    
        finally:
            # Restart wake word listener if not already recording a new utterance
            if self._running and not self._is_recording:
                if self.settings.voice.continuous_conversation:
                    # In continuous mode, listen again immediately without wake word
                    logger.info("Continuous mode: listening for reply...")
                    self._start_recording()
                else:
                    self.wake_word.start_listening()

    def start(self):
        """Start the main voice loop."""
        self._running = True
        logger.info("Voice loop started. Waiting for wake word or push-to-talk...")
        
        # Run wake word listening in a background thread
        ww_thread = threading.Thread(target=self.wake_word.start_listening, daemon=True)
        ww_thread.start()
        
        try:
            while self._running:
                try:
                    # Check for messages from audio callback
                    msg = self._audio_queue.get(timeout=0.1)
                    if msg == "SILENCE_TIMEOUT":
                        self._stop_recording()
                except queue.Empty:
                    pass
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop all voice components."""
        logger.info("Stopping voice loop...")
        self._running = False
        self.wake_word.stop()
        if hasattr(self, 'stream') and self.stream.active:
            self.stream.stop()
            self.stream.close()
        if self._ptt_listener:
            self._ptt_listener.stop()
        self.tts.stop()
