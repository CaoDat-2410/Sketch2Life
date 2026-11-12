import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const androidDirectory = path.resolve(scriptDirectory, '..', 'android');
const wrapper = process.platform === 'win32' ? 'gradlew.bat' : './gradlew';
const tasks = process.argv.slice(2);

if (tasks.length === 0) {
  throw new Error('At least one Gradle task is required.');
}

const result = spawnSync(wrapper, tasks, {
  cwd: androidDirectory,
  env: process.env,
  stdio: 'inherit',
  shell: false,
});

if (result.error) {
  throw result.error;
}

process.exitCode = result.status ?? 1;
