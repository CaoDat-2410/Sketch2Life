// FEAT-066 C6 M9-B: first Teacher of a class (SRS §21.2 line 1650; O-3a..O-3d).
// Candidates come only from the server list (display name and an opaque ref); the command sends
// If-Match with the class assignment revision and one Idempotency-Key per exact command.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { assignmentOutcomeMessage, classService, type Be1Class, type Be1TeacherCandidate } from "../services/classService";
import { Alert, Button, EmptyState, FormField, Select } from "../../../../shared/ui";

type Props = {
  selectedClass: Be1Class | undefined;
  onAssigned: () => void;
};

const CANDIDATE_ERROR = "Không tải được danh sách Teacher của tổ chức.";

export function TeacherAssignmentCard({ selectedClass, onAssigned }: Props) {
  const [candidates, setCandidates] = useState<Be1TeacherCandidate[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [candidateRef, setCandidateRef] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reloadCandidates, setReloadCandidates] = useState(0);
  const keys = useRef(new Map<string, string>());
  const revision = selectedClass?.assignment_revision;
  // T-7b: a suspended or archived class is read-only, so no assignment is offered (SRS l.593).
  const classActive = selectedClass?.state === "active";
  const canAssign = Boolean(selectedClass && classActive && revision !== undefined && !selectedClass.has_active_teacher);

  useEffect(() => {
    if (!canAssign) return;
    let current = true;
    void Promise.resolve()
      .then(() => {
        if (!current) return null;
        setLoading(true);
        setError("");
        return classService.listTeacherCandidates();
      })
      .then((page) => {
        if (!current || !page) return;
        setCandidates(page.items);
        setNextCursor(page.next_cursor);
        // No preselection: the manager chooses explicitly (an assignment cannot be changed here).
        setCandidateRef((selected) => (page.items.some((item) => item.candidate_ref === selected) ? selected : ""));
      })
      .catch(() => { if (current) setError(CANDIDATE_ERROR); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [canAssign, reloadCandidates]);

  const loadMore = async () => {
    if (!nextCursor) return;
    setLoading(true);
    try {
      const page = await classService.listTeacherCandidates(nextCursor);
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

  const assign = async () => {
    if (!selectedClass || revision === undefined || !candidateRef) return;
    const signature = JSON.stringify([selectedClass.class_id, candidateRef, revision]);
    let key = keys.current.get(signature);
    if (!key) {
      key = crypto.randomUUID();
      keys.current.set(signature, key);
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await classService.assignTeacher(selectedClass.class_id, candidateRef, revision, key);
      keys.current.delete(signature);
      setNotice("Đã phân công Teacher cho lớp.");
      onAssigned();
    } catch (cause) {
      const outcome = assignmentOutcomeMessage(cause);
      setError(outcome.text);
      if (outcome.reload) {
        setReloadCandidates((value) => value + 1);
        onAssigned();
      }
    } finally {
      setBusy(false);
    }
  };

  let body: ReactNode;
  if (!selectedClass) {
    body = <Alert role="status">Chọn lớp để phân công Teacher.</Alert>;
  } else if (!classActive) {
    body = <Alert role="status" tone="warning">Lớp không ở trạng thái hoạt động (tạm ngưng chỉ đọc hoặc đã lưu trữ); không thể phân công Teacher.</Alert>;
  } else if (selectedClass.has_active_teacher) {
    body = <Alert role="status" tone="info">Lớp đã có Teacher phụ trách; đổi Teacher chưa được hỗ trợ.</Alert>;
  } else if (revision === undefined) {
    body = <Alert role="status" tone="warning">Máy chủ chưa trả phiên bản phân công của lớp; tạm thời chưa thể phân công.</Alert>;
  } else if (!loading && !error && candidates.length === 0) {
    body = <EmptyState title="Chưa có Teacher nào của tổ chức đủ điều kiện." />;
  } else {
    body = (
      <form className="cozy-form-stack" onSubmit={(event) => { event.preventDefault(); void assign(); }}>
        {error && <Alert role="alert" tone="danger">{error}</Alert>}
        {error === CANDIDATE_ERROR && (
          <div>
            <Button type="button" variant="secondary" onClick={() => setReloadCandidates((value) => value + 1)} disabled={loading}>Tải lại danh sách</Button>
          </div>
        )}
        <div className="cozy-form-grid">
          <FormField className="cozy-span-4" label="Teacher của tổ chức" htmlFor="manager-assignment-teacher" required>
            <Select id="manager-assignment-teacher" aria-label="Teacher của tổ chức" value={candidateRef} onChange={(event) => setCandidateRef(event.target.value)} disabled={busy || loading}>
              <option value="" disabled>Chọn Teacher</option>
              {candidates.map((item) => (
                <option key={item.candidate_ref} value={item.candidate_ref}>{item.display_name ?? "Teacher chưa có tên hiển thị"}</option>
              ))}
            </Select>
          </FormField>
          <div className="cozy-form-actions cozy-span-2 cozy-form-inline-action" style={{ marginTop: 0 }}>
            {nextCursor && <Button type="button" variant="secondary" onClick={() => void loadMore()} disabled={loading || busy}>Tải thêm</Button>}
            <Button type="submit" variant="primary" loading={busy} disabled={busy || loading || !candidateRef}>Phân công</Button>
          </div>
        </div>
        {!busy && !loading && !candidateRef && (
          <p className="cozy-form-disabled-hint">Chọn Teacher ở trên để bật nút phân công.</p>
        )}
      </form>
    );
  }

  return (
    <section className="manager-business-card cozy-form-card cozy-form-card--wide" aria-labelledby="teacher-assignment-title">
      <div className="cozy-form-stack">
        <p className="manager-business-eyebrow" style={{ margin: 0 }}>Phân công lần đầu</p>
        <h2 id="teacher-assignment-title" style={{ margin: 0 }}>Phân công Teacher</h2>
        {body}
        {candidates.length === 0 && error && <Alert role="alert" tone="danger">{error}</Alert>}
        {candidates.length === 0 && error === CANDIDATE_ERROR && (
          <div>
            <Button type="button" variant="secondary" onClick={() => setReloadCandidates((value) => value + 1)} disabled={loading}>Tải lại danh sách</Button>
          </div>
        )}
        {notice && <Alert role="status" tone="success">{notice}</Alert>}
        <p className="manager-business-subtle" style={{ margin: 0 }}>Chỉ hiện tên hiển thị; không hiện email hay mã định danh đăng nhập.</p>
      </div>
    </section>
  );
}
