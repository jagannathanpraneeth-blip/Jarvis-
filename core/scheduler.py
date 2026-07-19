"""
Proactive Background Scheduler for JARVIS

Uses APScheduler to periodically wake JARVIS up to check system state
(battery, time) and allow him to initiate conversation autonomously.
"""

import threading
import psutil
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.logger import get_logger

logger = get_logger("core.scheduler")


class JARVISScheduler:
    def __init__(self, settings, brain, buffer):
        self.settings = settings
        self.brain = brain
        self.buffer = buffer
        self.scheduler = BackgroundScheduler()
        
    def _proactive_check(self):
        """The routine that JARVIS runs to decide if he should speak up."""
        logger.info("Running proactive background check...")
        
        # 1. Gather Telemetry
        battery = psutil.sensors_battery()
        battery_str = "Unknown"
        if battery:
            battery_str = f"{battery.percent}% (Plugged in: {battery.power_plugged})"
            
        # 2. Formulate the internal prompt
        prompt = (
            f"[SYSTEM INTERNAL: PROACTIVE CHECK]\n"
            f"Current Battery: {battery_str}\n"
            f"You are waking up in the background. If you notice something urgent "
            f"(like battery is under 20% and not plugged in), you MUST speak up and warn the user. "
            f"Otherwise, you can just say hello, ask how they are doing, or output 'IGNORE' if you prefer to stay quiet. "
            f"If you output 'IGNORE', nothing will be spoken."
        )
        
        # 3. Ask the Brain
        try:
            history = self.buffer.get_history()
            response = self.brain.think(prompt, history)
            
            if response and "IGNORE" not in response:
                print(f"\n\n  JARVIS (Proactive): {response}\n")
                self.buffer.add("user", prompt)
                self.buffer.add("assistant", response)
                
                # If voice is enabled (or we just want to proactively speak regardless)
                if not getattr(self.settings.voice, 'muted', False):
                    from core.state import set_state
                    import pyttsx3
                    set_state("speaking")
                    try:
                        engine = pyttsx3.init()
                        engine.say(response)
                        engine.runAndWait()
                    finally:
                        set_state("idle")
        except Exception as e:
            logger.error(f"Proactive check failed: {e}")

    def start(self):
        """Starts the background scheduler."""
        # For testing, we run it every 10 minutes. 
        # (You can change this to hours or add specific cron triggers)
        self.scheduler.add_job(
            self._proactive_check,
            trigger=IntervalTrigger(minutes=10),
            id="proactive_check",
            name="JARVIS Proactive Telemetry Check",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Proactive background scheduler started.")
        
    def stop(self):
        self.scheduler.shutdown(wait=False)
