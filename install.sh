#!/usr/bin/env bash
# ==============================================================================
# BlueStacks Linux - 1-Click Turnkey Installer for Ubuntu & Debian
# High-Performance Android Gaming Player with KVM & GPU Acceleration
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}       BlueStacks Linux - Turnkey Ubuntu/Debian Installer       ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Check Root / Sudo
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}[ERROR] Please do NOT run this installer directly as root.${NC}"
    echo -e "Run it as your normal user. The script will request sudo when required."
    exit 1
fi

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${BLUE}[1/7] Installing system packages and dependencies...${NC}"

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
    unzip \
    libpulse0 \
    libgl1-mesa-dri \
    libgl1-mesa-glx

# 2. Configure KVM Virtualization
echo -e "${BLUE}[2/7] Checking KVM Hardware Acceleration...${NC}"
if [ -e /dev/kvm ]; then
    echo -e "${GREEN}✓ Hardware KVM is available.${NC}"
    sudo usermod -aG kvm "$USER" || true
else
    echo -e "${YELLOW}! /dev/kvm not found. Ensure Virtualization (VT-x / AMD-V) is enabled in BIOS.${NC}"
fi

# 3. Memory & Anti-Crash Swapfile Protection
echo -e "${BLUE}[3/7] Setting up Anti-Crash Swap Protection (prevents OOM crashes)...${NC}"
TOTAL_SWAP_MB=$(free -m | awk '/Swap:/ {print $2}')
if [ "$TOTAL_SWAP_MB" -lt 4000 ]; then
    echo -e "${YELLOW}Swap is less than 4GB ($TOTAL_SWAP_MB MB). Setting up 6GB swapfile...${NC}"
    if [ ! -f /swapfile ]; then
        if sudo btrfs filesystem mkswapfile -s 6g /swapfile 2>/dev/null; then
            sudo chmod 600 /swapfile
            sudo swapon /swapfile
        else
            sudo fallocate -l 6G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=6144
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
        fi
        grep -q "/swapfile" /etc/fstab || echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
    fi
    echo -e "${GREEN}✓ 6GB swapfile active.${NC}"
else
    echo -e "${GREEN}✓ Adequate swap detected (${TOTAL_SWAP_MB} MB).${NC}"
fi

# Set optimal swappiness
sudo sysctl -w vm.swappiness=10 >/dev/null 2>&1 || true

# 4. Android SDK Setup
echo -e "${BLUE}[4/7] Checking Android SDK & System Images...${NC}"
ANDROID_SDK_ROOT="$HOME/Android/Sdk"
mkdir -p "$ANDROID_SDK_ROOT"

if [ ! -x "$ANDROID_SDK_ROOT/emulator/emulator" ]; then
    echo -e "${YELLOW}Android Emulator not found. Installing cmdline-tools & system image...${NC}"
    CMDLINE_DIR="$ANDROID_SDK_ROOT/cmdline-tools/latest"
    if [ ! -d "$CMDLINE_DIR" ]; then
        mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools"
        TMP_ZIP="/tmp/commandlinetools.zip"
        echo "Downloading Google Android SDK Tools..."
        curl -sSL "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" -o "$TMP_ZIP"
        unzip -q "$TMP_ZIP" -d "$ANDROID_SDK_ROOT/cmdline-tools"
        mv "$ANDROID_SDK_ROOT/cmdline-tools/cmdline-tools" "$CMDLINE_DIR"
        rm -f "$TMP_ZIP"
    fi

    export PATH="$CMDLINE_DIR/bin:$ANDROID_SDK_ROOT/emulator:$ANDROID_SDK_ROOT/platform-tools:$PATH"
    yes | "$CMDLINE_DIR/bin/sdkmanager" --licenses >/dev/null 2>&1 || true
    echo "Installing platform-tools, emulator, and Google Play x86_64 image..."
    "$CMDLINE_DIR/bin/sdkmanager" "platform-tools" "emulator" "system-images;android-34;google_apis_playstore;x86_64"
fi

# 5. Gaming AVD Configuration (16GB Storage, 2GB RAM, 4 vCPUs)
echo -e "${BLUE}[5/7] Configuring 'bluestacks_gaming' AVD instance...${NC}"
AVD_DIR="$HOME/.android/avd/bluestacks_gaming.avd"
mkdir -p "$HOME/.android/avd"

if [ ! -d "$AVD_DIR" ]; then
    echo "Creating BlueStacks Gaming AVD..."
    SYS_IMG=$(find "$ANDROID_SDK_ROOT/system-images" -type d -name "x86_64" 2>/dev/null | head -n 1)
    if [ -n "$SYS_IMG" ]; then
        REL_IMG=${SYS_IMG#$ANDROID_SDK_ROOT/}
        # Create AVD config manually for rock-solid reliability
        cat <<EOF > "$HOME/.android/avd/bluestacks_gaming.ini"
avd.ini.encoding=UTF-8
path=$AVD_DIR
path.rel=avd/bluestacks_gaming.avd
target=android
EOF
        mkdir -p "$AVD_DIR"
        cat <<EOF > "$AVD_DIR/config.ini"
AvdId=bluestacks_gaming
PlayStore.enabled=true
abi.type=x86_64
avd.ini.displayname=BlueStacks Gaming (1280x720)
avd.ini.encoding=UTF-8
disk.dataPartition.size=17179869184
fastboot.forceChosenSnapshotBoot=no
fastboot.forceColdBoot=yes
fastboot.forceFastBoot=no
hw.accelerometer=yes
hw.audioInput=yes
hw.audioOutput=yes
hw.battery=yes
hw.camera.back=virtualscene
hw.camera.front=emulated
hw.cpu.arch=x86_64
hw.cpu.ncore=4
hw.device.manufacturer=Google
hw.device.name=pixel_tablet
hw.gps=yes
hw.gpu.enabled=yes
hw.gpu.mode=auto
hw.initialOrientation=landscape
hw.keyboard=yes
hw.lcd.density=200
hw.lcd.height=720
hw.lcd.width=1280
hw.mainKeys=no
hw.ramSize=2048
hw.sdCard=yes
hw.sdCard.size=4096M
hw.sensors.orientation=yes
hw.sensors.proximity=no
image.sysdir.1=$REL_IMG/
skin.name=1280x720
tag.display=Google Play
tag.id=google_apis_playstore
vm.heapSize=384
EOF
        echo -e "${GREEN}✓ Created bluestacks_gaming AVD (16GB Storage, 2GB RAM).${NC}"
    fi
fi

# 6. Sideloading & Drop Folder Setup
echo -e "${BLUE}[6/7] Setting up APK drop folder and permissions...${NC}"
mkdir -p "$HOME/BlueStacks_APKs"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/applications"

# Symlink executable commands
sudo ln -sf "$INSTALL_DIR/bluestacks" /usr/local/bin/bluestacks || ln -sf "$INSTALL_DIR/bluestacks" "$HOME/.local/bin/bluestacks"
sudo ln -sf "$INSTALL_DIR/run-android.sh" /usr/local/bin/run-android || ln -sf "$INSTALL_DIR/run-android.sh" "$HOME/.local/bin/run-android"
chmod +x "$INSTALL_DIR/bluestacks" "$INSTALL_DIR/run-android.sh"

# Install custom icon
ICON_PATH="$INSTALL_DIR/assets/bluestacks_icon.png"
if [ ! -f "$ICON_PATH" ]; then
    mkdir -p "$INSTALL_DIR/assets"
    # Create fallback icon if missing
    python3 -c "
from PIL import Image, ImageDraw
im = Image.new('RGBA', (128, 128), (26, 35, 126, 255))
d = ImageDraw.Draw(im)
d.polygon([(64, 15), (110, 40), (110, 88), (64, 113), (18, 88), (18, 40)], fill=(0, 229, 255, 255))
im.save('$ICON_PATH')
" 2>/dev/null || true
fi

mkdir -p "$HOME/.local/share/icons/hicolor/128x128/apps"
cp -f "$ICON_PATH" "$HOME/.local/share/icons/hicolor/128x128/apps/bluestacks.png" 2>/dev/null || true

# 7. Desktop Entries & MIME Association
echo -e "${BLUE}[7/7] Registering desktop entries and 1-click APK installer...${NC}"

cat <<EOF > "$HOME/.local/share/applications/bluestacks.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=BlueStacks Linux
Comment=High-Performance Android Gaming Player for Linux
Exec=$INSTALL_DIR/bluestacks %F
Icon=bluestacks
Terminal=false
Categories=Game;Emulator;Utility;
MimeType=application/vnd.android.package-archive;
StartupNotify=true
StartupWMClass=bluestacks-linux
EOF

cat <<EOF > "$HOME/.local/share/applications/run-android.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Run Android (Direct 1-Click)
Comment=Launch Android Gaming Instance with 60 FPS & Auto-Save
Exec=$INSTALL_DIR/run-android.sh
Icon=bluestacks
Terminal=false
Categories=Game;Emulator;
StartupNotify=true
StartupWMClass=qemu-system-x86_64
EOF

# Update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  ✓ BlueStacks Linux Installation Complete!                    ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "You can launch BlueStacks Linux anytime using:"
echo -e "  1. Applications Menu -> Search '${BLUE}BlueStacks Linux${NC}' or '${BLUE}Run Android${NC}'"
echo -e "  2. Terminal command:   ${BLUE}bluestacks${NC} (GUI manager) or ${BLUE}run-android${NC} (direct game player)"
echo -e "  3. Drag & drop any .apk into the window or double-click any .apk file!"
echo -e "  4. Drop APKs into ${BLUE}~/BlueStacks_APKs${NC} for automatic 1-click installs."
echo -e "${GREEN}================================================================${NC}\n"
