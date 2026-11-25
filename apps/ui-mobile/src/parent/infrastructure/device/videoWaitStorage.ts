/**
 * Local-only storage of the waiting-time checklist ticks and the caption options (FEAT-093). Nothing leaves the
 * device; the files hold run ids and tick ids only. A storage failure never breaks the screen: reads answer the
 * defaults and writes are best effort.
 */
import * as FileSystem from 'expo-file-system';

export type CaptionOptions = { narrationVoice: boolean; captions: boolean; size: 'normal' | 'large' };
export const DEFAULT_CAPTION_OPTIONS: CaptionOptions = { narrationVoice: true, captions: true, size: 'normal' };

const SAFE_ID = /^[A-Za-z0-9_-]{1,80}$/;

function directory(): string | null {
  return FileSystem.documentDirectory ? `${FileSystem.documentDirectory}video-wait/` : null;
}

async function readJson(name: string): Promise<unknown> {
  const base = directory();
  if (!base) return null;
  try {
    return JSON.parse(await FileSystem.readAsStringAsync(`${base}${name}`));
  } catch {
    return null;
  }
}

async function writeJson(name: string, value: unknown): Promise<void> {
  const base = directory();
  if (!base) return;
  try {
    await FileSystem.makeDirectoryAsync(base, { intermediates: true });
    await FileSystem.writeAsStringAsync(`${base}${name}`, JSON.stringify(value));
  } catch {
    // best effort: the checklist still works for this session
  }
}

export async function loadTicks(runId: string): Promise<string[]> {
  if (!SAFE_ID.test(runId)) return [];
  const value = await readJson(`ticks-${runId}.json`);
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && SAFE_ID.test(item)).slice(0, 20) : [];
}

export async function saveTicks(runId: string, ticks: readonly string[]): Promise<void> {
  if (!SAFE_ID.test(runId)) return;
  await writeJson(`ticks-${runId}.json`, ticks.slice(0, 20));
}

export async function loadCaptionOptions(): Promise<CaptionOptions> {
  const value = await readJson('caption-options.json');
  if (typeof value !== 'object' || value === null) return DEFAULT_CAPTION_OPTIONS;
  const record = value as Record<string, unknown>;
  return {
    narrationVoice: record.narrationVoice !== false,
    captions: record.captions !== false,
    size: record.size === 'large' ? 'large' : 'normal',
  };
}

export async function saveCaptionOptions(options: CaptionOptions): Promise<void> {
  await writeJson('caption-options.json', options);
}
