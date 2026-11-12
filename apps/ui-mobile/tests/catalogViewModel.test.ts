import { describe, expect, it } from 'vitest';
import type { LessonSummary, ParentProfile } from '../src/parent/domain/types';
import {
  ALL_LESSONS_TOPIC,
  buildHomeProfileSummary,
  buildLessonCatalogViewModel,
} from '../src/parent/presentation/screens/catalogViewModel';

function makeProfile(id: string): ParentProfile {
  return {
    parent_profile_id: id,
    state: 'ACTIVE',
    current_revision: {
      profile_revision_id: `${id}-revision`,
      revision: 1,
      age_months: 60,
      display_name: `Bé ${id}`,
      interests_summary: 'Thiên nhiên',
      revision_sha256: 'synthetic-profile-hash',
      created_at: '2026-01-01T00:00:00Z',
    },
    authorization_state: 'GRANTED',
    authorization_policy_version: 'synthetic-policy',
    authorization_current: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function makeLesson(
  lessonId: string,
  title: string,
  topic: string,
  activityCount = 1,
): LessonSummary {
  return {
    lesson_id: lessonId,
    version_id: `${lessonId}-version-1`,
    title,
    topic,
    target_age_band_ref: 'synthetic-age-band',
    target_age_band_version: 1,
    activity_count: activityCount,
    access_source: 'PUBLIC',
  };
}

describe('Parent catalog view model', () => {
  it('keeps the home profile summary copy and derives its count from injected profiles', () => {
    expect(buildHomeProfileSummary([])).toEqual({
      title: 'Hồ sơ của bé',
      description: 'Tạo hồ sơ để lưu độ tuổi và sở thích cho từng buổi.',
      actionLabel: 'Xem hồ sơ',
    });

    expect(buildHomeProfileSummary([makeProfile('one'), makeProfile('two')])).toEqual({
      title: 'Hồ sơ của bé',
      description: '2 hồ sơ đã sẵn sàng.',
      actionLabel: 'Xem hồ sơ',
    });
  });

  it('offers distinct topic filters and sorts matching lessons by title', () => {
    const lessons = [
      makeLesson('lesson-z', 'Vòng đời bướm', 'Thiên nhiên', 2),
      makeLesson('lesson-a', 'Khu vườn nhỏ', 'Thiên nhiên', 1),
      makeLesson('lesson-color', 'Sắc màu quanh em', 'Sáng tạo', 3),
      makeLesson('lesson-space', 'Cùng ngắm sao', ' Thiên nhiên ', 4),
    ];

    const viewModel = buildLessonCatalogViewModel(lessons, 'Thiên nhiên');

    expect(viewModel.topics).toEqual([ALL_LESSONS_TOPIC, 'Sáng tạo', 'Thiên nhiên']);
    expect(viewModel.selectedTopic).toBe('Thiên nhiên');
    expect(viewModel.visibleLessons.map((lesson) => lesson.lesson_id)).toEqual([
      'lesson-space',
      'lesson-a',
      'lesson-z',
    ]);
    expect(viewModel.emptyState).toBeNull();
  });

  it('reports an empty catalog and safely resets a topic that is no longer available', () => {
    expect(buildLessonCatalogViewModel([])).toMatchObject({
      topics: [ALL_LESSONS_TOPIC],
      visibleLessons: [],
      emptyState: 'no-lessons',
    });

    const viewModel = buildLessonCatalogViewModel(
      [makeLesson('lesson-garden', 'Khu vườn nhỏ', 'Thiên nhiên')],
      'Âm nhạc',
    );

    expect(viewModel.selectedTopic).toBe(ALL_LESSONS_TOPIC);
    expect(viewModel.visibleLessons).toHaveLength(1);
    expect(viewModel.emptyState).toBeNull();
  });
});
