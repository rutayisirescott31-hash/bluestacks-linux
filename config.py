"""
Configuration module for BlueStacks Linux.
Manages user preferences, paths, and instance defaults.
"""
import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/bluestacks-linux")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
PROFILES_DIR = os.path.join(CONFIG_DIR, "profiles")
SCREENSHOTS_DIR = os.path.expanduser("~/Pictures/BlueStacks")

DEFAULT_CONFIG = {
    "sdk_path": os.path.expanduser("~/Android/Sdk"),
    "emulator_path": os.path.expanduser("~/Android/Sdk/emulator/emulator"),
    "adb_path": "/usr/bin/adb",
    "screenshots_dir": SCREENSHOTS_DIR,
    "default_instance": "bluestacks_gaming",
    "default_ram": 3072,
    "default_cores": 4,
    "active_profile": "roblox",
    "gpu_mode": "host",
    "enable_kvm": True,
    "keymapper_enabled": True,
    "show_overlay": True,
    "overlay_opacity": 0.65,
    "window_mode": "normal",
    "dark_mode": True,
    "fps_target": 60
}

class ConfigManager:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(PROFILES_DIR, exist_ok=True)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        self.config = self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(data)
                    return cfg
            except Exception as e:
                print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

# Global config instance
config = ConfigManager()
