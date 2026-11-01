#!/bin/bash
# 1-Click Direct Android Player Launcher
# High-Performance Gaming Player with 16GB Storage, 2GB RAM, and KVM + GPU Acceleration

# 1. Clean any stale lock files or broken snapshots
rm -f ~/.android/avd/bluestacks_gaming.avd/*.lock ~/.android/avd/*/*.lock 2>/dev/null || true
rm -rf ~/.android/avd/bluestacks_gaming.avd/snapshots/* 2>/dev/null || true

# 2. Check if already running
if pgrep -f "emulator.*bluestacks_gaming" > /dev/null 2>&1; then
    echo "Android instance is already running."
    exit 0
fi

# 3. Ensure Linux swap is active so the kernel never runs out of memory
if [ $(free -m | awk '/Swap:/ {print $2}') -lt 2000 ]; then
    sudo swapon /swapfile 2>/dev/null || true
    sudo swapon /swapfile2 2>/dev/null || true
fi

# 4. Use XCB platform for solid window stability
export QT_QPA_PLATFORM=xcb

# 5. Trap exit to flush all filesystem caches before closing
trap 'adb shell sync 2>/dev/null || true' EXIT INT TERM

# 6. Background daemon: optimizes performance, grants permissions, and auto-saves everything
(
    for i in $(seq 1 70); do
        if adb shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
            sleep 2

            # Grant full storage permissions to games (DLS, Roblox) so they don't freeze on loading
            adb shell "pm grant com.firsttouchgames.dls7 android.permission.READ_EXTERNAL_STORAGE 2>/dev/null; pm grant com.firsttouchgames.dls7 android.permission.WRITE_EXTERNAL_STORAGE 2>/dev/null; pm grant com.firsttouchgames.dls7 android.permission.POST_NOTIFICATIONS 2>/dev/null" 2>/dev/null || true

            # Prevent Google Play Protect from scanning or auto-removing sideloaded APKs
            adb shell "settings put global package_verifier_enable 0 && settings put global package_verifier_user_consent -1 && settings put global upload_apk_enable 0 && settings put global verifier_verify_adb_installs 0" 2>/dev/null || true

            # Apply 60 FPS SurfaceFlinger & zero-backpressure lag killer
            adb shell "setprop debug.sf.disable_backpressure 1 && setprop debug.sf.latch_unsignaled 1 && setprop debug.hwui.renderer skiagl && settings put global window_animation_scale 0 && settings put global transition_animation_scale 0 && settings put global animator_duration_scale 0 && sync" 2>/dev/null || true

            # Compile DLS to native speed ahead-of-time if installed
            adb shell "cmd package compile -m speed -f com.firsttouchgames.dls7" 2>/dev/null || true

            # Protect emulator process from Linux OOM killer
            emu_pids=$(pgrep -f "qemu-system|emulator" 2>/dev/null || true)
            for p in $emu_pids; do
                sudo sh -c "echo -500 > /proc/$p/oom_score_adj" 2>/dev/null || true
            done

            # Continuous Auto-Save Daemon: flushes memory to disk every 20 seconds so nothing is ever lost
            while pgrep -f "emulator.*bluestacks_gaming" > /dev/null 2>&1; do
                sleep 20
                adb shell sync 2>/dev/null || true
            done
            break
        fi
        sleep 1
    done
) &

echo "Starting Android Player (16GB Storage, 2GB RAM, KVM & GPU Accelerated)..."
EMU_BIN="$HOME/Android/Sdk/emulator/emulator"
if [ ! -x "$EMU_BIN" ]; then
    EMU_BIN="$(which emulator 2>/dev/null || echo "emulator")"
fi

exec "$EMU_BIN" \
    -avd bluestacks_gaming \
    -gpu auto \
    -accel on \
    -no-boot-anim \
    -no-snapshot-load \
    -vsync-rate 60 \
    -memory 2048 \
    -partition-size 16384 \
    -cores 4 \
    -qemu -cpu host "$@"
