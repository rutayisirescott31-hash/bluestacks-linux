# BlueStacks Linux 🎮

> **High-Performance Android Gaming Player & Multi-Instance Manager for Linux (Ubuntu, Debian, Linux Mint, Pop!_OS, ChromeOS Crostini).**

[![Linux](https://img.shields.io/badge/OS-Linux-FCC624?logo=linux&logoColor=black)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt&logoColor=white)](https://riverbankcomputing.com)
[![KVM](https://img.shields.io/badge/Acceleration-KVM-red)](https://www.linux-kvm.org)
[![Android](https://img.shields.io/badge/Android-Gaming-3DDC84?logo=android&logoColor=white)](https://developer.android.com)

---

## ✨ Features

- 🚀 **KVM Hardware Acceleration**: Near-native CPU performance using Linux Kernel Virtual Machine (`/dev/kvm`).
- ⚡ **Direct GPU Rendering**: Seamless Vulkan and OpenGL ES acceleration with auto-fallback to host drivers.
- 💾 **16GB Dedicated Game Storage & 2GB RAM**: Optimized memory footprint to prevent out-of-memory crashes on systems with 4GB - 8GB RAM.
- 🛡️ **Anti-Crash Swap & OOM Shield**: Automatic swap guard and OOM killer score adjustment (`-500`) to guarantee the emulator never closes or drops during heavy games (DLS, Roblox, etc.).
- 🔄 **Continuous Auto-Save Daemon**: Background sync flushes Android filesystem cache every 20 seconds so game progress and settings are 100% permanently saved across reboots.
- ⌨️ **Integrated Gaming Keymapper**: Custom WASD movement, action hotkeys, and transparent in-game overlay powered by `pynput` and `evdev`.
- 📦 **1-Click APK Installation**:
  - Drag & drop any `.apk` file directly onto the BlueStacks window.
  - Double-click `.apk` files directly from your Linux file manager.
  - Drop APKs into `~/BlueStacks_APKs` for automatic detection and 1-click install.
- 👥 **Multi-Instance Manager**: Create, clone, customize, and run multiple Android environments simultaneously with presets (1280x720, 1600x900, 1080x1920).

---

## 📥 Installation on Ubuntu / Debian

### Option 1: 1-Line Quick Install

Clone the repository and run the turnkey installer:

```bash
git clone https://github.com/$(gh api user -q .login 2>/dev/null || echo "YOUR_USERNAME")/bluestacks-linux.git
cd bluestacks-linux
chmod +x install.sh
./install.sh
```

### Option 2: Step-by-Step Terminal Commands for Ubuntu

If you prefer installing manually step-by-step in your Ubuntu terminal:

```bash
# 1. Update and install required dependencies
sudo apt-get update -y
sudo apt-get install -y \
    python3 \
    python3-pyqt6 \
    python3-pynput \
    python3-evdev \
    python3-pil \
    adb \
    qemu-system-x86 \
    qemu-utils \
    cpu-checker \
    curl \
    unzip

# 2. Grant KVM hardware acceleration permissions to your user
sudo usermod -aG kvm $USER

# 3. Create a 6GB swapfile (vital to stop Linux kernel OOM crashes)
if [ $(free -m | awk '/Swap:/ {print $2}') -lt 4000 ]; then
    sudo fallocate -l 6G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=6144
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# 4. Clone and set up BlueStacks Linux
git clone https://github.com/$(gh api user -q .login 2>/dev/null || echo "YOUR_USERNAME")/bluestacks-linux.git ~/bluestacks-linux
cd ~/bluestacks-linux
chmod +x bluestacks run-android.sh

# 5. Link system commands
sudo ln -sf ~/bluestacks-linux/bluestacks /usr/local/bin/bluestacks
sudo ln -sf ~/bluestacks-linux/run-android.sh /usr/local/bin/run-android
```

---

## 🎮 How to Run

You can launch BlueStacks Linux in three ways:

1. **Application Launcher**: Search for **BlueStacks Linux** or **Run Android** in your Ubuntu Application Dash / App Menu.
2. **Terminal GUI**:
   ```bash
   bluestacks
   ```
3. **Direct 1-Click Game Player (High-FPS mode)**:
   ```bash
   run-android
   ```

---

## 📲 Installing Games & Apps (APKs)

- **Drag & Drop**: Simply drag any `.apk` file into the BlueStacks window.
- **Double Click**: Double click any `.apk` in your Ubuntu File Manager (Files / Nautilus).
- **APK Drop Folder**: Place APKs into:
  ```bash
  ~/BlueStacks_APKs/
  ```
- **CLI Command**:
  ```bash
  bluestacks /path/to/game.apk
  ```

---

## 🚀 Publishing Updates to GitHub

To publish this project to your GitHub account and keep it updated:

```bash
cd ~/bluestacks-linux

# Run the 1-click publishing script
./publish.sh "Your commit message"
```

The script will automatically:
1. Verify GitHub CLI (`gh`).
2. Log you in via web browser (`gh auth login`) if not already authenticated.
3. Create a public repository on your GitHub account (`bluestacks-linux`).
4. Push all source code, assets, and documentation.
5. On subsequent runs, it will stage your changes and push updates to `main`.

---

## ⚙️ System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **OS** | Ubuntu 22.04+, Debian 12+, Linux Mint 21+ | Ubuntu 24.04 LTS |
| **CPU** | 4-Core Intel Core / AMD Ryzen with VT-x/AMD-V | 6+ Cores |
| **RAM** | 4 GB | 8 GB+ (with 6GB Swap configured) |
| **Storage** | 25 GB free disk space | SSD / NVMe |
| **GPU** | Intel HD Graphics 500+ / AMD Radeon / NVIDIA | Dedicated GPU |

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
