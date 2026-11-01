"""
Settings View for BlueStacks Linux.
Configuration for graphics acceleration, virtualization, memory allocation, and paths.
"""
import os
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel,
                             QComboBox, QSpinBox, QSlider, QLineEdit,
                             QPushButton, QHBoxLayout, QMessageBox, QGroupBox,
                             QFileDialog)
from PyQt6.QtCore import Qt

from config import config

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("BlueStacks Settings & Performance")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        # Performance Group
        perf_group = QGroupBox("Performance & Hardware Acceleration")
        perf_form = QFormLayout(perf_group)

        self.combo_gpu = QComboBox()
        self.combo_gpu.addItem("Host GPU (Vulkan Venus / Virgl - Fast 60FPS)", "host")
        self.combo_gpu.addItem("Auto-Detect GPU", "auto")
        self.combo_gpu.addItem("Software (SwiftShader)", "swiftshader")
        gpu_curr = config.get("gpu_mode", "host")
        idx = self.combo_gpu.findData(gpu_curr)
        if idx >= 0:
            self.combo_gpu.setCurrentIndex(idx)

        # KVM status check
        kvm_ok = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)
        lbl_kvm = QLabel("✅ KVM Hardware Virtualization Available" if kvm_ok else "⚠️ KVM not accessible")
        lbl_kvm.setStyleSheet("color: #00E676; font-weight: 600;" if kvm_ok else "color: #FFAA00;")

        self.spin_ram = QSpinBox()
        self.spin_ram.setRange(1024, 8192)
        self.spin_ram.setSingleStep(512)
        self.spin_ram.setSuffix(" MB")
        self.spin_ram.setValue(config.get("default_ram", 3584))

        self.spin_cores = QSpinBox()
        self.spin_cores.setRange(1, 8)
        self.spin_cores.setSuffix(" vCPUs")
        self.spin_cores.setValue(config.get("default_cores", 6))

        perf_form.addRow("Hardware Virtualization:", lbl_kvm)
        perf_form.addRow("GPU Renderer Backend:", self.combo_gpu)
        perf_form.addRow("Allocated RAM:", self.spin_ram)
        perf_form.addRow("CPU Cores:", self.spin_cores)
        layout.addWidget(perf_group)

        # Overlay & Display Group
        display_group = QGroupBox("Gaming Controls & HUD Overlay")
        disp_form = QFormLayout(display_group)

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(20, 100)
        self.slider_opacity.setValue(int(config.get("overlay_opacity", 0.70) * 100))

        disp_form.addRow("HUD Overlay Transparency:", self.slider_opacity)
        layout.addWidget(display_group)

        # Paths Group
        paths_group = QGroupBox("File Locations & SDK Paths")
        paths_form = QFormLayout(paths_group)

        self.input_sdk = QLineEdit(config.get("sdk_path", ""))
        self.input_screens = QLineEdit(config.get("screenshots_dir", ""))

        paths_form.addRow("Android SDK Path:", self.input_sdk)
        paths_form.addRow("Screenshots Folder:", self.input_screens)
        layout.addWidget(paths_group)

        layout.addStretch()

        # Save Button
        bottom_bar = QHBoxLayout()
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setFixedWidth(140)
        btn_save.clicked.connect(self.save_settings)
        bottom_bar.addStretch()
        bottom_bar.addWidget(btn_save)
        layout.addLayout(bottom_bar)

    def save_settings(self):
        config.set("gpu_mode", self.combo_gpu.currentData())
        config.set("default_ram", self.spin_ram.value())
        config.set("default_cores", self.spin_cores.value())
        config.set("overlay_opacity", self.slider_opacity.value() / 100.0)
        config.set("sdk_path", self.input_sdk.text().strip())
        config.set("screenshots_dir", self.input_screens.text().strip())
        QMessageBox.information(self, "Saved", "Settings saved successfully!")
