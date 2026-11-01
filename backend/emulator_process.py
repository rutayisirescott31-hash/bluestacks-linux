"""
Emulator Process Manager for BlueStacks Linux.
Handles starting, stopping, monitoring, and passing gaming optimization flags to the Android emulator.
"""
import os
import subprocess
import threading
import time
from typing import Optional, Callable

class EmulatorProcess:
    def __init__(self, emulator_bin: str = os.path.expanduser("~/Android/Sdk/emulator/emulator")):
        self.emulator_bin = emulator_bin if os.path.exists(emulator_bin) else "emulator"
        self.process: Optional[subprocess.Popen] = None
        self.current_avd: Optional[str] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_requested = False

        self.on_state_change: Optional[Callable[[str], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None

    def is_running(self, avd_name: Optional[str] = None) -> bool:
        if self.process and self.process.poll() is None:
            return True
        try:
            out = subprocess.check_output(["pgrep", "-a", "qemu-system|emulator"], text=True)
            if avd_name:
                return f"-avd {avd_name}" in out or f"@{avd_name}" in out
            return len(out.strip()) > 0
        except Exception:
            return False

    def _cleanup_stale_locks(self, avd_name: str):
        """Cleans up stale QEMU/Android lock files from previous runs to guarantee it opens every time."""
        import glob
        avd_folder = os.path.expanduser(f"~/.android/avd/{avd_name}.avd")
        if os.path.exists(avd_folder):
            for lock_f in glob.glob(os.path.join(avd_folder, "*.lock")):
                try:
                    os.remove(lock_f)
                except Exception:
                    pass

    def start(self, avd_name: str, gpu_mode: str = "host", ram_mb: int = 3072, cores: int = 4,
              headless: bool = False) -> bool:
        if self.is_running(avd_name):
            if self.on_state_change:
                self.on_state_change("RUNNING")
            return True

        # Always purge stale lock files before starting
        self._cleanup_stale_locks(avd_name)

        cmd = [
            self.emulator_bin,
            "-avd", avd_name,
            "-gpu", gpu_mode,
            "-accel", "on",
            "-no-boot-anim",
            "-no-snapshot-load",
            "-vsync-rate", "60",
            "-memory", str(ram_mb),
            "-partition-size", "20480",
            "-cores", str(cores)
        ]

        if headless:
            cmd.append("-no-window")

        # Pass native host CPU instruction sets (AVX2, SSE4.2, FMA) for ultra smooth gaming
        cmd.extend(["-qemu", "-cpu", "host"])

        if self.on_state_change:
            self.on_state_change("BOOTING")

        if self.on_log:
            self.on_log(f"Starting emulator: {' '.join(cmd)}")

        self._stop_requested = False
        self.current_avd = avd_name

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as e:
            if self.on_log:
                self.on_log(f"Failed to start emulator: {e}")
            if self.on_state_change:
                self.on_state_change("STOPPED")
            return False

        # Monitor thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        return True

    def _monitor_loop(self):
        # Read log lines
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                line_str = line.strip()
                if self.on_log and line_str:
                    self.on_log(line_str)
            else:
                time.sleep(0.05)

        ret = self.process.poll() if self.process else -1
        if self.on_log:
            self.on_log(f"Emulator exited with code: {ret}")
        if self.on_state_change:
            self.on_state_change("STOPPED")
        self.process = None

    def stop(self, avd_name: Optional[str] = None):
        target_avd = avd_name or self.current_avd
        self._stop_requested = True

        if self.on_state_change:
            self.on_state_change("STOPPING")

        # Flush Android filesystem cache and database transactions to disk to guarantee data persistence
        try:
            subprocess.run(["adb", "shell", "sync"], capture_output=True, timeout=6)
        except Exception:
            pass

        # Graceful stop via adb emu kill
        try:
            subprocess.run(["adb", "emu", "kill"], capture_output=True, timeout=8)
        except Exception:
            pass

        # If process still alive, terminate
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        # Force kill any lingering qemu for this avd
        try:
            subprocess.run(["killall", "-9", "qemu-system-x86_64"], capture_output=True, timeout=3)
        except Exception:
            pass

        if self.on_state_change:
            self.on_state_change("STOPPED")

emulator = EmulatorProcess()
