"""
Visual Keymap Editor for BlueStacks Linux.
Enables visual drag-and-drop placement of D-Pad (WASD) and action keys over a simulated gaming canvas.
"""
import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QCheckBox, QFrame,
                             QInputDialog, QMessageBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from backend.keymapper_engine import keymapper
from config import config, PROFILES_DIR

class KeymapCanvas(QFrame):
    modified = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background-color: #0A0D14; border: 2px dashed #20293A; border-radius: 8px;")

        self.profile_data = {}
        self.selected_item = None
        self.dragging = False
        self.drag_offset = (0, 0)

    def set_profile(self, data: dict):
        self.profile_data = data
        self.selected_item = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Grid lines for gaming alignment
        painter.setPen(QPen(QColor(255, 255, 255, 15), 1, Qt.PenStyle.DashLine))
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)

        if not self.profile_data:
            return

        # Draw D-Pad
        dpad = self.profile_data.get("dpad", {})
        if dpad.get("enabled"):
            cx = dpad.get("center_x", 0.16) * w
            cy = dpad.get("center_y", 0.76) * h
            r = dpad.get("radius", 0.08) * min(w, h)

            # Outer glow
            painter.setPen(QPen(QColor(0, 168, 255, 200), 2))
            painter.setBrush(QBrush(QColor(0, 128, 255, 45)))
            painter.drawEllipse(QPointF(cx, cy), r, r)

            # Directional arrows & WASD labels
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255, 240)))
            painter.drawText(QRectF(cx - 15, cy - r + 4, 30, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("up_key", "W").upper())
            painter.drawText(QRectF(cx - 15, cy + r - 24, 30, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("down_key", "S").upper())
            painter.drawText(QRectF(cx - r + 4, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("left_key", "A").upper())
            painter.drawText(QRectF(cx + r - 24, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, dpad.get("right_key", "D").upper())

            painter.setPen(QPen(QColor(0, 229, 255, 180)))
            painter.drawText(QRectF(cx - 30, cy - 10, 60, 20), Qt.AlignmentFlag.AlignCenter, "D-PAD")

        # Draw Action Keys
        for idx, key_item in enumerate(self.profile_data.get("keys", [])):
            kx = key_item.get("x", 0.5) * w
            ky = key_item.get("y", 0.5) * h
            kr = key_item.get("radius", 0.035) * min(w, h)
            label = key_item.get("key", "").upper()
            action_desc = key_item.get("label", "")

            is_sel = (self.selected_item == idx)
            fill_color = QColor(0, 168, 255, 180) if is_sel else QColor(30, 41, 59, 210)
            border_color = QColor(0, 229, 255, 255) if is_sel else QColor(0, 128, 255, 180)

            painter.setPen(QPen(border_color, 2))
            painter.setBrush(QBrush(fill_color))
            painter.drawEllipse(QPointF(kx, ky), kr, kr)

            # Key character inside
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QRectF(kx - kr, ky - kr, kr * 2, kr * 2), Qt.AlignmentFlag.AlignCenter, label)

            # Action label beneath
            if action_desc:
                painter.setFont(QFont("Segoe UI", 9))
                painter.setPen(QPen(QColor(148, 163, 184)))
                painter.drawText(QRectF(kx - 40, ky + kr + 2, 80, 18), Qt.AlignmentFlag.AlignCenter, action_desc)

    def mousePressEvent(self, event):
        w = self.width()
        h = self.height()
        pos = event.position()

        # Check D-Pad click
        dpad = self.profile_data.get("dpad", {})
        if dpad.get("enabled"):
            cx = dpad.get("center_x", 0.16) * w
            cy = dpad.get("center_y", 0.76) * h
            r = dpad.get("radius", 0.08) * min(w, h)
            if (pos.x() - cx)**2 + (pos.y() - cy)**2 <= r**2:
                self.selected_item = "dpad"
                self.dragging = True
                self.drag_offset = (pos.x() - cx, pos.y() - cy)
                self.update()
                return

        # Check action keys
        for idx, key_item in enumerate(self.profile_data.get("keys", [])):
            kx = key_item.get("x", 0.5) * w
            ky = key_item.get("y", 0.5) * h
            kr = key_item.get("radius", 0.035) * min(w, h)
            if (pos.x() - kx)**2 + (pos.y() - ky)**2 <= kr**2:
                self.selected_item = idx
                self.dragging = True
                self.drag_offset = (pos.x() - kx, pos.y() - ky)
                self.update()
                return

        self.selected_item = None
        self.update()

    def mouseMoveEvent(self, event):
        if not self.dragging or self.selected_item is None:
            return

        w = self.width()
        h = self.height()
        pos = event.position()

        nx = max(0.02, min(0.98, (pos.x() - self.drag_offset[0]) / w))
        ny = max(0.02, min(0.98, (pos.y() - self.drag_offset[1]) / h))

        if self.selected_item == "dpad":
            self.profile_data["dpad"]["center_x"] = nx
            self.profile_data["dpad"]["center_y"] = ny
        elif isinstance(self.selected_item, int):
            self.profile_data["keys"][self.selected_item]["x"] = nx
            self.profile_data["keys"][self.selected_item]["y"] = ny

        self.modified.emit()
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False

class KeymapperEditorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Control Bar
        top_bar = QHBoxLayout()
        title = QLabel("Game Controls & Keymapper")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")

        self.combo_profiles = QComboBox()
        self.load_profiles_list()
        self.combo_profiles.currentIndexChanged.connect(self.on_profile_selected)

        self.btn_save = QPushButton("💾 Save Profile")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self.save_current_profile)

        self.btn_add_key = QPushButton("➕ Add Key")
        self.btn_add_key.clicked.connect(self.add_key_dialog)

        self.btn_del_key = QPushButton("🗑️ Remove Key")
        self.btn_del_key.setObjectName("DangerButton")
        self.btn_del_key.clicked.connect(self.remove_selected_key)

        top_bar.addWidget(title)
        top_bar.addSpacing(20)
        top_bar.addWidget(QLabel("Profile:"))
        top_bar.addWidget(self.combo_profiles)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_add_key)
        top_bar.addWidget(self.btn_del_key)
        top_bar.addWidget(self.btn_save)
        layout.addLayout(top_bar)

        # Instruction info
        info = QLabel("🎮 Drag any key or the D-Pad to match your game's touch button positions. Press F10 to toggle the on-screen gaming overlay.")
        info.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(info)

        # Visual Canvas
        self.canvas = KeymapCanvas()
        layout.addWidget(self.canvas, 1)

        # Footer toggles
        footer = QHBoxLayout()
        self.chk_dpad = QCheckBox("Enable WASD Movement D-Pad")
        self.chk_dpad.setChecked(True)
        self.chk_dpad.toggled.connect(self.toggle_dpad)

        self.chk_mouselook = QCheckBox("Enable Mouse Look / FPS Aim Mode")
        self.chk_mouselook.toggled.connect(self.toggle_mouselook)

        self.chk_active = QCheckBox("⚡ Keymapper Active (Capturing Keys)")
        self.chk_active.setChecked(True)
        self.chk_active.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.chk_active.toggled.connect(self.toggle_engine)

        footer.addWidget(self.chk_dpad)
        footer.addWidget(self.chk_mouselook)
        footer.addStretch()
        footer.addWidget(self.chk_active)
        layout.addLayout(footer)

        # Load initial profile
        self.load_active_profile()

    def load_profiles_list(self):
        self.combo_profiles.clear()
        if os.path.exists(PROFILES_DIR):
            for f in sorted(os.listdir(PROFILES_DIR)):
                if f.endswith(".json"):
                    k = f[:-5]
                    self.combo_profiles.addItem(k.replace("_", " ").title(), k)

    def load_active_profile(self):
        pname = config.get("active_profile", "roblox")
        idx = self.combo_profiles.findData(pname)
        if idx >= 0:
            self.combo_profiles.setCurrentIndex(idx)
        else:
            self.on_profile_selected()

    def on_profile_selected(self):
        pname = self.combo_profiles.currentData()
        if not pname:
            return
        p_path = os.path.join(PROFILES_DIR, f"{pname}.json")
        if os.path.exists(p_path):
            with open(p_path, "r") as f:
                data = json.load(f)
                self.canvas.set_profile(data)
                self.chk_dpad.setChecked(data.get("dpad", {}).get("enabled", True))
                self.chk_mouselook.setChecked(data.get("mouse_look", {}).get("enabled", False))
                # Update engine
                keymapper.load_profile(p_path)

    def save_current_profile(self):
        pname = self.combo_profiles.currentData()
        if not pname:
            return
        p_path = os.path.join(PROFILES_DIR, f"{pname}.json")
        with open(p_path, "w") as f:
            json.dump(self.canvas.profile_data, f, indent=2)
        keymapper.load_profile(p_path)
        QMessageBox.information(self, "Saved", f"Profile '{pname}' saved successfully!")

    def add_key_dialog(self):
        key_str, ok = QInputDialog.getText(self, "Add Key Binding", "Enter keyboard key (e.g. Space, E, Q, Shift, R, 1, 2):")
        if not ok or not key_str.strip():
            return
        desc, _ = QInputDialog.getText(self, "Key Label", "Enter action description (optional):")

        new_key = {
            "key": key_str.strip().lower(),
            "label": desc.strip() or key_str.strip().upper(),
            "x": 0.5,
            "y": 0.5,
            "radius": 0.035
        }
        self.canvas.profile_data.setdefault("keys", []).append(new_key)
        self.canvas.selected_item = len(self.canvas.profile_data["keys"]) - 1
        self.canvas.update()

    def remove_selected_key(self):
        if isinstance(self.canvas.selected_item, int):
            idx = self.canvas.selected_item
            if 0 <= idx < len(self.canvas.profile_data.get("keys", [])):
                del self.canvas.profile_data["keys"][idx]
                self.canvas.selected_item = None
                self.canvas.update()

    def toggle_dpad(self, checked):
        self.canvas.profile_data.setdefault("dpad", {})["enabled"] = checked
        self.canvas.update()

    def toggle_mouselook(self, checked):
        self.canvas.profile_data.setdefault("mouse_look", {})["enabled"] = checked

    def toggle_engine(self, checked):
        if checked:
            keymapper.start()
        else:
            keymapper.stop()
