"""
Keymapper Engine for BlueStacks Linux.
Translates PC keyboard & mouse events into fast Android multi-touch inputs and virtual joystick gestures.
"""
import os
import json
import time
import math
import queue
import threading
from typing import Dict, Any, Optional
from pynput import keyboard, mouse
from backend.adb_client import adb

class KeymapperEngine:
    def __init__(self):
        self.profile: Dict[str, Any] = {}
        self.profile_name: str = "default"
        self.enabled: bool = False
        self.running: bool = False

        # Input tracking
        self.active_keys = set()
        self.dpad_keys = set()
        self.is_dpad_active = False

        # Screen dimensions
        self.screen_width = 1600
        self.screen_height = 900

        # Queue for async ADB execution
        self.input_queue = queue.Queue(maxsize=100)
        self._worker_thread: Optional[threading.Thread] = None

        # Pynput listener
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None

        # Mouse aim mode
        self.mouse_aim_active = False
        self.last_mouse_pos = (0, 0)

    def load_profile(self, profile_path_or_name: str) -> bool:
        if not os.path.exists(profile_path_or_name):
            # Check ~/.config/bluestacks-linux/profiles/
            cfg_p = os.path.expanduser(f"~/.config/bluestacks-linux/profiles/{profile_path_or_name}.json")
            if os.path.exists(cfg_p):
                profile_path_or_name = cfg_p
            else:
                return False

        try:
            with open(profile_path_or_name, "r") as f:
                self.profile = json.load(f)
                self.profile_name = self.profile.get("name", "Custom")
                return True
        except Exception as e:
            print(f"Failed to load keymap profile: {e}")
            return False

    def start(self, serial: Optional[str] = None):
        if self.running:
            return

        # Fetch screen size
        try:
            w, h = adb.get_screen_size(serial)
            if w > 0 and h > 0:
                self.screen_width = w
                self.screen_height = h
        except Exception:
            pass

        self.running = True
        self.enabled = True

        # Start input worker thread
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        # Start keyboard listener
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.start()

    def stop(self):
        self.running = False
        self.enabled = False
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

    def _normalize_key(self, key) -> str:
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        if hasattr(key, 'name') and key.name:
            return key.name.lower()
        return str(key).replace("Key.", "").lower()

    def _on_key_press(self, key):
        if not self.enabled or not self.profile:
            return

        k = self._normalize_key(key)
        if k in self.active_keys:
            return  # Ignore repeat
        self.active_keys.add(k)

        # Check toggle for mouse look
        mouse_cfg = self.profile.get("mouse_look", {})
        if mouse_cfg.get("enabled") and k == mouse_cfg.get("toggle_key", "f1").lower():
            self.mouse_aim_active = not self.mouse_aim_active
            return

        # Check D-Pad
        dpad = self.profile.get("dpad", {})
        if dpad.get("enabled"):
            up = dpad.get("up_key", "w").lower()
            down = dpad.get("down_key", "s").lower()
            left = dpad.get("left_key", "a").lower()
            right = dpad.get("right_key", "d").lower()

            if k in (up, down, left, right):
                self.dpad_keys.add(k)
                self._dispatch_dpad(up, down, left, right, dpad)
                return

        # Check Action Keys
        for key_item in self.profile.get("keys", []):
            if key_item.get("key", "").lower() == k:
                # Convert normalized x, y to screen pixels
                px = int(key_item.get("x", 0.5) * self.screen_width)
                py = int(key_item.get("y", 0.5) * self.screen_height)
                self._queue_tap(px, py)
                break

    def _on_key_release(self, key):
        if not self.enabled:
            return

        k = self._normalize_key(key)
        self.active_keys.discard(k)

        dpad = self.profile.get("dpad", {})
        if dpad.get("enabled"):
            up = dpad.get("up_key", "w").lower()
            down = dpad.get("down_key", "s").lower()
            left = dpad.get("left_key", "a").lower()
            right = dpad.get("right_key", "d").lower()

            if k in (up, down, left, right):
                self.dpad_keys.discard(k)
                if self.dpad_keys:
                    self._dispatch_dpad(up, down, left, right, dpad)
                else:
                    self.is_dpad_active = False

    def _dispatch_dpad(self, up, down, left, right, dpad):
        cx = int(dpad.get("center_x", 0.16) * self.screen_width)
        cy = int(dpad.get("center_y", 0.76) * self.screen_height)
        radius = int(dpad.get("radius", 0.08) * min(self.screen_width, self.screen_height))

        dx = 0
        dy = 0
        if up in self.dpad_keys:
            dy -= 1
        if down in self.dpad_keys:
            dy += 1
        if left in self.dpad_keys:
            dx -= 1
        if right in self.dpad_keys:
            dx += 1

        if dx == 0 and dy == 0:
            return

        # Normalize diagonal
        mag = math.hypot(dx, dy)
        tx = int(cx + (dx / mag) * radius)
        ty = int(cy + (dy / mag) * radius)

        # Queue swipe from center to target direction
        self._queue_swipe(cx, cy, tx, ty, duration_ms=120)

    def _queue_tap(self, x: int, y: int):
        try:
            self.input_queue.put_nowait(("tap", x, y))
        except queue.Full:
            pass

    def _queue_swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 100):
        # Clear stale movement swipes to ensure instant responsiveness without input lag
        try:
            with self.input_queue.mutex:
                self.input_queue.queue.clear()
        except Exception:
            pass
        try:
            self.input_queue.put_nowait(("swipe", x1, y1, x2, y2, duration_ms))
        except queue.Full:
            pass

    def _worker_loop(self):
        while self.running:
            try:
                task = self.input_queue.get(timeout=0.2)
                action = task[0]
                if action == "tap":
                    _, x, y = task
                    adb.tap(x, y)
                elif action == "swipe":
                    _, x1, y1, x2, y2, dur = task
                    adb.swipe(x1, y1, x2, y2, duration_ms=dur)
                self.input_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in keymapper worker: {e}")

keymapper = KeymapperEngine()
