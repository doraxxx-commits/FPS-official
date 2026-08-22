#!/bin/bash
cd /workspaces/Fps-offline/FPS/android

export ANDROID_HOME=/tmp/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# Doinstalowanie platform wymaganych przez Gradle (33 i 34) oraz build-tools
sdkmanager "platforms;android-33" "platforms;android-34" "build-tools;30.0.3" "build-tools;34.0.0" > /dev/null 2>&1

# Zaakceptowanie wszystkich licencji Android SDK
yes | sdkmanager --licenses > /dev/null 2>&1

# Zapisanie właściwości i uruchomienie budowania APK
echo "sdk.dir=/tmp/android-sdk" > local.properties
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew assembleDebug
#!/bin/bash
cd /workspaces/Fps-offline/FPS/android

export ANDROID_HOME=/tmp/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# 1. Wymuszenie zaakceptowania wszystkich licencji SDK
mkdir -p "$ANDROID_HOME/licenses"
printf "24833b2982d56e430fc57fc17928070b4f312817\n89330d22264220b8773a4783d6510960e43d9392\ne67a22780775d5706997427d96aec36496165e43\nf15441125c408d98fc00f88a0a826b51a06e1580\nd56f5187479451eabf01fb78af6dfcb131a6481e\n24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_HOME/licenses/android-sdk-license"

# 2. Akceptacja automatyczna przez strumień
yes | sdkmanager --licenses

# 3. Pobranie wymaganych wersji build-tools i platform
sdkmanager "build-tools;30.0.3" "build-tools;34.0.0" "platforms;android-33" "platforms;android-34"

# 4. Uruchomienie budowania APK
echo "sdk.dir=/tmp/android-sdk" > local.properties
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew assembleDebug
