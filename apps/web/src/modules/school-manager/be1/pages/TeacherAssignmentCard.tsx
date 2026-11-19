// FEAT-066 C6 M9-B: first Teacher of a class (SRS §21.2 line 1650; O-3a..O-3d).
// Candidates come only from the server list (display name and an opaque ref); the command sends
// If-Match with the class assignment revision and one Idempotency-Key per exact command.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { assignmentOutcomeMessage, classService, type Be1Class, type Be1TeacherCandidate } from "../services/classService";

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
  const canAssign = Boolean(selectedClass && revision !== undefined && !selectedClass.has_active_teacher);

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
    body = <p className="manager-business-state">Chọn lớp để phân công Teacher.</p>;
  } else if (selectedClass.has_active_teacher) {
    body = <p className="manager-business-state">Lớp đã có Teacher phụ trách; đổi Teacher chưa được hỗ trợ.</p>;
  } else if (revision === undefined) {
    body = <p className="manager-business-state">Máy chủ chưa trả phiên bản phân công của lớp; tạm thời chưa thể phân công.</p>;
  } else if (!loading && !error && candidates.length === 0) {
    body = <p className="manager-business-state">Chưa có Teacher nào của tổ chức đủ điều kiện.</p>;
  } else {
    body = (
      <div className="manager-business-form">
        <label>
          Teacher của tổ chức
          <select value={candidateRef} onChange={(event) => setCandidateRef(event.target.value)} disabled={busy || loading}>
            <option value="" disabled>Chọn Teacher</option>
            {candidates.map((item) => (
              <option key={item.candidate_ref} value={item.candidate_ref}>{item.display_name ?? "Teacher chưa có tên hiển thị"}</option>
            ))}
          </select>
        </label>
        {nextCursor && <button type="button" className="manager-business-button" onClick={() => void loadMore()} disabled={loading || busy}>Tải thêm</button>}
        <button type="button" className="manager-business-button" onClick={() => void assign()} disabled={busy || loading || !candidateRef}>Phân công</button>
      </div>
    );
  }

  return (
    <section className="manager-business-card" aria-labelledby="teacher-assignment-title">
      <div>
        <p className="manager-business-eyebrow">Phân công lần đầu</p>
        <h2 id="teacher-assignment-title">Phân công Teacher</h2>
        {body}
        {error && <p className="manager-business-alert" role="alert">{error}</p>}
        {error === CANDIDATE_ERROR && <button type="button" className="manager-business-button" onClick={() => setReloadCandidates((value) => value + 1)} disabled={loading}>Tải lại danh sách</button>}
        {notice && <p className="manager-business-subtle" role="status">{notice}</p>}
        <p className="manager-business-subtle">Chỉ hiện tên hiển thị; không hiện email hay mã định danh đăng nhập.</p>
      </div>
    </section>
  );
}
