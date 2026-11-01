"""
Sidebar Toolbar for BlueStacks Linux.
Provides the classic BlueStacks right-hand gaming toolbar with quick action buttons.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolTip,
                             QFileDialog, QMessageBox, QDialog, QTextEdit,
                             QHBoxLayout, QLabel, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

from backend.adb_client import adb
from backend.apk_installer import APKInstallWorker
from config import config

class SidebarWidget(QWidget):
    # Signals to parent window
    open_keymapper = pyqtSignal()
    open_settings = pyqtSignal()
    restart_instance = pyqtSignal()
    apk_installed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(56)
        self.setObjectName("SidebarFrame")
        self.setStyleSheet("""
            #SidebarFrame {
                background-color: #121822;
                border-left: 2px solid #20293A;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(6)

        # Action Buttons
        self.btn_fullscreen = self._add_button("⛶", "Full Screen (F11)", self.on_fullscreen)
        self.btn_boost = self._add_button("⚡", "1M FPS Boost (Turbo Speed)", self.on_fps_boost)
        self.btn_keymapper = self._add_button("🎮", "Game Controls (Keymapper)", self.open_keymapper.emit)
        self.btn_install_apk = self._add_button("📦", "Install APK from PC", self.on_install_apk)
        self.btn_screenshot = self._add_button("📸", "Take Screenshot", self.on_screenshot)
        self.btn_rotate = self._add_button("🔄", "Rotate Screen", self.on_rotate)
        self.btn_vol_up = self._add_button("🔊", "Volume Up", self.on_volume_up)
        self.btn_vol_down = self._add_button("🔉", "Volume Down", self.on_volume_down)
        self.btn_mute = self._add_button("🔇", "Mute Audio", self.on_mute)
        self.btn_shake = self._add_button("📳", "Shake Device", self.on_shake)
        self.btn_shell = self._add_button("💻", "ADB Console Shell", self.on_shell)
        self.btn_settings = self._add_button("⚙️", "Settings", self.open_settings.emit)

        layout.addStretch()

        self.btn_restart = self._add_button("🔄", "Restart Android Instance", self.restart_instance.emit)
        self.btn_restart.setStyleSheet("color: #EF4444;")

    def _add_button(self, icon_text: str, tooltip: str, slot) -> QPushButton:
        btn = QPushButton(icon_text)
        btn.setObjectName("SidebarButton")
        btn.setFixedSize(48, 44)
        btn.setFont(QFont("Segoe UI Emoji", 15))
        btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        self.layout().addWidget(btn)
        return btn

    def on_fullscreen(self):
        w = self.window()
        if w.isFullScreen():
            w.showNormal()
        else:
            w.showFullScreen()

    def on_install_apk(self):
        apk_path, _ = QFileDialog.getOpenFileName(
            self, "Select APK to Install",
            config.get("sdk_path", ""),
            "Android Package (*.apk);;All Files (*)"
        )
        if not apk_path:
            return

        self.btn_install_apk.setEnabled(False)
        self.btn_install_apk.setToolTip("Installing APK in background...")

        self.worker = APKInstallWorker(apk_path)
        def on_finished(success, msg):
            self.btn_install_apk.setEnabled(True)
            self.btn_install_apk.setToolTip("Install APK from PC")
            if success:
                QMessageBox.information(self, "APK Installed", f"Successfully installed:\n{os.path.basename(apk_path)}")
                self.apk_installed.emit()
            else:
                QMessageBox.warning(self, "Installation Failed", f"Could not install APK:\n{msg}")
        self.worker.finished.connect(on_finished)
        self.worker.start()

    def on_fps_boost(self):
        import threading
        self.btn_boost.setEnabled(False)
        def run_boost():
            success, msg = adb.apply_fps_boost()
            self.btn_boost.setEnabled(True)
            if success:
                QMessageBox.information(self, "⚡ 1M FPS Boost", msg)
            else:
                QMessageBox.warning(self, "Error", msg)
        threading.Thread(target=run_boost, daemon=True).start()

    def on_screenshot(self):
        import time, os
        ts = time.strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(config.get("screenshots_dir"), f"Screenshot_{ts}.png")
        success, res = adb.take_screenshot(dest)
        if success:
            QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved to:\n{dest}")
        else:
            QMessageBox.warning(self, "Screenshot Error", f"Failed to take screenshot:\n{res}")

    def on_rotate(self):
        adb.toggle_rotation()

    def on_volume_up(self):
        adb.keyevent(24)  # KEYCODE_VOLUME_UP

    def on_volume_down(self):
        adb.keyevent(25)  # KEYCODE_VOLUME_DOWN

    def on_mute(self):
        adb.keyevent(164)  # KEYCODE_VOLUME_MUTE

    def on_shake(self):
        adb.shake_device()

    def on_shell(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("BlueStacks - ADB Shell Console")
        dlg.resize(600, 400)
        vbox = QVBoxLayout(dlg)

        output = QTextEdit()
        output.setReadOnly(True)
        output.setStyleSheet("background-color: #0A0D14; font-family: monospace; font-size: 12px; color: #00E5FF;")
        output.append("Connected to Android ADB Shell.\nEnter commands below:\n")
        vbox.addWidget(output)

        hbox = QHBoxLayout()
        inp = QLineEdit()
        inp.setPlaceholderText("e.g. getprop ro.build.version.release, pm list packages, ls -l /sdcard")
        btn = QPushButton("Execute")
        btn.setObjectName("PrimaryButton")

        def run_cmd():
            cmd = inp.text().strip()
            if not cmd:
                return
            inp.clear()
            output.append(f"$ {cmd}")
            res = adb.shell_command(cmd)
            output.append(res.strip() + "\n")

        inp.returnPressed.connect(run_cmd)
        btn.clicked.connect(run_cmd)
        hbox.addWidget(inp)
        hbox.addWidget(btn)
        vbox.addLayout(hbox)

        dlg.exec()
