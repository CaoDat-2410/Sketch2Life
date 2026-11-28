import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const deviceMocks = vi.hoisted(() => ({
  share: vi.fn(async (_options: { title?: string; message?: string }) => ({ action: 'sharedAction' })),
  requestDirectoryPermissionsAsync: vi.fn(async () => ({ granted: true, directoryUri: 'content://documents/tree/folder' })),
  createFileAsync: vi.fn(async () => 'content://documents/tree/folder/document.json'),
  writeAsStringAsync: vi.fn(async () => undefined),
}));

vi.mock('react-native', () => ({
  Platform: { OS: 'android' },
  Share: { share: deviceMocks.share },
}));

vi.mock('expo-file-system', () => ({
  StorageAccessFramework: {
    requestDirectoryPermissionsAsync: deviceMocks.requestDirectoryPermissionsAsync,
    createFileAsync: deviceMocks.createFileAsync,
  },
  writeAsStringAsync: deviceMocks.writeAsStringAsync,
}));

import { Platform } from 'react-native';
import type { LessonExportV1 } from '../src/parent/domain/types';
import { saveLessonJson, shareLessonText } from '../src/parent/infrastructure/device/ParentLessonExportDevice';

function exportBody(): LessonExportV1 {
  return {
    contract: 'LessonExportV1',
    lesson_id: 'lesson-42',
    version_id: 'version-3',
    version_no: 3,
    content_sha256: 'a'.repeat(64),
    title: 'Khám phá con cá',
    topic: 'Đại dương',
    locale: 'vi-VN',
    target_age_band_ref: 'age-band:3-5',
    target_age_band_version: 1,
    objectives: ['Nhận biết hình dáng con cá'],
    drawing_subject: 'Con cá',
    drawing_steps_text: 'Vẽ thân cá rồi thêm vây.',
    subject_learning_notes: 'Cùng bé kể về nơi cá sống.',
    script_direction: null,
    script_following_allowed: false,
    activities: [{
      title: 'Quan sát vây cá',
      objective: 'Nhìn hình dáng vây',
      materials_text: 'Giấy và bút màu',
      preparation_text: '',
      instructions_text: 'Cùng bé vẽ vây cá.',
      observation_notes: '',
      safety_notes: '',
      activity_kind: 'indoor',
    }],
    access_source: 'PUBLIC',
    access_expires_at: null,
  };
}

const platform = Platform as unknown as { OS: string };

describe('Parent lesson export device actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    platform.OS = 'android';
    deviceMocks.requestDirectoryPermissionsAsync.mockResolvedValue({ granted: true, directoryUri: 'content://documents/tree/folder' });
    deviceMocks.createFileAsync.mockResolvedValue('content://documents/tree/folder/document.json');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shares readable lesson text with the core Share API and never logs the body', async () => {
    const log = vi.spyOn(console, 'log').mockImplementation(() => undefined);
    const lesson = exportBody();
    await shareLessonText(lesson);

    expect(deviceMocks.share).toHaveBeenCalledWith(expect.objectContaining({
      title: lesson.title,
      message: expect.stringContaining('Mục tiêu\n• Nhận biết hình dáng con cá'),
    }));
    const sharedMessage = deviceMocks.share.mock.calls[0]?.[0]?.message ?? '';
    expect(sharedMessage).toContain('Các bước vẽ\nVẽ thân cá rồi thêm vây.');
    expect(sharedMessage).toContain('Quan sát vây cá');
    expect(log).not.toHaveBeenCalled();
  });

  it('saves JSON through Android Storage Access Framework', async () => {
    const lesson = exportBody();
    const result = await saveLessonJson(lesson);

    expect(result).toBe('saved');
    expect(deviceMocks.requestDirectoryPermissionsAsync).toHaveBeenCalledOnce();
    expect(deviceMocks.createFileAsync).toHaveBeenCalledWith(
      'content://documents/tree/folder',
      'lesson-lesson-42.json',
      'application/json',
    );
    expect(deviceMocks.writeAsStringAsync).toHaveBeenCalledWith(
      'content://documents/tree/folder/document.json',
      JSON.stringify(lesson, null, 2),
    );
  });

  it('treats declined directory access as a cancelled save', async () => {
    deviceMocks.requestDirectoryPermissionsAsync.mockResolvedValue({ granted: false, directoryUri: '' });
    expect(await saveLessonJson(exportBody())).toBe('cancelled');
    expect(deviceMocks.createFileAsync).not.toHaveBeenCalled();
    expect(deviceMocks.writeAsStringAsync).not.toHaveBeenCalled();
  });

  it('skips the file action on web', async () => {
    platform.OS = 'web';
    expect(await saveLessonJson(exportBody())).toBe('unsupported');
    expect(deviceMocks.requestDirectoryPermissionsAsync).not.toHaveBeenCalled();
    expect(deviceMocks.createFileAsync).not.toHaveBeenCalled();
  });
});
