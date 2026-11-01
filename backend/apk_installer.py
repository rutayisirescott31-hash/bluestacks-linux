"""
Asynchronous APK Installer Worker for BlueStacks Linux.
Installs APKs in a background thread to prevent UI freezing and handles auto-starting the Android instance.
"""
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal

from backend.adb_client import adb
from backend.emulator_process import emulator
from backend.instance_manager import instance_mgr
from config import config

class APKInstallWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, apk_path: str, avd_id: str = None, parent=None):
        super().__init__(parent)
        self.apk_path = apk_path
        self.avd_id = avd_id or config.get("default_instance", "bluestacks_gaming")

    def run(self):
        if not os.path.exists(self.apk_path):
            self.finished.emit(False, f"APK file not found: {self.apk_path}")
            return

        # 1. Start instance if offline
        if not emulator.is_running(self.avd_id):
            self.progress.emit("Starting Android instance...")
            insts = instance_mgr.list_instances()
            target = [i for i in insts if i['id'] == self.avd_id]
            ram = target[0]['ram_mb'] if target else 3072
            cores = target[0]['cores'] if target else 4

            started = emulator.start(
                self.avd_id,
                gpu_mode=config.get("gpu_mode", "host"),
                ram_mb=ram,
                cores=cores
            )
            if not started:
                self.finished.emit(False, f"Failed to start instance '{self.avd_id}'")
                return

        # 2. Wait for Android boot
        self.progress.emit("Waiting for Android to complete boot...")
        booted = False
        for i in range(75):
            if adb.is_boot_completed():
                booted = True
                break
            time.sleep(1)
            if i % 5 == 0 and i > 0:
                self.progress.emit(f"Waiting for Android to boot ({i}s)...")

        if not booted:
            self.finished.emit(False, "Timed out waiting for Android instance to finish booting.")
            return

        # 3. Perform APK installation
        apk_name = os.path.basename(self.apk_path)
        self.progress.emit(f"Installing {apk_name}...")
        success, msg = adb.install_apk(self.apk_path)
        if success:
            # Sync filesystem to guarantee the APK is permanently saved to userdata
            adb.sync_data()
        self.finished.emit(success, msg)
