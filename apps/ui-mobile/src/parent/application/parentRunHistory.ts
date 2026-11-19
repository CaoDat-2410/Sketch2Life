// FEAT-081 C3b: pure helpers for the Parent run-history screen (no React, no config).
// SRS §21.5 line 1707 (history, cancel, delete), §21.1 line 1640 (cursor paging), FR-C-08.
import type { ParentStoryRunLifecycleEnvelopeV1, ParentStoryRunSummary } from '../domain/types';

export type RunHistoryAction = 'cancel' | 'delete';

export type RunHistoryPage = {
  items: ParentStoryRunSummary[];
  next_cursor: string | null;
};

/** A null cursor replaces the list; a cursor appends without duplicates. */
export function mergeRunHistoryPage(
  current: ParentStoryRunSummary[],
  page: RunHistoryPage,
  requestedCursor: string | null,
): { runs: ParentStoryRunSummary[]; nextCursor: string | null } {
  if (requestedCursor === null) return { runs: page.items, nextCursor: page.next_cursor };
  const seen = new Set(current.map((run) => run.run_id));
  const appended = page.items.filter((run) => !seen.has(run.run_id));
  // A cursor that does not advance stops paging instead of looping.
  const nextCursor = page.next_cursor === requestedCursor ? null : page.next_cursor;
  return { runs: [...current, ...appended], nextCursor };
}

/** One key per (action, run, revision): a retry reuses it, a new revision gets a new key. */
export function runActionSignature(action: RunHistoryAction, run: ParentStoryRunSummary): string {
  return `${action}:${run.run_id}:${run.revision}`;
}

export function retainedRunActionKey(
  store: Map<string, string>,
  signature: string,
  createKey: () => string,
): string {
  const existing = store.get(signature);
  if (existing) return existing;
  const key = createKey();
  store.set(signature, key);
  return key;
}

/** After a 202 the item shows the lifecycle projection; no extra request is needed. */
export function applyLifecycleProjection(
  runs: ParentStoryRunSummary[],
  envelope: ParentStoryRunLifecycleEnvelopeV1,
): ParentStoryRunSummary[] {
  const projection = envelope.lifecycle;
  return runs.map((run) => (
    run.run_id === projection.run_id
      ? {
        ...run,
        run_state: projection.run_state,
        revision: projection.revision,
        deleting: true,
        can_cancel: false,
        can_delete: false,
        parent_profile_id: null,
      }
      : run
  ));
}

export type RunActionOutcome = 'reload' | 'remove' | 'error';

/** 409 stale or invalid transition → reload; 404 → the run is gone; anything else → error. */
export function runActionOutcome(code: string | undefined, status: number | undefined): RunActionOutcome {
  if (status === 404 || code === 'RESOURCE_NOT_FOUND') return 'remove';
  if (status === 409 || code === 'STALE_REVISION' || code === 'INVALID_STATE_TRANSITION') return 'reload';
  return 'error';
}

const STATE_LABELS: Record<string, string> = {
  INPUT_PROCESSING: 'Đang xử lý tranh',
  SUBJECT_REVIEW: 'Chờ xác nhận nội dung tranh',
  PREPARATION_REVIEW: 'Chờ xác nhận chuẩn bị',
  SCRIPT_GENERATING: 'Đang tạo câu chuyện',
  SCRIPT_GENERATION_UNKNOWN: 'Đang kiểm tra câu chuyện',
  SCRIPT_REVIEW: 'Chờ duyệt câu chuyện',
  VIDEO_ADMISSION_PENDING: 'Chờ xếp hàng video',
  COMPLETED: 'Đã hoàn tất',
  FAILED: 'Không hoàn tất',
  ABANDONED: 'Đã dừng',
  DELETE_PENDING: 'Đang xóa',
};

export function runHistoryStateLabel(run: ParentStoryRunSummary): string {
  if (run.deleting) return 'Đang xóa';
  return STATE_LABELS[run.run_state] ?? 'Trạng thái chưa xác định';
}

/** Date in Vietnamese day/month/year form; the run has no title or topic in the summary. */
export function runHistoryDateLabel(run: ParentStoryRunSummary): string {
  const date = new Date(run.created_at);
  if (Number.isNaN(date.getTime())) return 'Buổi sáng tạo';
  const pad = (value: number) => String(value).padStart(2, '0');
  return `Buổi ngày ${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`;
}
