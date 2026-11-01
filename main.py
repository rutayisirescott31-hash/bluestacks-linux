#!/usr/bin/env python3
"""
BlueStacks for Linux - Main Entry Point.
High-performance Android Gaming App Player for Linux.
"""
import sys
import os

# Enforce X11 / XCB backend to prevent Wayland Sommelier sub-surface crashes on ChromeOS/Linux
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# Add directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from backend.keymapper_engine import keymapper

def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BlueStacks Linux")
    app.setApplicationDisplayName("BlueStacks for Linux")

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    # Automatically install APK if passed via command line, file manager, or double click
    apk_to_install = None
    for arg in sys.argv[1:]:
        if arg.lower().endswith(".apk") and os.path.exists(arg):
            apk_to_install = os.path.abspath(arg)
            break
        elif arg == "install" and len(sys.argv) > 2:
            candidate = sys.argv[sys.argv.index("install") + 1]
            if os.path.exists(candidate):
                apk_to_install = os.path.abspath(candidate)
                break

    if apk_to_install:
        window.install_apk_file(apk_to_install)

    ret = app.exec()

    # Clean shutdown
    try:
        keymapper.stop()
    except Exception:
        pass

    sys.exit(ret)

if __name__ == "__main__":
    main()
