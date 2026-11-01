"""
Game Center and Installed Apps View for BlueStacks Linux.
Shows installed games/apps with quick launch, native zero-lag launchers, APK drop, and game store integration.
"""
import os
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QGridLayout, QFrame,
                             QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap

from backend.adb_client import adb
from backend.emulator_process import emulator
from backend.apk_installer import APKInstallWorker
from config import config

class GameCard(QFrame):
    launched = pyqtSignal(str)

    def __init__(self, name: str, package: str, is_system: bool = False, is_native: bool = False, parent=None):
        super().__init__(parent)
        self.package = package
        self.is_native = is_native
        self.setObjectName("GameCard")
        self.setFixedSize(190, 215)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Icon placeholder / graphic
        icon_box = QLabel()
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedHeight(65)

        # Custom emoji or icon based on app
        icon_symbol = "🎮"
        if is_native or "roblox" in package.lower():
            icon_symbol = "🧱"
        elif "vending" in package.lower():
            icon_symbol = "🛒"
        elif "settings" in package.lower():
            icon_symbol = "⚙️"
        elif "chrome" in package.lower():
            icon_symbol = "🌐"

        icon_box.setText(icon_symbol)
        icon_box.setFont(QFont("Segoe UI Emoji", 36))
        layout.addWidget(icon_box)

        # Native tag
        if is_native:
            badge = QLabel("⚡ NATIVE ZERO-LAG")
            badge.setStyleSheet("color: #00E676; font-size: 10px; font-weight: 800; background: rgba(0, 230, 118, 0.15); border-radius: 4px; padding: 2px 4px;")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(badge)

        # Title
        title = QLabel(name)
        title.setObjectName("CardTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        layout.addStretch()

        # Play Button
        if is_native:
            btn = QPushButton("PLAY 120 FPS")
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E676, stop:1 #00E5FF);
                    color: #000000;
                    font-weight: 800;
                    border: none;
                    border-radius: 6px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #69F0AE, stop:1 #18FFFF);
                }
            """)
        else:
            btn = QPushButton("PLAY NOW" if not is_system else "OPEN")
            btn.setObjectName("PrimaryButton")

        btn.clicked.connect(lambda: self.launched.emit(self.package))
        layout.addWidget(btn)

class GamesView(QWidget):
    request_start_emulator = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Top Control Bar
        top_bar = QHBoxLayout()

        search_label = QLabel("🔍")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search installed games and apps...")
        self.search_input.textChanged.connect(self.filter_apps)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_apps)

        self.btn_folder = QPushButton("📁 APK Folder")
        self.btn_folder.setToolTip("Open ~/BlueStacks_APKs to drop APK files directly")
        self.btn_folder.clicked.connect(self.open_apk_folder)

        self.btn_install = QPushButton("➕ Install APK")
        self.btn_install.setObjectName("PrimaryButton")
        self.btn_install.clicked.connect(self.install_apk_dialog)

        top_bar.addWidget(search_label)
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_folder)
        top_bar.addWidget(self.btn_install)
        main_layout.addLayout(top_bar)

        # Drag and drop hint / detected APK banner
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E293B, stop:1 #0F172A);
                border: 1px solid #0080FF;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        banner_layout = QHBoxLayout(self.banner_frame)
        self.banner_text = QLabel("💡 <b>Drag & Drop any APK</b> onto this window or put it in <code>~/BlueStacks_APKs</code> to install!")
        self.banner_btn = QPushButton("Open Folder")
        self.banner_btn.setObjectName("PrimaryButton")
        self.banner_btn.clicked.connect(self.open_apk_folder)
        banner_layout.addWidget(self.banner_text, 1)
        banner_layout.addWidget(self.banner_btn)
        main_layout.addWidget(self.banner_frame)

        self.check_downloads_for_apk()

        # Scrollable Game Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll, 1)

        self.all_apps = []
        self.refresh_apps()

    def open_apk_folder(self):
        apk_dir = os.path.expanduser("~/BlueStacks_APKs")
        os.makedirs(apk_dir, exist_ok=True)
        subprocess.Popen(["xdg-open", apk_dir])

    def check_downloads_for_apk(self):
        downloads_dir = os.path.expanduser("~/Downloads")
        ser_apk = os.path.join(downloads_dir, "ser.apk")
        if os.path.exists(ser_apk):
            self.banner_apk_path = ser_apk
            self.banner_text.setText("💡 <b>Roblox APK detected in Downloads!</b> Click to install into BlueStacks instantly.")
            self.banner_btn.setText("Install Roblox APK")
            self.banner_btn.clicked.disconnect()
            self.banner_btn.clicked.connect(self.install_detected_apk)
            self.banner_frame.show()
        else:
            self.banner_frame.show()

    def install_detected_apk(self):
        if hasattr(self, 'banner_apk_path') and os.path.exists(self.banner_apk_path):
            self.install_external_apk(self.banner_apk_path)

    def install_external_apk(self, apk_path: str):
        if not os.path.exists(apk_path):
            return

        fname = os.path.basename(apk_path)
        self.banner_text.setText(f"📦 <b>Installing {fname}...</b> (Please wait)")
        self.banner_btn.setEnabled(False)
        self.banner_btn.setText("⏳ Installing...")
        self.banner_frame.show()

        self.worker = APKInstallWorker(apk_path)
        self.worker.progress.connect(lambda txt: self.banner_btn.setText(f"⏳ {txt}"))
        def on_finished(success, msg):
            self.banner_btn.setEnabled(True)
            if success:
                self.banner_text.setText(f"✅ <b>{fname} installed successfully into BlueStacks!</b>")
                self.banner_btn.setText("Refresh")
                self.refresh_apps()
            else:
                self.banner_text.setText(f"⚠️ Failed to install {fname}")
                self.banner_btn.setText("Retry")
                QMessageBox.warning(self, "Installation Error", f"Install failed: {msg}")
        self.worker.finished.connect(on_finished)
        self.worker.start()

    def install_apk_dialog(self):
        apk_path, _ = QFileDialog.getOpenFileName(
            self, "Select APK to Install",
            os.path.expanduser("~/BlueStacks_APKs"),
            "Android Package (*.apk);;All Files (*)"
        )
        if apk_path:
            self.install_external_apk(apk_path)

    def refresh_apps(self):
        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        self.all_apps = []

        # Check for Native Sober (Zero-lag Roblox)
        sober_path = os.path.expanduser("~/.local/share/flatpak/app/org.vinegarhq.Sober")
        if os.path.exists(sober_path) or os.path.exists("/var/lib/flatpak/app/org.vinegarhq.Sober"):
            self.all_apps.append({
                "package": "org.vinegarhq.Sober",
                "name": "Roblox (Native Linux 120 FPS)",
                "is_system": False,
                "is_native": True
            })

        # Get installed apps from emulator
        installed = adb.list_installed_apps()
        if installed:
            self.all_apps.extend(installed)
        else:
            # Suggestions if emulator offline
            self.all_apps.extend([
                {"package": "com.roblox.client", "name": "Roblox (Android Mobile)", "is_system": False, "is_native": False},
                {"package": "com.android.vending", "name": "Google Play Store", "is_system": True, "is_native": False},
                {"package": "com.android.settings", "name": "System Settings", "is_system": True, "is_native": False},
                {"package": "com.android.chrome", "name": "Chrome Browser", "is_system": True, "is_native": False}
            ])

        self.render_apps(self.all_apps)

    def render_apps(self, apps):
        # Clear layout items
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        cols = 4
        for idx, app in enumerate(apps):
            card = GameCard(app["name"], app["package"], app.get("is_system", False), app.get("is_native", False))
            card.launched.connect(self.launch_game)
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)

    def filter_apps(self, query: str):
        q = query.strip().lower()
        if not q:
            self.render_apps(self.all_apps)
        else:
            filtered = [a for a in self.all_apps if q in a["name"].lower() or q in a["package"].lower()]
            self.render_apps(filtered)

    def launch_game(self, package: str):
        if package == "org.vinegarhq.Sober":
            # Launch native zero-lag Roblox
            subprocess.Popen(["flatpak", "run", "org.vinegarhq.Sober"])
            return

        if not adb.is_boot_completed():
            QMessageBox.information(self, "Starting Android", "Starting instance to play game...")
            self.request_start_emulator.emit()
            return
        success, msg = adb.launch_app(package)
        if not success:
            QMessageBox.warning(self, "Launch Error", f"Could not launch {package}:\n{msg}")
