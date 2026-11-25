import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('Parent learning path capture intent', () => {
  it('clears a pending camera/gallery shortcut before Topic or Lesson flow begins', () => {
    const source = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    const entryRoute = source.slice(source.indexOf("if (step === 'entry')"), source.indexOf("if (step === 'topic')"));

    expect(entryRoute).toContain('clearPendingCaptureIntent(); void parent.beginTopicPath();');
    expect(entryRoute).toContain('clearPendingCaptureIntent(); parent.beginLessonPath();');
    expect(source).toContain('function startCaptureFlow(source: \'camera\' | \'gallery\')');
    expect(source).toContain('setPendingCaptureSource(source);');
  });

  it('clears an idea from the previous run when beginning a new topic path', () => {
    const source = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const beginTopicPath = source.slice(source.indexOf('async function beginTopicPath()'), source.indexOf('async function loadTopicSuggestionSet('));

    expect(beginTopicPath).toContain("setIdea('');");
  });
});
