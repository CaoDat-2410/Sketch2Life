import type { LessonSummary, ParentProfile } from '../../domain/types';

export const ALL_LESSONS_TOPIC = 'Tất cả';

export type LessonCatalogEmptyState = 'no-lessons' | null;

export type LessonCatalogViewModel = {
  topics: string[];
  selectedTopic: string;
  visibleLessons: LessonSummary[];
  emptyState: LessonCatalogEmptyState;
};

export type HomeProfileSummary = {
  title: string;
  description: string;
  actionLabel: string;
};

function compareVietnameseText(left: string, right: string): number {
  return left.localeCompare(right, 'vi', { sensitivity: 'base' }) || left.localeCompare(right);
}

export function buildHomeProfileSummary(profiles: readonly ParentProfile[]): HomeProfileSummary {
  return {
    title: 'Hồ sơ của bé',
    description: profiles.length === 0
      ? 'Tạo hồ sơ để lưu độ tuổi và sở thích cho từng buổi.'
      : `${profiles.length} hồ sơ đã sẵn sàng.`,
    actionLabel: 'Xem hồ sơ',
  };
}

export function buildLessonCatalogViewModel(
  lessons: readonly LessonSummary[],
  requestedTopic: string = ALL_LESSONS_TOPIC,
): LessonCatalogViewModel {
  const topicNames = [...new Set(
    lessons
      .map((lesson) => lesson.topic.trim())
      .filter((topic) => topic.length > 0),
  )].sort(compareVietnameseText);
  const topics = [ALL_LESSONS_TOPIC, ...topicNames];
  const selectedTopic = topics.includes(requestedTopic) ? requestedTopic : ALL_LESSONS_TOPIC;
  const matchingLessons = selectedTopic === ALL_LESSONS_TOPIC
    ? [...lessons]
    : lessons.filter((lesson) => lesson.topic.trim() === selectedTopic);
  const visibleLessons = matchingLessons.sort((left, right) => (
    compareVietnameseText(left.title, right.title)
    || left.lesson_id.localeCompare(right.lesson_id)
    || left.version_id.localeCompare(right.version_id)
  ));

  return {
    topics,
    selectedTopic,
    visibleLessons,
    emptyState: lessons.length === 0 ? 'no-lessons' : null,
  };
}
