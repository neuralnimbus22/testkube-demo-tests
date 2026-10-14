#!/bin/sh
# Record facts about the emulator and the installed app, for the mobile report.
# Usage: record-device.sh <device address> <apk url>
set -e
DEVICE="$1"
APK_URL="$2"
OUT=/data/reports/device.env
FLOWS=/data/repo/mobile/maestro

prop() { adb -s "$DEVICE" shell getprop "$1" | tr -d '\r'; }

# The app id is the appId line at the top of the Maestro flows.
APP_ID=$(grep -h '^appId:' "$FLOWS"/*.yaml | head -1 | awk '{print $2}')
APP_VERSION=$(adb -s "$DEVICE" shell dumpsys package "$APP_ID" | tr -d '\r' | grep -m1 'versionName=' | cut -d= -f2)

mkdir -p /data/reports
cat > "$OUT" <<FACTS
address=$DEVICE
manufacturer=$(prop ro.product.manufacturer)
model=$(prop ro.product.model)
android=$(prop ro.build.version.release)
sdk=$(prop ro.build.version.sdk)
abi=$(prop ro.product.cpu.abi)
screen=$(adb -s "$DEVICE" shell wm size | tr -d '\r' | awk '{print $NF}')
density=$(adb -s "$DEVICE" shell wm density | tr -d '\r' | awk '{print $NF}')
app_id=$APP_ID
app_version=$APP_VERSION
apk_url=$APK_URL
FACTS
cat "$OUT"
