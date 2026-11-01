"""
Roblox & Luau Scripting Tools View for BlueStacks Linux.
Enables quick management of Luau scripts, executing scripts via cordial-luau, and pushing scripts/APKs to Android.
"""
import os
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QTextEdit, QMessageBox,
                             QFileDialog, QFrame, QSplitter)
from PyQt6.QtCore import Qt

from backend.adb_client import adb

class ScriptHelperView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        title = QLabel("Roblox & Script Tools")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")

        self.btn_refresh = QPushButton("🔄 Refresh Scripts")
        self.btn_refresh.clicked.connect(self.scan_scripts)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_refresh)
        layout.addLayout(top_bar)

        desc = QLabel("⚡ Manage and test Luau scripts, push configurations to Android games, and run local Luau executions.")
        desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc)

        # Splitter for Scripts List & Script Editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Available Scripts (in ~/Applications):"))
        self.script_list = QListWidget()
        self.script_list.itemClicked.connect(self.on_script_selected)
        left_layout.addWidget(self.script_list)

        btn_box = QHBoxLayout()
        self.btn_push = QPushButton("📲 Push to Android")
        self.btn_push.clicked.connect(self.push_selected_script)

        self.btn_run_cordial = QPushButton("▶ Run Luau")
        self.btn_run_cordial.setObjectName("PrimaryButton")
        self.btn_run_cordial.clicked.connect(self.run_luau_local)

        btn_box.addWidget(self.btn_push)
        btn_box.addWidget(self.btn_run_cordial)
        left_layout.addLayout(btn_box)

        splitter.addWidget(left_widget)

        # Right editor & output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("Script Content / Terminal Output:"))
        self.editor = QTextEdit()
        self.editor.setStyleSheet("font-family: monospace; font-size: 12px; background-color: #0A0D14;")
        right_layout.addWidget(self.editor)

        btn_save = QPushButton("💾 Save Script Changes")
        btn_save.clicked.connect(self.save_script_content)
        right_layout.addWidget(btn_save)

        splitter.addWidget(right_widget)
        splitter.setSizes([260, 540])

        layout.addWidget(splitter, 1)

        self.current_script_path = None
        self.scan_scripts()

    def scan_scripts(self):
        self.script_list.clear()
        search_dirs = [os.path.expanduser("~/Applications"), os.path.expanduser("~/Downloads")]
        for sdir in search_dirs:
            if os.path.exists(sdir):
                for f in os.listdir(sdir):
                    if f.endswith(".lua") or f.endswith(".luau"):
                        full_p = os.path.join(sdir, f)
                        self.script_list.addItem(full_p)

    def on_script_selected(self, item):
        path = item.text()
        self.current_script_path = path
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.editor.setPlainText(f.read())
        except Exception as e:
            self.editor.setPlainText(f"Error opening script: {e}")

    def save_script_content(self):
        if not self.current_script_path:
            return
        try:
            with open(self.current_script_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            QMessageBox.information(self, "Saved", "Script saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save script: {e}")

    def push_selected_script(self):
        if not self.current_script_path:
            QMessageBox.warning(self, "No Selection", "Please select a script from the list.")
            return

        fname = os.path.basename(self.current_script_path)
        dest = f"/sdcard/Download/{fname}"
        res = adb.shell_command(f"mkdir -p /sdcard/Download")

        # Run adb push
        p = subprocess.run(["adb", "push", self.current_script_path, dest], capture_output=True, text=True)
        if p.returncode == 0:
            QMessageBox.information(self, "Pushed", f"Successfully pushed script to Android:\n{dest}")
        else:
            QMessageBox.warning(self, "Push Failed", f"Failed to push script:\n{p.stderr or p.stdout}")

    def run_luau_local(self):
        if not self.current_script_path:
            return
        cordial_bin = os.path.expanduser("~/Downloads/cordial-luau-executor/build/cordial-luau")
        if not os.path.exists(cordial_bin):
            QMessageBox.warning(self, "Executor Not Found", f"Cordial Luau binary not found at:\n{cordial_bin}")
            return

        try:
            cmd = [cordial_bin, "run", self.current_script_path, "--context", "client", "--timeout", "30"]
            self.editor.append(f"\n--- Running: {' '.join(cmd)} ---\n")
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            self.editor.append(res.stdout)
            if res.stderr:
                self.editor.append(f"Errors:\n{res.stderr}")
        except Exception as e:
            self.editor.append(f"\nExecution error: {e}")
