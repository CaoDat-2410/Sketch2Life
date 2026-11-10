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

if (process.platform === 'win32' && tasks.some((task) => !/^[A-Za-z0-9:_.=+/-]+$/.test(task))) {
  throw new Error('Gradle tasks may contain only task names and simple command-line options.');
}

const command = process.platform === 'win32' ? (process.env.ComSpec ?? 'cmd.exe') : wrapper;
const args = process.platform === 'win32' ? ['/d', '/s', '/c', `${wrapper} ${tasks.join(' ')}`] : tasks;
const result = spawnSync(command, args, {
  cwd: androidDirectory,
  env: process.env,
  stdio: 'inherit',
  shell: false,
});

if (result.error) {
  throw result.error;
}

process.exitCode = result.status ?? 1;
