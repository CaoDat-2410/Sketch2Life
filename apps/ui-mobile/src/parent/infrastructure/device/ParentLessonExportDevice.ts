import * as FileSystem from 'expo-file-system';
import { Platform, Share } from 'react-native';
import type { LessonExportV1 } from '../../domain/types';

export type ParentLessonJsonSaveResult = 'saved' | 'cancelled' | 'unsupported';

export async function shareLessonText(lesson: LessonExportV1): Promise<void> {
  await Share.share({
    title: lesson.title,
    message: renderLessonText(lesson),
  });
}

export async function saveLessonJson(lesson: LessonExportV1): Promise<ParentLessonJsonSaveResult> {
  if (Platform.OS !== 'android') return 'unsupported';

  const permission = await FileSystem.StorageAccessFramework.requestDirectoryPermissionsAsync();
  if (!permission.granted || !permission.directoryUri) return 'cancelled';

  const safeLessonId = lesson.lesson_id.replace(/[^A-Za-z0-9._-]/g, '_');
  const fileUri = await FileSystem.StorageAccessFramework.createFileAsync(
    permission.directoryUri,
    `lesson-${safeLessonId}.json`,
    'application/json',
  );
  await FileSystem.writeAsStringAsync(fileUri, JSON.stringify(lesson, null, 2));
  return 'saved';
}

export function renderLessonText(lesson: LessonExportV1): string {
  const sections = [
    lesson.title,
    `Chủ đề: ${lesson.topic}`,
    lesson.objectives.length > 0
      ? `Mục tiêu\n${lesson.objectives.map((objective) => `• ${objective}`).join('\n')}`
      : '',
    lesson.drawing_steps_text.trim() ? `Các bước vẽ\n${lesson.drawing_steps_text.trim()}` : '',
    lesson.activities.length > 0
      ? `Hoạt động\n${lesson.activities.map((activity, index) => {
        const details = [
          activity.objective,
          activity.instructions_text,
          activity.materials_text ? `Chuẩn bị: ${activity.materials_text}` : '',
        ].filter(Boolean).join('\n');
        return `${index + 1}. ${activity.title}${details ? `\n${details}` : ''}`;
      }).join('\n\n')}`
      : '',
  ];
  return sections.filter(Boolean).join('\n\n');
}
