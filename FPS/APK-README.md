# FPS-Pro — wersja przygotowana pod APK

Projekt został przygotowany do opakowania istniejącego frontendu HTML/CSS/JS w aplikację Android przez Capacitor 8.

## Co zostało przygotowane

- `package.json` z Capacitor 8
- `capacitor.config.json`
- `scripts/copy-web.mjs`
- `frontend/runtime-config.js`
- frontend korzysta z `window.FPS_API_URL`, więc APK może łączyć się z backendem na Render
- `credentials: include` w zapytaniach API
- backend ma obsługę CORS dla `capacitor://localhost` i `http://localhost`
- ustawienia sesji Flask można przełączyć na cross-site cookies przez zmienne Render

## Ważne: URL Render

Przed zbudowaniem APK otwórz:

`frontend/runtime-config.js`

i ustaw:

`window.FPS_API_URL = 'https://TWOJ-PROJEKT.onrender.com/api';`

Nie wpisuj końcowego `/` po domenie; `/api` już jest częścią wartości.

## Render — zmienne środowiskowe

Dla APK ustaw:

- `SESSION_COOKIE_SAMESITE=None`
- `SESSION_COOKIE_SECURE=1`
- `FLASK_SECRET_KEY` na własny, długi losowy sekret

## Budowanie

Na komputerze lub w chmurowym środowisku z Node + Android SDK:

```bash
npm install
npm run copy:web
npx cap add android
npx cap sync android
cd android
./gradlew assembleDebug
```

APK debug będzie w:

`android/app/build/outputs/apk/debug/app-debug.apk`

## Istotne ograniczenie obecnej architektury

Silnik gry i stan sesji nadal działają po stronie Flask/Render. APK jest więc natywną powłoką nad frontendem, ale do działania większości API potrzebuje internetu.

Następnym etapem może być przeniesienie zapisu gry do lokalnego storage oraz tryb offline.

## Dźwięki i muzyka

Możesz dodawać pliki do:

`frontend/audio/`

a następnie odtwarzać je z JS. Obecna wersja ma już syntetyzowane efekty Web Audio, więc przejście na prawdziwe pliki audio jest proste.


## FPS-Pro backend
The APK/web client is configured to use `https://fps-pro.onrender.com`.
