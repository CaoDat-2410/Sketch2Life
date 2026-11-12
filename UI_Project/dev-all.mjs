import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';

const apps = [
  { name: 'parent-ui', port: 5171, title: 'Parent (Phụ huynh)' },
  { name: 'teacher-ui', port: 5172, title: 'Teacher (Giáo viên)' },
  { name: 'school-manager-ui', port: 5173, title: 'School Manager (Quản lý trường)' },
  { name: 'platform-admin-ui', port: 5174, title: 'Platform Admin (Quản trị nền tảng)' },
  { name: 'web-ui', port: 5175, title: 'Web chung (3 vai trò)' },
];

console.log('--- KHỞI ĐỘNG 5 ỨNG DỤNG FRONTEND SKETCH2LIFE ---');

for (const app of apps) {
  const appDir = path.resolve(process.cwd(), app.name);
  const child = spawn('npx', ['vite', '--port', String(app.port), '--host'], {
    cwd: appDir,
    shell: true,
    stdio: 'inherit'
  });

  child.on('error', (err) => {
    console.error(`[${app.name}] Lỗi:`, err);
  });
}
