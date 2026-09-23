import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const root = resolve(import.meta.dirname, '..');
const files = [
  'BaoApp.tsx',
  'src/screens/Flow1Screens.tsx',
  'src/screens/Flow2Screens.tsx',
  'src/context/AppContext.tsx',
];
const forbiddenVisibleTerms = [
  'Lightning',
  'ExperienceSpec',
  'Pixi protocol',
  'Fine Motor',
  'Backend ',
];

for (const relativePath of files) {
  const source = readFileSync(resolve(root, relativePath), 'utf8');
  for (const term of forbiddenVisibleTerms) {
    if (source.includes(term)) {
      throw new Error(`${relativePath} still contains child-facing technical copy: ${term}`);
    }
  }
}

const flow1 = readFileSync(resolve(root, 'src/screens/Flow1Screens.tsx'), 'utf8');
const flow2 = readFileSync(resolve(root, 'src/screens/Flow2Screens.tsx'), 'utf8');
const shell = readFileSync(resolve(root, 'BaoApp.tsx'), 'utf8');

if (!flow1.includes('KeyboardAvoidingView') || !flow2.includes('KeyboardAvoidingView')) {
  throw new Error('Narration and feedback inputs must retain keyboard avoidance.');
}
if (!flow2.includes('Bức vẽ gốc của con vẫn an toàn ở đây.')) {
  throw new Error('Pixi failure must keep the original drawing visible.');
}
if (!flow2.includes('Dành cho người lớn') || !flow2.includes('Thử lại')) {
  throw new Error('Adult details and renderer recovery actions must remain available.');
}
if (!shell.includes('Về bước ảnh') || !shell.includes('Thử lại')) {
  throw new Error('Global workflow modal must expose bounded recovery actions.');
}

console.log('UI_COPY_AND_RECOVERY_VALID');
