"""
Instance Manager for BlueStacks Linux.
Handles creation, listing, cloning, deletion, and configuration of Android AVD instances.
"""
import os
import shutil
import subprocess
from typing import List, Dict, Any, Optional

AVD_DIR = os.path.expanduser("~/.android/avd")

PRESETS = {
    "gaming_1600": {
        "name": "BlueStacks Gaming Tablet (1600x900)",
        "width": 1600,
        "height": 900,
        "density": 240,
        "ram": 3584,
        "cores": 6,
        "orientation": "landscape",
        "skin": "1600x900"
    },
    "gaming_720": {
        "name": "BlueStacks Fast HD (1280x720)",
        "width": 1280,
        "height": 720,
        "density": 213,
        "ram": 3072,
        "cores": 6,
        "orientation": "landscape",
        "skin": "1280x720"
    },
    "gaming_1080": {
        "name": "BlueStacks Full HD (1920x1080)",
        "width": 1920,
        "height": 1080,
        "density": 280,
        "ram": 4096,
        "cores": 6,
        "orientation": "landscape",
        "skin": "1920x1080"
    },
    "phone": {
        "name": "BlueStacks Smartphone (1080x1920)",
        "width": 1080,
        "height": 1920,
        "density": 320,
        "ram": 3584,
        "cores": 6,
        "orientation": "portrait",
        "skin": "1080x1920"
    }
}

class InstanceManager:
    def __init__(self, avd_dir: str = AVD_DIR):
        self.avd_dir = avd_dir
        os.makedirs(self.avd_dir, exist_ok=True)

    def _parse_ini(self, path: str) -> Dict[str, str]:
        data = {}
        if not os.path.exists(path):
            return data
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip()
        return data

    def _write_ini(self, path: str, data: Dict[str, str]):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for k, v in data.items():
                f.write(f"{k}={v}\n")

    def list_instances(self) -> List[Dict[str, Any]]:
        instances = []
        if not os.path.exists(self.avd_dir):
            return instances

        running_names = self.get_running_instances()

        for fname in os.listdir(self.avd_dir):
            if fname.endswith(".ini"):
                avd_id = fname[:-4]
                ini_path = os.path.join(self.avd_dir, fname)
                ini_data = self._parse_ini(ini_path)
                avd_folder = ini_data.get("path", os.path.join(self.avd_dir, f"{avd_id}.avd"))
                config_path = os.path.join(avd_folder, "config.ini")
                config_data = self._parse_ini(config_path)

                w = config_data.get("hw.lcd.width", "1600")
                h = config_data.get("hw.lcd.height", "900")
                display_name = config_data.get("avd.ini.displayname", avd_id.replace("_", " ").title())
                ram = config_data.get("hw.ramSize", "3072")
                cores = config_data.get("hw.cpu.ncore", "4")
                density = config_data.get("hw.lcd.density", "240")
                target = ini_data.get("target", "Android")

                is_running = (avd_id in running_names)

                instances.append({
                    "id": avd_id,
                    "display_name": display_name,
                    "resolution": f"{w}x{h}",
                    "width": int(w) if w.isdigit() else 1600,
                    "height": int(h) if h.isdigit() else 900,
                    "density": int(density) if density.isdigit() else 240,
                    "ram_mb": int(ram) if ram.isdigit() else 3072,
                    "cores": int(cores) if cores.isdigit() else 4,
                    "target": target,
                    "status": "Running" if is_running else "Stopped",
                    "path": avd_folder
                })
        return instances

    def get_running_instances(self) -> List[str]:
        running = []
        try:
            out = subprocess.check_output(["pgrep", "-a", "qemu-system|emulator"], text=True)
            for line in out.splitlines():
                if "-avd" in line:
                    parts = line.split("-avd")
                    if len(parts) > 1:
                        avd_name = parts[1].strip().split()[0]
                        running.append(avd_name)
        except Exception:
            pass
        return running

    def create_instance(self, avd_id: str, display_name: str, preset_key: str = "gaming_1600",
                        system_image_dir: str = "system-images/android-37.0/google_apis_playstore/x86_64/") -> bool:
        preset = PRESETS.get(preset_key, PRESETS["gaming_1600"])
        ini_file = os.path.join(self.avd_dir, f"{avd_id}.ini")
        avd_folder = os.path.join(self.avd_dir, f"{avd_id}.avd")
        os.makedirs(avd_folder, exist_ok=True)

        # Write root .ini
        root_data = {
            "avd.ini.encoding": "UTF-8",
            "path": avd_folder,
            "path.rel": f"avd/{avd_id}.avd",
            "target": "android-37.0"
        }
        self._write_ini(ini_file, root_data)

        # Write config.ini
        config_data = {
            "AvdId": avd_id,
            "PlayStore.enabled": "true",
            "abi.type": "x86_64",
            "avd.ini.displayname": display_name,
            "avd.ini.encoding": "UTF-8",
            "disk.dataPartition.size": "12884901888",
            "fastboot.forceColdBoot": "no",
            "fastboot.forceFastBoot": "yes",
            "fastboot.forceChosenSnapshotBoot": "no",
            "fastboot.chosenSnapshotFile": "",
            "hw.accelerometer": "yes",
            "hw.audioInput": "yes",
            "hw.audioOutput": "yes",
            "hw.battery": "yes",
            "hw.camera.back": "virtualscene",
            "hw.camera.front": "emulated",
            "hw.cpu.arch": "x86_64",
            "hw.cpu.ncore": str(preset["cores"]),
            "hw.device.manufacturer": "Google",
            "hw.device.name": "pixel_tablet" if preset["orientation"] == "landscape" else "pixel_7",
            "hw.gps": "yes",
            "hw.gpu.enabled": "yes",
            "hw.gpu.mode": "host",
            "hw.initialOrientation": preset["orientation"],
            "hw.keyboard": "yes",
            "hw.lcd.density": str(preset["density"]),
            "hw.lcd.height": str(preset["height"]),
            "hw.lcd.width": str(preset["width"]),
            "hw.mainKeys": "no",
            "hw.ramSize": str(preset["ram"]),
            "hw.sdCard": "yes",
            "hw.sensors.orientation": "yes",
            "hw.sensors.proximity": "no",
            "image.sysdir.1": system_image_dir,
            "skin.name": preset["skin"],
            "tag.display": "Google Play",
            "tag.id": "google_apis_playstore",
            "vm.heapSize": "512"
        }
        self._write_ini(os.path.join(avd_folder, "config.ini"), config_data)
        return True

    def clone_instance(self, src_id: str, new_id: str, new_display_name: str) -> bool:
        src_folder = os.path.join(self.avd_dir, f"{src_id}.avd")
        if not os.path.exists(src_folder):
            return False

        dst_folder = os.path.join(self.avd_dir, f"{new_id}.avd")
        # Copy directory excluding lock files
        shutil.copytree(src_folder, dst_folder, ignore=shutil.ignore_patterns("*.lock", "tmpAdbCmds"))

        # Write new .ini
        ini_file = os.path.join(self.avd_dir, f"{new_id}.ini")
        self._write_ini(ini_file, {
            "avd.ini.encoding": "UTF-8",
            "path": dst_folder,
            "path.rel": f"avd/{new_id}.avd",
            "target": "android-37.0"
        })

        # Update config.ini
        cfg_path = os.path.join(dst_folder, "config.ini")
        cfg_data = self._parse_ini(cfg_path)
        cfg_data["AvdId"] = new_id
        cfg_data["avd.ini.displayname"] = new_display_name
        self._write_ini(cfg_path, cfg_data)
        return True

    def delete_instance(self, avd_id: str) -> bool:
        ini_file = os.path.join(self.avd_dir, f"{avd_id}.ini")
        folder = os.path.join(self.avd_dir, f"{avd_id}.avd")
        try:
            if os.path.exists(ini_file):
                os.remove(ini_file)
            if os.path.exists(folder):
                shutil.rmtree(folder)
            return True
        except Exception as e:
            print(f"Error deleting instance {avd_id}: {e}")
            return False

    def update_instance_specs(self, avd_id: str, ram_mb: int, cores: int, width: int, height: int, density: int) -> bool:
        folder = os.path.join(self.avd_dir, f"{avd_id}.avd")
        cfg_path = os.path.join(folder, "config.ini")
        if not os.path.exists(cfg_path):
            return False
        cfg = self._parse_ini(cfg_path)
        cfg["hw.ramSize"] = str(ram_mb)
        cfg["hw.cpu.ncore"] = str(cores)
        cfg["hw.lcd.width"] = str(width)
        cfg["hw.lcd.height"] = str(height)
        cfg["hw.lcd.density"] = str(density)
        cfg["skin.name"] = f"{width}x{height}"
        self._write_ini(cfg_path, cfg)
        return True

instance_mgr = InstanceManager()
