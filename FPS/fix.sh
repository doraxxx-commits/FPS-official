#!/bin/bash
set -e

echo "🚀 [1/5] Instalacja Java 17 i narzędzi systemowych..."
sudo apt-get update -y > /dev/null 2>&1
sudo apt-get install -y openjdk-17-jdk unzip wget > /dev/null 2>&1

# Ustalenie katalogu roboczego
WORK_DIR=$(pwd)

# Automatyczna obsługa rozpakowywania aktualnego pliku archiwum
if [ ! -d "$WORK_DIR/FPS" ]; then
    if [ -f "$WORK_DIR/FPS naprawione.zip" ]; then
        echo "📦 Rozpakowywanie archiwum FPS naprawione.zip..."
        unzip -o "$WORK_DIR/FPS naprawione.zip" > /dev/null 2>&1
    elif [ -f "$WORK_DIR/FPS-fixed.zip" ]; then
        echo "📦 Rozpakowywanie archiwum FPS-fixed.zip..."
        unzip -o "$WORK_DIR/FPS-fixed.zip" > /dev/null 2>&1
    elif [ -f "$WORK_DIR/FPS.zip" ]; then
        echo "📦 Rozpakowywanie archiwum FPS.zip..."
        unzip -o "$WORK_DIR/FPS.zip" > /dev/null 2>&1
    fi
fi

if [ -d "$WORK_DIR/FPS" ]; then
    cd "$WORK_DIR/FPS"
fi

PROJECT_DIR=$(pwd)

echo "📦 [2/5] Instalacja pakietów NPM i synchronizacja Capacitor..."
npm install --silent
if [ ! -d "$PROJECT_DIR/android" ]; then
    npx cap add android
fi
npm run cap:build

echo "🛠️ [3/5] Pobieranie i konfiguracja Android SDK..."
export ANDROID_HOME=/tmp/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

if [ ! -d "$ANDROID_HOME/cmdline-tools" ]; then
    mkdir -p /tmp/android-sdk/cmdline-tools
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O /tmp/cmdline-tools.zip
    unzip -q /tmp/cmdline-tools.zip -d /tmp/android-sdk/cmdline-tools
    mv /tmp/android-sdk/cmdline-tools/cmdline-tools /tmp/android-sdk/cmdline-tools/latest
fi

echo "🔑 [4/5] Automatyczna akceptacja licencji Android SDK..."
mkdir -p "$ANDROID_HOME/licenses"
printf "24833b2982d56e430fc57fc17928070b4f312817\n89330d22264220b8773a4783d6510960e43d9392\ne67a22780775d5706997427d96aec36496165e43\nf15441125c408d98fc00f88a0a826b51a06e1580\nd56f5187479451eabf01fb78af6dfcb131a6481e\n24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_HOME/licenses/android-sdk-license"
yes | sdkmanager --licenses > /dev/null 2>&1 || true
sdkmanager "build-tools;30.0.3" "build-tools;34.0.0" "platforms;android-33" "platforms;android-34" > /dev/null 2>&1

echo "🏗️ [5/5] Kompilacja APK..."
cd "$PROJECT_DIR/android"
echo "sdk.dir=/tmp/android-sdk" > local.properties
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew assembleDebug

echo ""
echo "🎉 ZROBIONE! Twój plik APK znajduje się w:"
echo "$PROJECT_DIR/android/app/build/outputs/apk/debug/app-debug.apk"
