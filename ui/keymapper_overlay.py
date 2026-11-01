"""
On-screen Gaming HUD Key Overlay for BlueStacks Linux.
A transparent, frameless, click-through overlay showing keybindings over the active Android game screen.
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from backend.keymapper_engine import keymapper
from config import config

class KeymapperOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Frameless, transparent, stays on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Match screen / window geometry
        self.resize(1280, 720)
        self.opacity = config.get("overlay_opacity", 0.70)

    def paintEvent(self, event):
        if not keymapper.enabled or not keymapper.profile:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        dpad = keymapper.profile.get("dpad", {})
        if dpad.get("enabled"):
            cx = dpad.get("center_x", 0.16) * w
            cy = dpad.get("center_y", 0.76) * h
            r = dpad.get("radius", 0.08) * min(w, h)

            # Draw outer ring
            painter.setPen(QPen(QColor(0, 168, 255, int(180 * self.opacity)), 2))
            painter.setBrush(QBrush(QColor(0, 128, 255, int(40 * self.opacity))))
            painter.drawEllipse(QPointF(cx, cy), r, r)

            # WASD letters
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255, int(230 * self.opacity))))
            painter.drawText(QRectF(cx - 15, cy - r + 4, 30, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("up_key", "W").upper())
            painter.drawText(QRectF(cx - 15, cy + r - 24, 30, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("down_key", "S").upper())
            painter.drawText(QRectF(cx - r + 4, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("left_key", "A").upper())
            painter.drawText(QRectF(cx + r - 24, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("right_key", "D").upper())

        # Action Keys
        for key_item in keymapper.profile.get("keys", []):
            kx = key_item.get("x", 0.5) * w
            ky = key_item.get("y", 0.5) * h
            kr = key_item.get("radius", 0.035) * min(w, h)
            label = key_item.get("key", "").upper()

            painter.setPen(QPen(QColor(0, 229, 255, int(220 * self.opacity)), 2))
            painter.setBrush(QBrush(QColor(15, 23, 42, int(190 * self.opacity))))
            painter.drawEllipse(QPointF(kx, ky), kr, kr)

            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255, int(255 * self.opacity))))
            painter.drawText(QRectF(kx - kr, ky - kr, kr * 2, kr * 2), Qt.AlignmentFlag.AlignCenter, label)
