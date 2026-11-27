/**
 * FEAT-093: what the adult sees while the video is made. Pure functions only (no React, no storage, no network):
 * the real stage list from the server's progress, a rough time left, a short outdoor checklist taken from the chosen
 * activity, the caption shown at a playback time, and the model of the floating status chip.
 */
import type { ParentStoryRunV1, ParentVideoCueV1, ParentVideoProgressV1 } from '../domain/types';

export type VideoStageId = ParentVideoProgressV1['stage'];
export type StageStatus = 'done' | 'active' | 'pending';
export type StageRow = { id: VideoStageId; label: string; status: StageStatus };

const ORDER: readonly VideoStageId[] = ['PLANNING', 'PREPARING_SCENES', 'RENDERING', 'NARRATING', 'ASSEMBLING', 'CHECKING'];

const LABELS: Record<VideoStageId, string> = {
  PLANNING: 'Lên kịch bản từng cảnh',
  PREPARING_SCENES: 'Chuẩn bị tranh và nền',
  RENDERING: 'Tạo các cảnh chuyển động',
  NARRATING: 'Thu giọng kể',
  ASSEMBLING: 'Ghép video và phụ đề',
  CHECKING: 'Kiểm tra trước khi phát',
};

/** The preparation and the narration run beside the scenes, so they count as done once rendering has started. */
export function videoStageRows(progress: ParentVideoProgressV1 | null | undefined): StageRow[] {
  const activeIndex = progress ? ORDER.indexOf(progress.stage) : -1;
  return ORDER.map((id, index) => {
    let label = LABELS[id];
    const counted = id === 'RENDERING' || id === 'PREPARING_SCENES';
    if (counted && progress && progress.stage === id && progress.scene_index !== null && progress.scene_count > 0) {
      label = `${label} (${Math.min(progress.scene_index, progress.scene_count)}/${progress.scene_count})`;
    }
    const status: StageStatus = activeIndex < 0 ? 'pending' : index < activeIndex ? 'done' : index === activeIndex ? 'active' : 'pending';
    return { id, label, status };
  });
}

// Share of the whole wait at which each stage starts and ends (measured on the live runs: rendering dominates).
const SPAN: Record<VideoStageId, readonly [number, number]> = {
  PLANNING: [0.03, 0.08],
  PREPARING_SCENES: [0.08, 0.2],
  RENDERING: [0.2, 0.9],
  NARRATING: [0.9, 0.93],
  ASSEMBLING: [0.93, 0.96],
  CHECKING: [0.96, 0.98],
};

/** How far along the video is, between 0 and 1, from the server's stage and scene numbers; never 1 while working. */
export function videoProgressFraction(progress: ParentVideoProgressV1 | null | undefined): number {
  if (!progress) return 0;
  const [from, to] = SPAN[progress.stage];
  const scenes = progress.scene_count;
  const inside = progress.scene_index !== null && scenes > 0
    ? (Math.min(Math.max(progress.scene_index, 1), scenes) - 1) / scenes
    : 0;
  return from + (to - from) * inside;
}

/** "khoảng 4 phút" — an estimate, rounded up to the minute, never a promise. */
export function formatEta(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds) || seconds <= 0) return 'Sắp xong';
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  return minutes >= 60 ? `khoảng ${Math.floor(minutes / 60)} giờ ${minutes % 60} phút` : `khoảng ${minutes} phút`;
}

export type WaitChecklistItem = { id: string; label: string };

const FALLBACK_CHECKLIST: readonly WaitChecklistItem[] = [
  { id: 'look-outside', label: 'Cùng bé ra ngoài và nhìn xem có gì quanh nhà.' },
  { id: 'find-three', label: 'Tìm ba thứ cùng màu và kể tên chúng.' },
  { id: 'touch-nature', label: 'Chạm nhẹ vào lá, đất hoặc đá và hỏi bé cảm giác thế nào.' },
];

const MAX_ITEMS = 5;
const MAX_LABEL = 140;

/** The adult's own activity first (its instruction lines), else a few gentle outdoor ideas. */
export function waitChecklist(activity: { instructions_text?: string | null; title?: string | null } | null | undefined): WaitChecklistItem[] {
  const text = (activity?.instructions_text ?? '').trim();
  const lines = text
    .split(/\r?\n|(?<=[.!?])\s+/)
    .map((line) => line.replace(/^[\s\-*•\d.)]+/, '').trim())
    .filter((line) => line.length >= 8)
    .slice(0, MAX_ITEMS)
    .map((line, index) => ({ id: `activity-${index + 1}`, label: line.length > MAX_LABEL ? `${line.slice(0, MAX_LABEL - 1).trimEnd()}…` : line }));
  return lines.length > 0 ? lines : [...FALLBACK_CHECKLIST];
}

/** The caption at a playback position, or null between cues (the last cue never lingers past its end). */
export function captionAt(cues: readonly ParentVideoCueV1[] | null | undefined, positionMs: number): ParentVideoCueV1 | null {
  if (!cues || !Number.isFinite(positionMs)) return null;
  for (const cue of cues) {
    if (positionMs >= cue.start_ms && positionMs < cue.end_ms) return cue;
  }
  return null;
}

export type VideoChip = { visible: boolean; text: string; badge: boolean };

const HIDDEN: VideoChip = { visible: false, text: '', badge: false };

/** The floating chip: visible only while a video is in flight (or just became ready) and the adult is elsewhere. */
export function videoChipModel(run: ParentStoryRunV1 | null, onVideoStep: boolean): VideoChip {
  if (!run || run.video === undefined || run.video === null || onVideoStep) return HIDDEN;
  const video = run.video;
  if (video.state === 'READY' && video.playback.state === 'AVAILABLE' && run.run_state === 'VIDEO_READY') {
    return { visible: true, text: 'Video đã sẵn sàng', badge: true };
  }
  if (['ACCEPTED', 'QUEUED', 'GENERATING', 'TECHNICAL_VALIDATING', 'SAFETY_VALIDATING'].includes(video.state)) {
    const progress = video.progress ?? null;
    const stage = progress ? LABELS[progress.stage] : 'Đang tạo video';
    const eta = progress ? ` · ${formatEta(progress.eta_seconds)}` : '';
    return { visible: true, text: `${stage}${eta}`, badge: false };
  }
  return HIDDEN;
}

/** True when the transition means the adult should be told (local notification). */
export function videoBecameReady(previous: ParentStoryRunV1 | null, next: ParentStoryRunV1 | null): boolean {
  const was = previous?.video?.state;
  const now = next?.video?.state;
  return now === 'READY' && was !== undefined && was !== 'READY' && next?.video?.playback.state === 'AVAILABLE';
}

export function videoFailedNow(previous: ParentStoryRunV1 | null, next: ParentStoryRunV1 | null): boolean {
  const was = previous?.video?.state;
  const now = next?.video?.state;
  return (now === 'FAILED' || now === 'SAFETY_BLOCKED') && was !== undefined && was !== now;
}
