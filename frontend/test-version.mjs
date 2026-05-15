import { execSync } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

function getAppVersion() {
  try {
    const __dirname = dirname(fileURLToPath(import.meta.url));
    const repoRoot = resolve(__dirname, '..');
    console.log('Test 1 - __dirname:', __dirname);
    console.log('Test 1 - repoRoot:', repoRoot);
    const version = execSync('bash scripts/get-version.sh', { cwd: repoRoot, encoding: 'utf-8' }).trim();
    console.log('Test 1 - Version result:', version);
    return version;
  } catch (e) {
    console.log('Test 1 - Catch block:', e.message);
    return 'v0.0.0-unknown';
  }
}

getAppVersion();
