import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const androidDirectory = path.resolve(scriptDirectory, '..', 'android');
const wrapper = process.platform === 'win32' ? 'gradlew.bat' : './gradlew';
const tasks = process.argv.slice(2);
const gradleArgumentPattern = /^(?:[A-Za-z][A-Za-z0-9:_-]*|--[A-Za-z][A-Za-z0-9-]*(?:=[A-Za-z0-9._-]+)?)$/;

if (tasks.length === 0) {
  throw new Error('At least one Gradle task is required.');
}

if (tasks.some((task) => !gradleArgumentPattern.test(task))) {
  throw new Error('Gradle arguments must be task names or simple --option flags.');
}

const result = spawnSync(wrapper, tasks, {
  cwd: androidDirectory,
  env: process.env,
  stdio: 'inherit',
  // Windows only runs .bat files through a command shell. Task/flag arguments
  // are restricted above so enabling the shell cannot interpret arbitrary input.
  shell: process.platform === 'win32',
});

if (result.error) {
  throw result.error;
}

process.exitCode = result.status ?? 1;
