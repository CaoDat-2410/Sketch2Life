// FEAT-066 M9-B: first assignment and durable Teacher reassignment/offboarding.
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  assignmentOutcomeMessage,
  assignmentTransferStateLabel,
  classService,
  teacherCandidateLabels,
  type Be1Class,
  type Be1TeacherAssignmentTransferAcceptedV1,
  type Be1TeacherAssignmentTransferState,
  type Be1TeacherCandidate,
} from "../services/classService";
import { AdminBe1Error } from "../services/be1Client";
import { Alert, Button, ConfirmDialog, EmptyState, FormField, Select } from "../../../../shared/ui";

const CANDIDATE_ERROR = "Không tải được danh sách Giáo viên của tổ chức.";
const DEFAULT_TRANSFER_POLL_INTERVAL_MS = 2_000;
const MAX_TRANSFER_POLLS = 30;
const TRANSFER_POLL_FOLLOW_UP = "Không thể tự động kiểm tra trạng thái chuyển giáo viên. Hãy kiểm tra lại để xem trạng thái mới nhất.";
const TERMINAL_TRANSFER_STATES: ReadonlySet<Be1TeacherAssignmentTransferState> = new Set([
  "COMPLETED",
  "OFFBOARDED",
  "COMPENSATED_CONFLICT",
]);

type PendingAssignmentAction =
  | { kind: "reassign"; classId: string; displayName: string; candidateRef: string; revision: number }
  | { kind: "offboard"; classId: string; displayName: string; revision: number };

type Props = {
  selectedClass: Be1Class | undefined;
  onAssigned: () => void;
  /** Poll interval injection keeps transfer UI tests fast while production polls every 2 seconds. */
  pollIntervalMs?: number;
};

export function TeacherAssignmentCard({
  selectedClass,
  onAssigned,
  pollIntervalMs = DEFAULT_TRANSFER_POLL_INTERVAL_MS,
}: Props) {
  const [candidates, setCandidates] = useState<Be1TeacherCandidate[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [candidateSelection, setCandidateSelection] = useState({ scope: "", ref: "" });
  const [loading, setLoading] = useState(false);
  const [candidatesLoaded, setCandidatesLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reloadCandidates, setReloadCandidates] = useState(0);
  const [transfer, setTransfer] = useState<Be1TeacherAssignmentTransferAcceptedV1 | null>(null);
  const [transferStatus, setTransferStatus] = useState<{
    state: Be1TeacherAssignmentTransferState;
  } | null>(null);
  const [pollMessage, setPollMessage] = useState("");
  const [pollRun, setPollRun] = useState(0);
  const [pendingAction, setPendingAction] = useState<PendingAssignmentAction | null>(null);
  const keys = useRef(new Map<string, string>());
  const busyRef = useRef(false);
  const onAssignedRef = useRef(onAssigned);
  const revision = selectedClass?.assignment_revision;
  const classActive = selectedClass?.state === "active";
  const hasAssignmentRevision = revision !== undefined;
  const candidateScope = JSON.stringify([
    selectedClass?.class_id ?? null,
    revision ?? null,
    selectedClass?.has_active_teacher ?? null,
  ]);
  const candidateRef = candidateSelection.scope === candidateScope &&
    candidates.some((item) => item.candidate_ref === candidateSelection.ref)
    ? candidateSelection.ref
    : "";
  const transferState = transferStatus?.state ?? transfer?.state;
  const transferBlocksActions = Boolean(
    transfer && (!transferStatus || !TERMINAL_TRANSFER_STATES.has(transferStatus.state)),
  );
  const canManageCandidates = Boolean(
    classActive && hasAssignmentRevision &&
    (selectedClass?.has_active_teacher === false || selectedClass?.has_active_teacher === true) &&
    !transferBlocksActions,
  );
  const isReassignment = selectedClass?.has_active_teacher === true;
  const activePendingAction = pendingAction &&
    canManageCandidates &&
    selectedClass?.class_id === pendingAction.classId &&
    revision === pendingAction.revision &&
    selectedClass?.has_active_teacher === true &&
    (pendingAction.kind === "offboard" || candidateRef === pendingAction.candidateRef)
    ? pendingAction
    : null;

  if (pendingAction && !activePendingAction) {
    setPendingAction(null);
  }

  useEffect(() => {
    onAssignedRef.current = onAssigned;
  }, [onAssigned]);

  useEffect(() => {
    setError("");
    setNotice("");
    setTransfer(null);
    setTransferStatus(null);
    setPollMessage("");
    setPendingAction(null);
  }, [selectedClass?.class_id]);

  useEffect(() => {
    if (!canManageCandidates) return;
    let current = true;
    setCandidatesLoaded(false);
    void Promise.resolve()
      .then(() => {
        if (!current) return null;
        setLoading(true);
        return classService.listTeacherCandidates(undefined, selectedClass?.class_id);
      })
      .then((page) => {
        if (!current || !page) return;
        setCandidates(page.items);
        setNextCursor(page.next_cursor);
        setError((currentError) => currentError === CANDIDATE_ERROR ? "" : currentError);
      })
      .catch(() => { if (current) setError(CANDIDATE_ERROR); })
      .finally(() => {
        if (current) {
          setLoading(false);
          setCandidatesLoaded(true);
        }
      });
    return () => { current = false; };
  // A new assignment revision changes who the current Teacher is, so the list is read again.
  }, [canManageCandidates, reloadCandidates, selectedClass?.class_id, selectedClass?.assignment_revision]);

  useEffect(() => {
    if (!transfer) return;
    let current = true;
    let attempts = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();

    const poll = async () => {
      if (!current) return;
      attempts += 1;
      try {
        const status = await classService.getAssignmentTransfer(
          transfer.class_id,
          transfer.transfer_id,
          controller.signal,
        );
        if (!current) return;
        setTransferStatus(status);
        if (TERMINAL_TRANSFER_STATES.has(status.state)) {
          onAssignedRef.current();
          return;
        }
        if (status.state === "RECONCILE_REQUIRED") {
          onAssignedRef.current();
          return;
        }
      } catch (cause) {
        if (!current || controller.signal.aborted) return;
        if (
          cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500 &&
          cause.status !== 408 && cause.status !== 429
        ) {
          setPollMessage(TRANSFER_POLL_FOLLOW_UP);
          onAssignedRef.current();
          return;
        }
      }

      if (attempts >= MAX_TRANSFER_POLLS) {
        setPollMessage("Chưa có kết quả cuối cùng. Hãy kiểm tra lại trạng thái sau.");
        onAssignedRef.current();
        return;
      }
      timer = setTimeout(() => { void poll(); }, pollIntervalMs);
    };

    timer = setTimeout(() => { void poll(); }, pollIntervalMs);
    return () => {
      current = false;
      if (timer !== undefined) clearTimeout(timer);
      controller.abort();
    };
  }, [transfer, pollIntervalMs, pollRun]);

  const recheckTransfer = () => {
    setPollMessage("");
    setTransferStatus(null);
    setPollRun((value) => value + 1);
  };

  const loadMore = async () => {
    if (!nextCursor || busyRef.current || activePendingAction) return;
    setLoading(true);
    try {
      const page = await classService.listTeacherCandidates(nextCursor, selectedClass?.class_id);
      setCandidates((current) => {
        const byRef = new Map(current.map((item) => [item.candidate_ref, item] as const));
        page.items.forEach((item) => byRef.set(item.candidate_ref, item));
        return Array.from(byRef.values());
      });
      setNextCursor(page.next_cursor === nextCursor ? null : page.next_cursor);
    } catch {
      setError(CANDIDATE_ERROR);
    } finally {
      setLoading(false);
    }
  };

  const takeBusyLock = () => {
    if (busyRef.current) return false;
    busyRef.current = true;
    setBusy(true);
    return true;
  };

  const releaseBusyLock = () => {
    busyRef.current = false;
    setBusy(false);
  };

  const clearActionBanners = () => {
    setNotice("");
    setTransfer(null);
    setTransferStatus(null);
    setPollMessage("");
  };

  const keyFor = (signature: string) => {
    let key = keys.current.get(signature);
    if (!key) {
      key = crypto.randomUUID();
      keys.current.set(signature, key);
    }
    return key;
  };

  const executeReassign = async (classId: string, chosenCandidateRef: string, classRevision: number) => {
    if (!takeBusyLock()) return;
    const signature = JSON.stringify(["REASSIGN", classId, chosenCandidateRef, classRevision]);
    const key = keyFor(signature);
    setError("");
    clearActionBanners();
    try {
      const accepted = await classService.reassignTeacher(classId, chosenCandidateRef, classRevision, key);
      keys.current.delete(signature);
      clearActionBanners();
      if (accepted) {
        setTransfer(accepted);
        setTransferStatus(null);
      } else {
        setTransfer(null);
        setTransferStatus(null);
        setNotice("Lớp đã thay đổi. Danh sách lớp đã được tải lại.");
        onAssigned();
      }
    } catch (cause) {
      const outcome = assignmentOutcomeMessage(cause);
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) {
        keys.current.delete(signature);
      }
      setError(outcome.text);
      if (outcome.reload) {
        setReloadCandidates((value) => value + 1);
        onAssigned();
      }
    } finally {
      releaseBusyLock();
    }
  };

  const handleAssignmentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedClass || revision === undefined || !candidateRef || busyRef.current || activePendingAction) return;

    setError("");
    clearActionBanners();
    const reassigning = selectedClass.has_active_teacher === true;
    if (reassigning) {
      setPendingAction({
        kind: "reassign",
        classId: selectedClass.class_id,
        displayName: selectedClass.display_name,
        candidateRef,
        revision,
      });
      return;
    }

    if (!takeBusyLock()) return;
    const signature = JSON.stringify(["ASSIGN", selectedClass.class_id, candidateRef, revision]);
    const key = keyFor(signature);
    try {
      const result = await classService.assignTeacher(selectedClass.class_id, candidateRef, revision, key);
      keys.current.delete(signature);
      clearActionBanners();
      if (result.kind === "assigned") {
        setNotice("Đã phân công Giáo viên cho lớp.");
        onAssigned();
      } else {
        setTransfer(result.transfer);
        setTransferStatus(null);
      }
    } catch (cause) {
      const outcome = assignmentOutcomeMessage(cause);
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) {
        keys.current.delete(signature);
      }
      setError(outcome.text);
      if (outcome.reload) {
        setReloadCandidates((value) => value + 1);
        onAssigned();
      }
    } finally {
      releaseBusyLock();
    }
  };

  const requestOffboard = () => {
    if (!selectedClass || revision === undefined || selectedClass.has_active_teacher !== true || busyRef.current || activePendingAction) return;
    setError("");
    clearActionBanners();
    setPendingAction({
      kind: "offboard",
      classId: selectedClass.class_id,
      displayName: selectedClass.display_name,
      revision,
    });
  };

  const executeOffboard = async (classId: string, classRevision: number) => {
    if (!takeBusyLock()) return;
    const signature = JSON.stringify(["OFFBOARD", classId, classRevision]);
    const key = keyFor(signature);
    setError("");
    clearActionBanners();
    try {
      const accepted = await classService.offboardTeacher(classId, classRevision, key);
      keys.current.delete(signature);
      clearActionBanners();
      if (accepted) {
        setTransfer(accepted);
        setTransferStatus(null);
      } else {
        setTransfer(null);
        setTransferStatus(null);
        setNotice("Lớp đã thay đổi. Danh sách lớp đã được tải lại.");
        onAssigned();
      }
    } catch (cause) {
      const outcome = assignmentOutcomeMessage(cause);
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) {
        keys.current.delete(signature);
      }
      setError(outcome.text);
      if (outcome.reload) {
        setReloadCandidates((value) => value + 1);
        onAssigned();
      }
    } finally {
      releaseBusyLock();
    }
  };

  const confirmPendingAction = () => {
    const action = activePendingAction;
    if (!action) return;
    setPendingAction(null);
    if (action.kind === "reassign") {
      void executeReassign(action.classId, action.candidateRef, action.revision);
    } else {
      void executeOffboard(action.classId, action.revision);
    }
  };

  const transferTone = transferState === "COMPLETED" || transferState === "OFFBOARDED"
    ? "success"
    : transferState === "RECONCILE_REQUIRED" || transferState === "COMPENSATED_CONFLICT"
      ? "warning"
      : "info";
  const assignableCandidates = candidates.filter((item) => !item.is_current);
  const assignableCandidateLabels = teacherCandidateLabels(assignableCandidates);

  let body: ReactNode;
  if (!selectedClass) {
    body = <Alert role="status">Chọn lớp để quản lý giáo viên phụ trách.</Alert>;
  } else if (!classActive) {
    body = <Alert role="status" tone="warning">Lớp không ở trạng thái hoạt động (tạm ngưng chỉ đọc hoặc đã lưu trữ); không thể thay đổi giáo viên phụ trách.</Alert>;
  } else if (transfer && transferState && transferBlocksActions) {
    body = (
      <Alert role="status" tone={transferTone}>
        <p>{assignmentTransferStateLabel(transferState)}</p>
        {transferState === "RECONCILE_REQUIRED" && <p>Cần quản lý theo dõi để hoàn tất việc chuyển giáo viên.</p>}
        <p>Mã yêu cầu: {transfer.transfer_id.slice(0, 8)}</p>
        {pollMessage && <p>{pollMessage}</p>}
        {(transferStatus?.state === "RECONCILE_REQUIRED" || pollMessage) && (
          <Button type="button" variant="secondary" onClick={recheckTransfer}>Kiểm tra lại</Button>
        )}
      </Alert>
    );
  } else if (!hasAssignmentRevision) {
    body = <Alert role="status" tone="warning">Máy chủ chưa trả phiên bản phân công của lớp; tạm thời chưa thể thay đổi giáo viên.</Alert>;
  } else if (selectedClass.has_active_teacher !== true && selectedClass.has_active_teacher !== false) {
    body = <Alert role="status" tone="warning">Chưa xác định được trạng thái giáo viên phụ trách; hãy tải lại danh sách lớp.</Alert>;
  } else if (candidatesLoaded && !loading && !error && candidates.length === 0 && !isReassignment) {
    body = <EmptyState title="Chưa có Giáo viên nào của tổ chức đủ điều kiện." />;
  } else {
    body = (
      <div className="cozy-form-stack">
        {error && <Alert role="alert" tone="danger">{error}</Alert>}
        {error === CANDIDATE_ERROR && (
          <div>
            <Button type="button" variant="secondary" onClick={() => setReloadCandidates((value) => value + 1)} disabled={loading}>Tải lại danh sách</Button>
          </div>
        )}
        {isReassignment && candidatesLoaded && !loading && !error && candidates.every((item) => item.is_current) && !nextCursor
          ? <EmptyState title="Chưa có Giáo viên nào khác của tổ chức đủ điều kiện." />
          : (
            <form className="cozy-form-stack" onSubmit={(event) => { void handleAssignmentSubmit(event); }}>
              <div className="cozy-form-grid">
                <FormField className="cozy-span-4" label="Giáo viên của tổ chức" htmlFor="manager-assignment-teacher" required>
                  <Select id="manager-assignment-teacher" aria-label="Giáo viên của tổ chức" value={candidateRef} onChange={(event) => setCandidateSelection({ scope: candidateScope, ref: event.target.value })} disabled={busy || loading || Boolean(activePendingAction)}>
                    <option value="" disabled>{isReassignment ? "Chọn Giáo viên khác" : "Chọn Giáo viên"}</option>
                    {assignableCandidates.map((item, index) => (
                      <option key={item.candidate_ref} value={item.candidate_ref}>{assignableCandidateLabels[index]}</option>
                    ))}
                  </Select>
                </FormField>
                <div className="cozy-form-actions cozy-span-2 cozy-form-inline-action" style={{ marginTop: 0 }}>
                  {nextCursor && <Button type="button" variant="secondary" onClick={() => void loadMore()} disabled={loading || busy || Boolean(activePendingAction)}>Tải thêm</Button>}
                  <Button type="submit" variant="primary" loading={busy} disabled={busy || loading || !candidateRef || Boolean(activePendingAction)}>
                    {isReassignment ? "Đổi giáo viên phụ trách" : "Phân công"}
                  </Button>
                </div>
              </div>
              {!busy && !loading && !candidateRef && (
                <p className="cozy-form-disabled-hint">{isReassignment ? "Chọn Giáo viên khác ở trên để đổi người phụ trách." : "Chọn Giáo viên ở trên để bật nút phân công."}</p>
              )}
            </form>
          )}
        {isReassignment && (
          <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button type="button" variant="secondary" onClick={requestOffboard} disabled={busy || Boolean(activePendingAction)} loading={busy}>
              Gỡ giáo viên phụ trách
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <section className="manager-business-card cozy-form-card cozy-form-card--wide" aria-labelledby="teacher-assignment-title">
      <div className="cozy-form-stack">
        <p className="manager-business-eyebrow" style={{ margin: 0 }}>{isReassignment ? "Quản lý phân công" : "Phân công lần đầu"}</p>
        <h2 id="teacher-assignment-title" style={{ margin: 0 }}>Giáo viên phụ trách</h2>
        {transfer && transferStatus && TERMINAL_TRANSFER_STATES.has(transferStatus.state) && (
          <Alert role="status" tone={transferTone}>
            <p>{assignmentTransferStateLabel(transferStatus.state)}</p>
            <p>Mã yêu cầu: {transfer.transfer_id.slice(0, 8)}</p>
          </Alert>
        )}
        {body}
        {notice && <Alert role="status" tone="success">{notice}</Alert>}
        <p className="manager-business-subtle" style={{ margin: 0 }}>Hiển thị tên và email đã được che (nếu có); không hiển thị mã định danh đăng nhập.</p>
      </div>
      <ConfirmDialog
        open={Boolean(activePendingAction)}
        onOpenChange={(open) => {
          if (!open) {
            setPendingAction(null);
            releaseBusyLock();
          }
        }}
        title={activePendingAction?.kind === "offboard" ? "Gỡ giáo viên phụ trách?" : "Đổi giáo viên phụ trách?"}
        description={
          activePendingAction?.kind === "offboard"
            ? `Bạn có chắc muốn gỡ giáo viên phụ trách khỏi lớp “${activePendingAction.displayName}”? Lớp sẽ không còn giáo viên phụ trách.`
            : activePendingAction
              ? `Bạn có chắc muốn đổi giáo viên phụ trách lớp “${activePendingAction.displayName}” sang giáo viên đã chọn không?`
              : ""
        }
        confirmLabel={activePendingAction?.kind === "offboard" ? "Gỡ giáo viên" : "Đổi giáo viên"}
        tone={activePendingAction?.kind === "offboard" ? "danger" : "primary"}
        onConfirm={confirmPendingAction}
      />
    </section>
  );
}
