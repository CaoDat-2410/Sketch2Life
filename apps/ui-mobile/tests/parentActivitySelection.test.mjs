import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const apiSource = readFileSync(
  new URL('../src/parent/infrastructure/http/ParentApi.ts', import.meta.url),
  'utf8',
);
const learningSource = readFileSync(
  new URL('../src/parent/application/use-cases/ParentLearningUseCases.ts', import.meta.url),
  'utf8',
);
const screenSource = readFileSync(
  new URL('../src/parent/presentation/screens/ActivityScreen.tsx', import.meta.url),
  'utf8',
);
const guideControllerSource = readFileSync(
  new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url),
  'utf8',
);
const guideScreenSource = readFileSync(
  new URL('../src/parent/presentation/screens/SketchGuideScreen.tsx', import.meta.url),
  'utf8',
);

describe('Parent primary activity selection contract', () => {
  it('requires a selected activity before initial story generation', () => {
    expect(learningSource).toContain('PARENT_PRIMARY_ACTIVITY_REQUIRED');
    expect(learningSource).toContain('primaryActivity.activityRef');
  });

  it('sends only the selected AI response request/ref pair to the story API', () => {
    expect(apiSource).toContain('primary_activity_request_id: primaryActivity.requestId');
    expect(apiSource).toContain('primary_activity_ref: primaryActivity.activityRef');
    expect(apiSource).not.toContain('primary_activity: primaryActivity');
  });

  it('renders selectable cards and disables continue until a choice is made', () => {
    expect(screenSource).toContain('accessibilityRole="radio"');
    expect(screenSource).toContain('props.onSelect(activity.activity_ref)');
    expect(screenSource).toContain('!props.selectedActivityRef');
    expect(screenSource).not.toContain('Bỏ qua gợi ý');
  });

  it('allows one AI guide draft after catalog lookup fails while showing the failure', () => {
    expect(guideControllerSource).toContain('setGuideError(displayError(cause));');
    expect(guideControllerSource).toContain('setGuideCatalogChecked(true);');
    expect(guideScreenSource).toContain('Chưa tải được mẫu đã duyệt');
    expect(guideScreenSource).toContain('Tạo gợi ý nét vẽ');
    expect(guideScreenSource).toContain('Thư viện chưa phản hồi.');
  });
});
