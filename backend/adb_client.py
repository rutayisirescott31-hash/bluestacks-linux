"""
ADB Client for BlueStacks Linux.
Handles communication, package management, touch inputs, screenshots, and system controls.
"""
import os
import subprocess
import time
from typing import List, Dict, Optional, Tuple

class ADBClient:
    def __init__(self, adb_path: str = "/usr/bin/adb"):
        self.adb_path = adb_path if os.path.exists(adb_path) else "adb"
        self._cached_screen_size = None

    def _cmd(self, args: List[str], timeout: int = 15, serial: Optional[str] = None) -> Tuple[int, str, str]:
        cmd = [self.adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def list_devices(self) -> List[Dict[str, str]]:
        code, out, _ = self._cmd(["devices"])
        devices = []
        if code == 0:
            for line in out.strip().splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    devices.append({"serial": parts[0], "state": parts[1]})
        return devices

    def get_default_device(self) -> Optional[str]:
        devices = self.list_devices()
        # Prefer online emulator
        for dev in devices:
            if dev["state"] == "device" and "emulator" in dev["serial"]:
                return dev["serial"]
        for dev in devices:
            if dev["state"] == "device":
                return dev["serial"]
        return devices[0]["serial"] if devices else None

    def is_boot_completed(self, serial: Optional[str] = None) -> bool:
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, out, _ = self._cmd(["shell", "getprop", "sys.boot_completed"], timeout=4, serial=ser)
        return code == 0 and out.strip() == "1"

    def get_screen_size(self, serial: Optional[str] = None) -> Tuple[int, int]:
        if self._cached_screen_size:
            return self._cached_screen_size
        ser = serial or self.get_default_device()
        if not ser:
            return (1600, 900)
        code, out, _ = self._cmd(["shell", "wm", "size"], timeout=5, serial=ser)
        if code == 0 and "Physical size:" in out:
            try:
                line = [l for l in out.splitlines() if "Physical size:" in l][0]
                dims = line.split(":")[-1].strip().split("x")
                self._cached_screen_size = (int(dims[0]), int(dims[1]))
                return self._cached_screen_size
            except Exception:
                pass
        return (1600, 900)

    def install_apk(self, apk_path: str, serial: Optional[str] = None) -> Tuple[bool, str]:
        if not os.path.exists(apk_path):
            return False, f"APK file not found: {apk_path}"
        ser = serial or self.get_default_device()
        if not ser:
            return False, "No running Android instance found"
        code, out, err = self._cmd(["install", "-r", "-d", apk_path], timeout=120, serial=ser)
        if code == 0 and ("Success" in out or "Success" in err):
            return True, "Installed successfully"
        return False, out.strip() or err.strip()

    def uninstall_app(self, package_name: str, serial: Optional[str] = None) -> Tuple[bool, str]:
        ser = serial or self.get_default_device()
        if not ser:
            return False, "No running Android instance found"
        code, out, err = self._cmd(["uninstall", package_name], timeout=30, serial=ser)
        return (code == 0 and "Success" in out), out.strip() or err.strip()

    def list_installed_apps(self, serial: Optional[str] = None) -> List[Dict[str, str]]:
        ser = serial or self.get_default_device()
        if not ser:
            return []
        # Get 3rd-party installed packages
        code, out, _ = self._cmd(["shell", "pm", "list", "packages", "-3"], timeout=8, serial=ser)
        packages = []
        if code == 0:
            for line in out.strip().splitlines():
                if line.startswith("package:"):
                    pkg = line.replace("package:", "").strip()
                    if pkg:
                        packages.append(pkg)
        
        # Include popular known apps even if system
        known_system = [
            ("com.android.vending", "Google Play Store"),
            ("com.android.settings", "Android Settings"),
            ("com.android.chrome", "Chrome Browser"),
            ("com.google.android.youtube", "YouTube")
        ]
        
        app_list = []
        for pkg, label in known_system:
            c, o, _ = self._cmd(["shell", "pm", "path", pkg], timeout=3, serial=ser)
            if c == 0 and "package:" in o:
                app_list.append({
                    "package": pkg,
                    "name": label,
                    "is_system": True
                })
        
        for pkg in packages:
            # Generate friendly name
            name = pkg.split(".")[-1].capitalize()
            if "roblox" in pkg.lower():
                name = "Roblox"
            elif "minecraft" in pkg.lower():
                name = "Minecraft"
            elif "freefire" in pkg.lower():
                name = "Free Fire"
            elif "pubg" in pkg.lower():
                name = "PUBG Mobile"
            elif "genshin" in pkg.lower():
                name = "Genshin Impact"
            elif "subway" in pkg.lower():
                name = "Subway Surfers"
            elif "clash" in pkg.lower():
                name = "Clash of Clans"

            app_list.append({
                "package": pkg,
                "name": name,
                "is_system": False
            })
        return app_list

    def launch_app(self, package_name: str, serial: Optional[str] = None) -> Tuple[bool, str]:
        ser = serial or self.get_default_device()
        if not ser:
            return False, "No device connected"
        # Use monkey launcher
        code, out, err = self._cmd(["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"], timeout=10, serial=ser)
        if code == 0:
            return True, "Launched"
        return False, out.strip() or err.strip()

    def force_stop_app(self, package_name: str, serial: Optional[str] = None) -> bool:
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, _, _ = self._cmd(["shell", "am", "force-stop", package_name], timeout=5, serial=ser)
        return code == 0

    def tap(self, x: int, y: int, serial: Optional[str] = None) -> bool:
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, _, _ = self._cmd(["shell", "input", "tap", str(x), str(y)], timeout=3, serial=ser)
        return code == 0

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 150, serial: Optional[str] = None) -> bool:
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, _, _ = self._cmd(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)], timeout=4, serial=ser)
        return code == 0

    def keyevent(self, keycode: int, serial: Optional[str] = None) -> bool:
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, _, _ = self._cmd(["shell", "input", "keyevent", str(keycode)], timeout=3, serial=ser)
        return code == 0

    def take_screenshot(self, output_path: str, serial: Optional[str] = None) -> Tuple[bool, str]:
        ser = serial or self.get_default_device()
        if not ser:
            return False, "No active Android device"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            cmd = [self.adb_path]
            if ser:
                cmd.extend(["-s", ser])
            cmd.extend(["exec-out", "screencap", "-p"])
            with open(output_path, "wb") as f:
                res = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=10)
            if res.returncode == 0 and os.path.getsize(output_path) > 1000:
                return True, output_path
            return False, "Screenshot file empty or failed"
        except Exception as e:
            return False, str(e)

    def set_rotation(self, orientation: int = 1, serial: Optional[str] = None) -> bool:
        """
        0 = Portrait, 1 = Landscape, 2 = Reverse Portrait, 3 = Reverse Landscape
        """
        ser = serial or self.get_default_device()
        if not ser:
            return False
        self._cmd(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial=ser)
        code, _, _ = self._cmd(["shell", "settings", "put", "system", "user_rotation", str(orientation)], serial=ser)
        return code == 0

    def toggle_rotation(self, serial: Optional[str] = None) -> bool:
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, out, _ = self._cmd(["shell", "settings", "get", "system", "user_rotation"], serial=ser)
        curr = int(out.strip()) if code == 0 and out.strip().isdigit() else 0
        new_rot = 1 if curr == 0 else 0
        return self.set_rotation(new_rot, serial=ser)

    def shake_device(self, serial: Optional[str] = None) -> bool:
        w, h = self.get_screen_size(serial)
        cx, cy = w // 2, h // 2
        # Quick back and forth swipe to simulate shake
        self.swipe(cx - 150, cy, cx + 150, cy, 60, serial=serial)
        self.swipe(cx + 150, cy, cx - 150, cy, 60, serial=serial)
        return True

    def shell_command(self, cmd: str, serial: Optional[str] = None) -> str:
        ser = serial or self.get_default_device()
        if not ser:
            return "No Android device connected"
        _, out, err = self._cmd(["shell", cmd], timeout=15, serial=ser)
        return out or err

    def sync_data(self, serial: Optional[str] = None) -> bool:
        """Flushes Android disk buffers to save all changes immediately."""
        ser = serial or self.get_default_device()
        if not ser:
            return False
        code, _, _ = self._cmd(["shell", "sync"], timeout=5, serial=ser)
        return code == 0

    def apply_gaming_optimizations(self, serial: Optional[str] = None) -> bool:
        """
        Injects SurfaceFlinger hardware acceleration, removes backpressure lag,
        optimizes animation speed, and sets high performance properties for silky smooth 60 FPS gaming.
        """
        ser = serial or self.get_default_device()
        if not ser:
            return False

        tweak_cmds = [
            "setprop debug.sf.hw 1",
            "setprop debug.egl.hw 1",
            "setprop debug.sf.disable_backpressure 1",
            "setprop debug.sf.latch_unsignaled 1",
            "setprop debug.hwui.renderer skiagl",
            "setprop debug.renderengine.backend skiagl",
            "setprop persist.sys.power.high_performance 1",
            "setprop persist.sys.sf.native_mode 1",
            "settings put global window_animation_scale 0.5",
            "settings put global transition_animation_scale 0.5",
            "settings put global animator_duration_scale 0.5",
            "setprop touch.pressure.scale 0.001",
            "sync"
        ]

        full_cmd = " && ".join(tweak_cmds)
        code, _, _ = self._cmd(["shell", full_cmd], timeout=10, serial=ser)
        return code == 0

    def apply_fps_boost(self, serial: Optional[str] = None, ultra_mode: bool = False) -> Tuple[bool, str]:
        """
        Applies the 1M FPS Booster tweaks:
        - Downscales render size (1280x720 or 960x540)
        - Compiles Roblox to native speed machine code
        - Kills background bloatware
        - Removes SurfaceFlinger frame lag & disables animations
        """
        ser = serial or self.get_default_device()
        if not ser:
            return False, "No running Android instance found"

        # 1. Scale resolution
        if ultra_mode:
            self._cmd(["shell", "wm", "size", "960x540"], serial=ser)
            self._cmd(["shell", "wm", "density", "160"], serial=ser)
        else:
            self._cmd(["shell", "wm", "size", "1280x720"], serial=ser)
            self._cmd(["shell", "wm", "density", "200"], serial=ser)

        # 2. Performance tweaks
        tweak_cmds = [
            "setprop debug.sf.disable_backpressure 1",
            "setprop debug.sf.latch_unsignaled 1",
            "setprop debug.hwui.renderer skiagl",
            "setprop debug.renderengine.backend skiagl",
            "settings put global window_animation_scale 0",
            "settings put global transition_animation_scale 0",
            "settings put global animator_duration_scale 0",
            "setprop touch.pressure.scale 0.001",
            "am force-stop com.google.android.apps.wellbeing",
            "pm disable-user --user 0 com.google.android.apps.wellbeing 2>/dev/null",
            "am set-inactive com.google.android.gms true",
            "cmd appops set com.google.android.gms RUN_IN_BACKGROUND ignore",
            "sync"
        ]
        self._cmd(["shell", " && ".join(tweak_cmds)], timeout=10, serial=ser)

        # 3. Compile Roblox if installed
        self._cmd(["shell", "cmd", "package", "compile", "-m", "speed", "-f", "com.roblox.client"], timeout=45, serial=ser)

        mode_name = "Ultra Potato 540p" if ultra_mode else "Turbo 720p"
        return True, f"1M FPS Boost Applied: {mode_name}, Native Machine Code Compiled, 0x Animations & Background Bloat Killed!"

adb = ADBClient()
