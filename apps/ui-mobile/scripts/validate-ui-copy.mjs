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
if (
  !flow2.includes("nav('pixi_intro')")
  || !flow2.includes("nav('video_placeholder')")
  || !flow2.includes("nav('activity_detail')")
) {
  throw new Error('Gate B, Pixi intro, video placeholder and outdoor activity order must remain explicit.');
}
if (
  !flow2.includes('OrientationLock.LANDSCAPE')
  || !flow2.includes('OrientationLock.PORTRAIT_UP')
  || !flow2.includes('RendererControlCommandSchema')
) {
  throw new Error('Landscape lifecycle and bounded Pixi playback controls must remain wired.');
}
if (!flow2.includes('Video chính sẽ được thêm ở phiên bản sau')) {
  throw new Error('The future-video surface must remain an honest placeholder.');
}
if (!flow2.includes('Đang tạo các hướng câu chuyện')) {
  throw new Error('Understanding must expose stage-aware loading instead of a frozen percentage.');
}

console.log('UI_COPY_AND_RECOVERY_VALID');
