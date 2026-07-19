"""Verify Voice Dependencies"""
import sys
import os
import traceback

print("Testing Voice Dependencies...")

try:
    print("Loading sounddevice...")
    import sounddevice as sd
    print("sounddevice OK")

    print("Loading openwakeword...")
    from openwakeword.model import Model
    print("openwakeword OK")

    print("Loading faster-whisper...")
    from faster_whisper import WhisperModel
    print("faster-whisper OK")
    
    print("Loading piper-tts...")
    from piper import PiperVoice
    print("piper-tts OK")
    
    print("Loading pynput...")
    from pynput import keyboard
    print("pynput OK")
    
    print("\nALL IMPORTS SUCCESSFUL")
    sys.exit(0)
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
