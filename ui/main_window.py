"""
Main Window for BlueStacks Linux.
Combines Header, Game Center, Multi-Instance Manager, Keymapping Canvas, and BlueStacks Gaming Toolbar.
"""
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QComboBox,
                             QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QShortcut, QPixmap

from ui.theme import STYLESHEET
from ui.sidebar_widget import SidebarWidget
from ui.games_view import GamesView
from ui.instance_view import InstanceView
from ui.keymapper_editor import KeymapperEditorView
from ui.keymapper_overlay import KeymapperOverlay
from ui.script_helper_view import ScriptHelperView
from ui.settings_view import SettingsView

from backend.instance_manager import instance_mgr
from backend.emulator_process import emulator
from backend.adb_client import adb
from backend.keymapper_engine import keymapper
from config import config

class MainWindow(QMainWindow):
    state_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BlueStacks for Linux - Android App Player")
        self.resize(1180, 720)
        self.setMinimumSize(960, 580)
        self.setStyleSheet(STYLESHEET)
        self.setAcceptDrops(True)

        # Set window icon
        icon_path = os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps/bluestacks-linux.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Overlay window
        self.overlay = KeymapperOverlay()

        # Connect signals
        self.state_signal.connect(self.update_state_ui)
        emulator.on_state_change = lambda s: self.state_signal.emit(s)

        # Central Layout
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Header Bar
        header = self._create_header()
        root_layout.addWidget(header)

        # 2. Main Body (Tabs + Sidebar)
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Tabs
        self.tabs = QTabWidget()
        self.view_games = GamesView()
        self.view_games.request_start_emulator.connect(self.toggle_emulator_state)
        self.view_instances = InstanceView()
        self.view_instances.instance_started.connect(self.on_instance_started)
        self.view_keymapper = KeymapperEditorView()
        self.view_scripts = ScriptHelperView()
        self.view_settings = SettingsView()

        self.tabs.addTab(self.view_games, "🎮 Game Center")
        self.tabs.addTab(self.view_instances, "⚡ Multi-Instance")
        self.tabs.addTab(self.view_keymapper, "🎯 Game Controls")
        self.tabs.addTab(self.view_scripts, "📜 Roblox & Scripts")
        self.tabs.addTab(self.view_settings, "⚙️ Settings")

        body_layout.addWidget(self.tabs, 1)

        # BlueStacks Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.open_keymapper.connect(lambda: self.tabs.setCurrentIndex(2))
        self.sidebar.open_settings.connect(lambda: self.tabs.setCurrentIndex(4))
        self.sidebar.restart_instance.connect(self.restart_current_instance)
        self.sidebar.apk_installed.connect(self.view_games.refresh_apps)
        body_layout.addWidget(self.sidebar)

        root_layout.addWidget(body, 1)

        # Shortcuts
        self.sc_f11 = QShortcut(QKeySequence("F11"), self)
        self.sc_f11.activated.connect(self.sidebar.on_fullscreen)

        self.sc_f10 = QShortcut(QKeySequence("F10"), self)
        self.sc_f10.activated.connect(self.toggle_overlay)

        # Status polling timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_emulator_status)
        self.status_timer.start(2500)

        self._opt_applied = False

        # Initial refresh
        self.refresh_instances_dropdown()

    def _create_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("HeaderFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(16)

        # App Logo & Titles
        logo_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("🔷")
            logo_label.setFont(QFont("Segoe UI Emoji", 22))

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("BlueStacks App Player")
        lbl_title.setObjectName("TitleLabel")
        lbl_sub = QLabel("Linux Edition • Hardware Accelerated (KVM & Vulkan)")
        lbl_sub.setObjectName("SubtitleLabel")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)

        layout.addWidget(logo_label)
        layout.addLayout(title_box)
        layout.addSpacing(20)

        # Instance Selector Dropdown
        layout.addWidget(QLabel("Active Instance:"))
        self.combo_instance = QComboBox()
        self.combo_instance.setMinimumWidth(180)
        self.combo_instance.currentIndexChanged.connect(self.on_active_instance_changed)
        layout.addWidget(self.combo_instance)

        # Status badge
        self.badge_status = QLabel("Stopped")
        self.badge_status.setObjectName("StatusBadge")
        self.badge_status.setProperty("status", "Stopped")
        layout.addWidget(self.badge_status)

        layout.addStretch()

        # Start / Stop Action Button
        self.btn_power = QPushButton("▶ Launch Android")
        self.btn_power.setObjectName("PrimaryButton")
        self.btn_power.setFixedWidth(150)
        self.btn_power.clicked.connect(self.toggle_emulator_state)
        layout.addWidget(self.btn_power)

        # 1M FPS Boost Button
        self.btn_fps_boost = QPushButton("⚡ 1M FPS Boost")
        self.btn_fps_boost.setObjectName("FpsBoostButton")
        self.btn_fps_boost.setStyleSheet("""
            QPushButton#FpsBoostButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF9100, stop:1 #FFD600);
                color: #000000;
                font-weight: 800;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton#FpsBoostButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFEE58);
            }
        """)
        self.btn_fps_boost.setToolTip("Instant lag killer: Downscales render, AOT compiles Roblox, kills background bloat")
        self.btn_fps_boost.clicked.connect(self.trigger_fps_boost)
        layout.addWidget(self.btn_fps_boost)

        # HUD Overlay Toggle Button
        self.btn_overlay = QPushButton("👁️ HUD (F10)")
        self.btn_overlay.setToolTip("Toggle on-screen keybinding overlay")
        self.btn_overlay.clicked.connect(self.toggle_overlay)
        layout.addWidget(self.btn_overlay)

        return frame

    def refresh_instances_dropdown(self):
        self.combo_instance.blockSignals(True)
        self.combo_instance.clear()
        insts = instance_mgr.list_instances()
        default_inst = config.get("default_instance", "bluestacks_gaming")

        selected_idx = 0
        for idx, inst in enumerate(insts):
            self.combo_instance.addItem(f"{inst['display_name']} ({inst['resolution']})", inst['id'])
            if inst['id'] == default_inst:
                selected_idx = idx

        if insts:
            self.combo_instance.setCurrentIndex(selected_idx)
        self.combo_instance.blockSignals(False)

    def on_active_instance_changed(self):
        avd_id = self.combo_instance.currentData()
        if avd_id:
            config.set("default_instance", avd_id)
            self.check_emulator_status()

    def on_instance_started(self, avd_id: str):
        self.refresh_instances_dropdown()
        self.update_state_ui("BOOTING")

    def toggle_emulator_state(self):
        avd_id = self.combo_instance.currentData() or "bluestacks_gaming"
        if emulator.is_running(avd_id):
            emulator.stop(avd_id)
            self.update_state_ui("STOPPED")
        else:
            insts = instance_mgr.list_instances()
            target = [i for i in insts if i['id'] == avd_id]
            ram = target[0]['ram_mb'] if target else 3072
            cores = target[0]['cores'] if target else 4

            success = emulator.start(avd_id, gpu_mode=config.get("gpu_mode", "host"), ram_mb=ram, cores=cores)
            if success:
                self.update_state_ui("BOOTING")
                # Start keymapper engine
                if config.get("keymapper_enabled", True):
                    keymapper.start()

    def restart_current_instance(self):
        avd_id = self.combo_instance.currentData() or "bluestacks_gaming"
        adb.sync_data()
        emulator.stop(avd_id)
        QTimer.singleShot(1500, self.toggle_emulator_state)

    def check_emulator_status(self):
        avd_id = self.combo_instance.currentData()
        running = emulator.is_running(avd_id)
        if running:
            booted = adb.is_boot_completed()
            if booted:
                state = "Running"
                if not self._opt_applied:
                    self._opt_applied = True
                    # Automatically apply 60 FPS SurfaceFlinger & touch optimizations
                    adb.apply_gaming_optimizations()
            else:
                state = "Booting"
        else:
            state = "Stopped"
            self._opt_applied = False
        self.update_state_ui(state)

    def update_state_ui(self, state: str):
        self.badge_status.setText(state)
        self.badge_status.setProperty("status", state)
        self.badge_status.style().polish(self.badge_status)

        if state == "Running":
            self.btn_power.setText("⏹ Stop Android")
            self.btn_power.setObjectName("DangerButton")
            self.btn_power.setStyleSheet("")
            self.btn_power.style().polish(self.btn_power)
        elif state == "Booting":
            self.btn_power.setText("⏳ Booting...")
            self.btn_power.setObjectName("PrimaryButton")
            self.btn_power.style().polish(self.btn_power)
        else:
            self.btn_power.setText("▶ Launch Android")
            self.btn_power.setObjectName("PrimaryButton")
            self.btn_power.setStyleSheet("")
            self.btn_power.style().polish(self.btn_power)

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def trigger_fps_boost(self):
        if not adb.is_boot_completed():
            QMessageBox.information(self, "Instance Offline", "Start an instance first to apply 1M FPS Boost!")
            return
        self.btn_fps_boost.setEnabled(False)
        self.btn_fps_boost.setText("⚡ Boosting...")
        def run_boost():
            success, msg = adb.apply_fps_boost()
            self.btn_fps_boost.setEnabled(True)
            self.btn_fps_boost.setText("⚡ 1M FPS Boost")
            if success:
                QMessageBox.information(self, "⚡ 1M FPS Boost Active", msg)
            else:
                QMessageBox.warning(self, "Boost Error", msg)
        import threading
        threading.Thread(target=run_boost, daemon=True).start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".apk"):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                apk_path = url.toLocalFile()
                if apk_path.lower().endswith(".apk") and os.path.exists(apk_path):
                    event.acceptProposedAction()
                    self.install_apk_file(apk_path)
                    return
        super().dropEvent(event)

    def install_apk_file(self, apk_path: str):
        if not os.path.exists(apk_path):
            QMessageBox.warning(self, "APK Not Found", f"Cannot find APK file: {apk_path}")
            return
        self.tabs.setCurrentIndex(0)
        self.view_games.install_external_apk(apk_path)
