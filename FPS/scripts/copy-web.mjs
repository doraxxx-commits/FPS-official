import fs from 'fs-extra';
import path from 'path';

const ROOT_DIR = path.resolve();
const ANDROID_PYTHON_DIR = path.join(ROOT_DIR, 'android', 'app', 'src', 'main', 'python');
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');
const ANDROID_ASSETS_DIR = path.join(ROOT_DIR, 'android', 'app', 'src', 'main', 'assets', 'public');

async function syncAll() {
    try {
        console.log('🔄 Kopiowanie football_engine oraz backendu do Android Studio...');
        await fs.ensureDir(ANDROID_PYTHON_DIR);
        await fs.copy(path.join(ROOT_DIR, 'backend', 'app.py'), path.join(ANDROID_PYTHON_DIR, 'app.py'));
        await fs.copy(path.join(ROOT_DIR, 'football_engine'), path.join(ANDROID_PYTHON_DIR, 'football_engine'));
        
        console.log('🔄 Kopiowanie frontend do assets/public...');
        await fs.ensureDir(ANDROID_ASSETS_DIR);
        await fs.copy(FRONTEND_DIR, ANDROID_ASSETS_DIR);
        
        console.log('✅ Automatyczna synchronizacja zakończona pomyślnie!');
    } catch (err) {
        console.error('❌ Błąd synchronizacji:', err);
    }
}

syncAll();
