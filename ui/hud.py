"""
HUD Overlay for JARVIS

A frameless, transparent PyQt6 window that sits on the desktop
and reacts to JARVIS's internal state.
Runs in a separate process to avoid GIL/thread blocking with the main CLI.
"""

import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush

from core.state import get_state

class JarvisHUD(QWidget):
    def __init__(self):
        super().__init__()
        
        # Window settings for a transparent, frameless, always-on-top overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Put it in the bottom right corner (we'll estimate for now, standard 1080p)
        self.setGeometry(1700, 900, 150, 150)
        
        # State variables
        self.jarvis_state = "idle"
        self.animation_tick = 0
        
        # Poll state every 200ms
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.poll_state)
        self.state_timer.start(200)
        
        # Animation loop (60fps)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(16)
        
    def poll_state(self):
        state = get_state()
        self.jarvis_state = state.get("status", "idle")
        
    def update_animation(self):
        self.animation_tick += 1
        self.update() # Trigger a repaint
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = 40
        
        # Determine colors based on state
        if self.jarvis_state == "thinking":
            # Pulsing orange/yellow
            base_color = QColor(255, 170, 0)
            glow_intensity = 40 + math.sin(self.animation_tick * 0.1) * 20
        elif self.jarvis_state == "speaking":
            # Fast pulsing blue
            base_color = QColor(0, 150, 255)
            glow_intensity = 30 + math.sin(self.animation_tick * 0.3) * 30
            radius = 40 + math.sin(self.animation_tick * 0.5) * 10
        elif self.jarvis_state == "listening":
            # Steady green
            base_color = QColor(0, 255, 100)
            glow_intensity = 50
        else:
            # Idle - slow pulse cyan
            base_color = QColor(0, 229, 255)
            glow_intensity = 20 + math.sin(self.animation_tick * 0.05) * 10
            
        # Draw Glow (Radial Gradient)
        gradient = QRadialGradient(center_x, center_y, radius + glow_intensity)
        
        glow_color = QColor(base_color)
        glow_color.setAlpha(100)
        gradient.setColorAt(0, glow_color)
        
        edge_color = QColor(base_color)
        edge_color.setAlpha(0)
        gradient.setColorAt(1, edge_color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(radius + glow_intensity), int(radius + glow_intensity))
        
        # Draw Core
        painter.setBrush(QBrush(base_color))
        # White hot center
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(radius), int(radius))


def run_hud():
    """Entry point for the multiprocessing.Process."""
    app = QApplication(sys.argv)
    hud = JarvisHUD()
    hud.show()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    run_hud()
