import { useCallback, useEffect, useRef, useState } from "react";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { Alert, Button, FormField, Select } from "../../../../shared/ui";
import { classService, teacherCandidateLabels, type Be1TeacherCandidate } from "../services/classService";
import {
  storyRunForceCloseErrorMessage,
  storyRunForceCloseService,
  type ManagerActiveStoryRunConflictV1,
} from "../services/storyRunForceCloseService";

type ResultNotice = { tone: "status" | "alert" | "success"; message: string };

const RUN_STATE_LABELS: Record<string, string> = {
  ACTIVE: "Đang chạy",
  RUNNING: "Đang chạy",
  IN_PROGRESS: "Đang xử lý",
  PROCESSING: "Đang xử lý",
  GENERATING: "Đang tạo video",
  QUEUED: "Đang chờ",
  PENDING: "Đang chờ",
  COMPLETED: "Đã hoàn tất",
  FAILED: "Đã thất bại",
  CANCELLED: "Đã hủy",
  ABANDONED: "Đã đóng",
  INPUT_PROCESSING: "Đang chuẩn bị tác phẩm và ý tưởng",
  INPUT_REVIEW: "Cần rà soát ý tưởng và thông tin",
  SUBJECT_REVIEW: "Cần xác nhận chủ thể bức tranh",
  PREPARATION_REVIEW: "Sẵn sàng viết kịch bản",
  SCRIPT_GENERATING: "Đang viết kịch bản",
  SCRIPT_REVIEW: "Cần xác nhận kịch bản",
  VIDEO_QUEUED: "Video đang chờ xử lý",
  VIDEO_GENERATING: "Đang tạo video",
  VIDEO_READY: "Video đã sẵn sàng",
};

function shortenedRunId(runId: string): string {
  return `${runId.slice(0, 8)}…${runId.slice(-4)}`;
}

function runStateLabel(runState: string): string {
  return RUN_STATE_LABELS[runState.toUpperCase()] ?? "Trạng thái hiện tại";
}

function mergeCandidates(current: Be1TeacherCandidate[], incoming: Be1TeacherCandidate[]): Be1TeacherCandidate[] {
  const byRef = new Map(current.map((item) => [item.candidate_ref, item] as const));
  incoming.forEach((item) => byRef.set(item.candidate_ref, item));
  return Array.from(byRef.values());
}

export function StoryRunForceClosePanel() {
  const [candidates, setCandidates] = useState<Be1TeacherCandidate[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [teacherRef, setTeacherRef] = useState("");
  const [candidateLoading, setCandidateLoading] = useState(false);
  const [candidateLoaded, setCandidateLoaded] = useState(false);
  const [candidateError, setCandidateError] = useState(false);
  const [conflict, setConflict] = useState<ManagerActiveStoryRunConflictV1 | null>(null);
  const [reason, setReason] = useState("");
  const [reasonTouched, setReasonTouched] = useState(false);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ResultNotice | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const busyRef = useRef(false);
  const candidateLoadingRef = useRef(false);
  const candidateLoadedRef = useRef(false);
  const pendingCommandRef = useRef<{ signature: string; key: string } | null>(null);
  const candidateLabels = teacherCandidateLabels(candidates);

  useEffect(() => {
    if (result) resultRef.current?.focus();
  }, [result]);

  const loadCandidates = useCallback(async () => {
    if (candidateLoadingRef.current || candidateLoadedRef.current) return;
    candidateLoadingRef.current = true;
    setCandidateLoading(true);
    setCandidateError(false);
    try {
      const page = await classService.listTeacherCandidates();
      setCandidates(page.items);
      setNextCursor(page.next_cursor);
      setTeacherRef((selected) => (page.items.some((item) => item.candidate_ref === selected) ? selected : ""));
      candidateLoadedRef.current = true;
      setCandidateLoaded(true);
    } catch {
      setCandidateError(true);
    } finally {
      candidateLoadingRef.current = false;
      setCandidateLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCandidates();
  }, [loadCandidates]);

  const loadMoreCandidates = async () => {
    if (!nextCursor || candidateLoading || submitting || busyRef.current) return;
    const cursor = nextCursor;
    setCandidateLoading(true);
    setCandidateError(false);
    try {
      const page = await classService.listTeacherCandidates(cursor);
      setCandidates((current) => mergeCandidates(current, page.items));
      setNextCursor(page.next_cursor === cursor ? null : page.next_cursor);
    } catch {
      setCandidateError(true);
    } finally {
      setCandidateLoading(false);
    }
  };

  const loadConflict = async (selectedTeacherRef: string, context: "check" | "stale" | "gone") => {
    try {
      const nextConflict = await storyRunForceCloseService.getActiveConflict(selectedTeacherRef);
      setConflict(nextConflict);
      if (context === "stale") {
        setResult({ tone: "status", message: "Lượt đã thay đổi. Kiểm tra thông tin mới rồi xác nhận lại." });
      } else if (context === "gone") {
        setResult({ tone: "status", message: "Lượt trước không còn hoạt động. Đã tải lại lượt đang chạy; hãy kiểm tra rồi xác nhận lại." });
      } else {
        setResult({ tone: "status", message: "Đã tìm thấy lượt đang chạy." });
      }
    } catch (cause) {
      const outcome = storyRunForceCloseErrorMessage(cause, "lookup");
      setConflict(null);
      if (outcome.kind === "not-found") {
        setResult({
          tone: "status",
          message: context === "gone" ? "Lượt này không còn tồn tại hoặc đã kết thúc." : "Giáo viên này không có lượt đang chạy.",
        });
      } else {
        setResult({ tone: "alert", message: outcome.message });
      }
    }
  };

  const checkConflict = async () => {
    if (!teacherRef || checking || candidateLoading || busyRef.current) return;
    setChecking(true);
    setConflict(null);
    setConfirmationOpen(false);
    setResult({ tone: "status", message: "Đang kiểm tra lượt đang chạy…" });
    try {
      const activeConflict = await storyRunForceCloseService.getActiveConflict(teacherRef);
      setConflict(activeConflict);
      setResult({ tone: "status", message: "Đã tìm thấy lượt đang chạy." });
    } catch (cause) {
      const outcome = storyRunForceCloseErrorMessage(cause, "lookup");
      setConflict(null);
      setResult({ tone: outcome.kind === "not-found" ? "status" : "alert", message: outcome.message });
    } finally {
      setChecking(false);
    }
  };

  const handleForceClose = async () => {
    if (busyRef.current || !conflict || !teacherRef || !confirmationOpen) return;
    const trimmedReason = reason.trim();
    if (trimmedReason.length < 1 || trimmedReason.length > 500) {
      setReasonTouched(true);
      return;
    }

    busyRef.current = true;
    setSubmitting(true);
    setResult(null);
    const signature = JSON.stringify([teacherRef, conflict.run_id, conflict.revision, trimmedReason]);
    let pending = pendingCommandRef.current;
    if (!pending || pending.signature !== signature) {
      pending = { signature, key: createIdempotencyKey() };
      pendingCommandRef.current = pending;
    }

    try {
      await storyRunForceCloseService.forceClose(conflict.run_id, conflict.revision, trimmedReason, pending.key);
      pendingCommandRef.current = null;
      setConflict(null);
      setConfirmationOpen(false);
      setReason("");
      setReasonTouched(false);
      setResult({ tone: "success", message: "Đã đóng lượt (ABANDONED)" });
    } catch (cause) {
      const outcome = storyRunForceCloseErrorMessage(cause, "command");
      if (!outcome.keepIdempotencyKey) pendingCommandRef.current = null;

      if (outcome.kind === "stale") {
        setConfirmationOpen(false);
        await loadConflict(teacherRef, "stale");
      } else if (outcome.kind === "not-found") {
        setConfirmationOpen(false);
        await loadConflict(teacherRef, "gone");
      } else {
        setResult({ tone: "alert", message: outcome.message });
      }
    } finally {
      busyRef.current = false;
      setSubmitting(false);
    }
  };

  const reasonValid = reason.trim().length >= 1 && reason.trim().length <= 500;
  const reasonError = reasonTouched && !reasonValid ? "Nhập lý do từ 1 đến 500 ký tự." : undefined;

  return (
    <section className="manager-business-card cozy-form-card cozy-form-card--wide" aria-labelledby="story-run-force-close-title">
      <div className="cozy-form-stack">
        <h2 id="story-run-force-close-title" style={{ margin: 0 }}>Đóng khẩn cấp lượt tạo video của Giáo viên</h2>
        <p className="manager-business-subtle" style={{ margin: 0 }}>
          Chỉ dùng khi Giáo viên bị chặn phân công lại do còn lượt đang chạy.
        </p>

        {candidateError && (
          <Alert role="alert" tone="danger">
            <div>Không tải được danh sách Giáo viên của tổ chức.</div>
            <Button type="button" size="sm" onClick={() => void loadCandidates()} disabled={candidateLoading}>
              Tải lại danh sách
            </Button>
          </Alert>
        )}

        <div className="cozy-form-grid">
          <div className="cozy-span-4">
            <FormField label="Giáo viên của tổ chức" htmlFor="story-run-force-close-teacher" required>
              <Select
                id="story-run-force-close-teacher"
                value={teacherRef}
                onChange={(event) => {
                  setTeacherRef(event.target.value);
                  setConflict(null);
                  setConfirmationOpen(false);
                  setResult(null);
                }}
                disabled={checking || submitting}
              >
                <option value="" disabled>Chọn Giáo viên</option>
                {candidates.map((candidate, index) => (
                  <option key={candidate.candidate_ref} value={candidate.candidate_ref}>
                    {candidateLabels[index]}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
          <div className="cozy-form-actions cozy-span-2 cozy-form-inline-action" style={{ marginTop: 0 }}>
            {nextCursor && (
              <Button type="button" onClick={() => void loadMoreCandidates()} disabled={candidateLoading || checking || submitting}>
                {candidateLoading ? "Đang tải…" : "Tải thêm Giáo viên"}
              </Button>
            )}
            <Button
              type="button"
              variant="primary"
              onClick={() => void checkConflict()}
              loading={checking}
              disabled={checking || candidateLoading || submitting || !teacherRef}
            >
              Kiểm tra lượt đang chạy
            </Button>
          </div>
        </div>

        {candidateLoading && <Alert role="status">Đang tải danh sách Giáo viên…</Alert>}
        {candidateLoaded && !candidateLoading && candidates.length === 0 && (
          <Alert role="status">Tổ chức chưa có Giáo viên đủ điều kiện.</Alert>
        )}

        {result && (
          <div
            ref={resultRef}
            tabIndex={-1}
            role={result.tone === "alert" ? "alert" : "status"}
            className="rounded-xl border border-rule bg-paper-muted px-4 py-3 text-sm leading-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
          >
            {result.message}
          </div>
        )}

        {conflict && (
          <div className="rounded-xl border border-rule bg-paper-muted px-4 py-3" aria-label="Thông tin lượt đang chạy">
            <dl className="cozy-form-stack" style={{ margin: 0 }}>
              <div><dt className="font-semibold">Mã lượt</dt><dd style={{ margin: 0 }}><code>{shortenedRunId(conflict.run_id)}</code></dd></div>
              <div><dt className="font-semibold">Trạng thái</dt><dd style={{ margin: 0 }}>{runStateLabel(conflict.run_state)}</dd></div>
              <div><dt className="font-semibold">Phiên bản</dt><dd style={{ margin: 0 }}>{conflict.revision}</dd></div>
            </dl>
          </div>
        )}

        {conflict && (
          <div className="cozy-form-stack">
            <FormField
              label="Lý do đóng khẩn cấp"
              htmlFor="story-run-force-close-reason"
              required
              error={reasonError}
              help="Không nhập tên trẻ hoặc nội dung câu chuyện."
            >
              <textarea
                id="story-run-force-close-reason"
                value={reason}
                maxLength={500}
                required
                rows={4}
                onChange={(event) => {
                  setReason(event.target.value);
                  setReasonTouched(true);
                  if (confirmationOpen) setConfirmationOpen(false);
                }}
                disabled={submitting}
                className="w-full rounded-control border border-rule bg-paper px-3 py-2 font-ui text-sm text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              />
            </FormField>

            {!confirmationOpen ? (
              <Button type="button" variant="danger" onClick={() => {
                setReasonTouched(true);
                if (reasonValid) setConfirmationOpen(true);
              }} disabled={submitting || checking}>
                Xem lại yêu cầu
              </Button>
            ) : (
              <div className="cozy-form-stack">
                <Alert role="alert" tone="warning">
                  Bạn có chắc muốn đóng khẩn cấp lượt này? Thao tác không hoàn tác được.
                </Alert>
                <div className="cozy-form-actions" style={{ justifyContent: "flex-start" }}>
                  <Button type="button" variant="secondary" onClick={() => setConfirmationOpen(false)} disabled={submitting}>
                    Hủy xác nhận
                  </Button>
                  <Button type="button" variant="danger" onClick={() => void handleForceClose()} loading={submitting} disabled={submitting}>
                    Xác nhận đóng khẩn cấp
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
