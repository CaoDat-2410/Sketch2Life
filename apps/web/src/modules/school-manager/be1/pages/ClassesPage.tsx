import { useEffect, useRef, useState } from "react";
import { RefreshCw, School } from "lucide-react";
import {
  allowedClassCommands,
  classService,
  classStateLabel,
  classStateOutcomeMessage,
  type Be1Class,
  type Be1ClassFilter,
  type ClassStateCommand,
} from "../services/classService";
import { AdminBe1Error } from "../services/be1Client";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { Alert, Button, FormField, Select } from "../../../../shared/ui";

export function ClassesPage() {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [retryName, setRetryName] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [stateError, setStateError] = useState("");
  const [notice, setNotice] = useState("");
  const actionKeys = useRef(new Map<string, string>());
  // T-7b: the list filter (default every state) and one key per exact suspend/archive command.
  const [filter, setFilter] = useState<Be1ClassFilter>("all");
  const [pendingCommand, setPendingCommand] = useState<ClassStateCommand | null>(null);
  const [changingState, setChangingState] = useState(false);
  const stateKeys = useRef(new Map<string, string>());
  const selected = classes.find((item) => item.class_id === selectedId) ?? classes[0];

  const refresh = async (nextFilter: Be1ClassFilter = filter) => {
    setLoading(true);
    try {
      const items = await classService.listClasses(nextFilter);
      setClasses(items);
      setSelectedId((current) => items.some((item) => item.class_id === current) ? current : items[0]?.class_id ?? "");
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được danh sách lớp từ BE1.");
      setClasses([]); setSelectedId("");
    } finally { setLoading(false); }
  };

  useEffect(() => {
    let current = true;
    classService.listClasses("all")
      .then((items) => { if (current) { setClasses(items); setSelectedId(items[0]?.class_id ?? ""); } })
      .catch((cause: unknown) => { if (current) setError(cause instanceof Error ? cause.message : "Không tải được danh sách lớp từ BE1."); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, []);

  const createClass = async () => {
    const name = displayName.trim();
    if (!name || creating) return;
    // One key per user action: a retry of the same name reuses it, a changed name is a new action.
    const key = actionKeys.current.get(name) ?? createIdempotencyKey();
    actionKeys.current.set(name, key);
    setCreating(true); setError(""); setNotice("");
    try {
      const created = await classService.createClass(name, key);
      actionKeys.current.delete(name);
      setRetryName(null);
      setDisplayName("");
      setNotice(`Đã tạo lớp “${created.display_name}”.`);
      setClasses((items) => [created, ...items.filter((item) => item.class_id !== created.class_id)]);
      setSelectedId(created.class_id);
      try {
        const items = await classService.listClasses(filter);
        setClasses(items); setSelectedId(created.class_id);
      } catch {
        setError("Lớp đã được tạo; danh sách chưa thể làm mới. Chọn Làm mới từ BE1 để cập nhật.");
      }
    } catch (cause) {
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) actionKeys.current.delete(name);
      setRetryName(actionKeys.current.has(name) ? name : null);
      setError(cause instanceof Error ? cause.message : "Không thể tạo lớp. Hãy thử lại cùng yêu cầu.");
    } finally { setCreating(false); }
  };

  const changeState = async (command: ClassStateCommand) => {
    const target = selected;
    const revision = target?.class_revision;
    if (!target || revision === undefined || changingState) return;
    const signature = JSON.stringify([target.class_id, command, revision]);
    const key = stateKeys.current.get(signature) ?? createIdempotencyKey();
    stateKeys.current.set(signature, key);
    setChangingState(true); setStateError(""); setNotice("");
    try {
      const result = await classService.changeClassState(target.class_id, command, revision, key);
      stateKeys.current.delete(signature);
      setPendingCommand(null);
      setNotice(command === "suspend"
        ? `Đã tạm ngưng lớp “${target.display_name}”. Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.`
        : `Đã lưu trữ lớp “${target.display_name}”.`);
      setClasses((items) => items.map((item) => item.class_id === result.class_id ? { ...item, state: result.state, class_revision: result.class_revision } : item));
      await refresh();
    } catch (cause) {
      const outcome = classStateOutcomeMessage(cause);
      if (!outcome.keepKey) stateKeys.current.delete(signature);
      // The reload clears the page error, so the refusal text is set after it.
      if (outcome.reload) { setPendingCommand(null); await refresh(); }
      setStateError(outcome.text);
    } finally { setChangingState(false); }
  };

  const commands = selected ? allowedClassCommands(selected.state) : [];

  return (
    <div className="s2l-page s2l-data-page manager-business-page">
      <PageHeading
        eyebrow="School Manager · BE1"
        title="Lớp học"
        description="Danh sách lớp trong organization đã xác minh."
        action={<button type="button" className="manager-business-button" onClick={() => void refresh()} disabled={loading || changingState}><RefreshCw size={16} aria-hidden="true" />Làm mới từ BE1</button>}
      />

      <section className="manager-business-card cozy-form-card cozy-form-card--wide manager-business-create-class" aria-labelledby="create-class-heading">
        <div>
          <h2 id="create-class-heading">Tạo lớp</h2>
          <p className="manager-business-subtle">Nhập tên lớp. Nếu kết quả gửi chưa rõ, hãy gửi lại cùng yêu cầu để tránh tạo trùng.</p>
        </div>
        <form className="cozy-form-stack" onSubmit={(event) => { event.preventDefault(); void createClass(); }}>
          {error && <Alert role="alert" tone="danger">{error}</Alert>}
          <div className="cozy-form-grid">
            <FormField
              className="cozy-span-4"
              label="Tên lớp"
              htmlFor="manager-class-name"
              required
              help="API tạo lớp hiện chưa kiểm tra giới hạn sức chứa (SRS FR-T-03); hãy tự kiểm tra sức chứa trước khi tạo lớp."
            >
              <input id="manager-class-name" className="cozy-input" value={displayName} onChange={(event) => setDisplayName(event.target.value)} maxLength={200} required disabled={creating} />
            </FormField>
            <div className="cozy-form-actions cozy-span-2 cozy-form-inline-action" style={{ marginTop: 0 }}>
              <Button type="submit" variant="primary" loading={creating} disabled={creating || !displayName.trim()}>
                {creating ? "Đang tạo…" : retryName !== null && retryName === displayName.trim() ? "Gửi lại cùng yêu cầu" : "Tạo lớp"}
              </Button>
            </div>
          </div>
          {!creating && !displayName.trim() && (
            <p className="cozy-form-disabled-hint">Nhập tên lớp để bật nút tạo lớp.</p>
          )}
        </form>
      </section>
      {notice && <div role="status" className="manager-business-subtle">{notice}</div>}

      <section className="s2l-data-grid" aria-label="Lớp học trong phạm vi được cấp quyền">
        <div className="s2l-data-card cozy-form-stack">
          <div className="manager-business-card-head-row">
            <h2>Danh sách lớp</h2>
            <FormField label="Trạng thái lớp" htmlFor="manager-class-filter" className="manager-business-filter-inline">
              <Select id="manager-class-filter" aria-label="Trạng thái lớp" value={filter} disabled={loading || changingState} onChange={(event) => { const next = event.target.value as Be1ClassFilter; setFilter(next); setPendingCommand(null); void refresh(next); }}>
                <option value="all">Tất cả</option>
                <option value="active">Đang hoạt động</option>
                <option value="suspended">Tạm ngưng</option>
                <option value="archived">Đã lưu trữ</option>
              </Select>
            </FormField>
          </div>
          {loading ? <p role="status">Đang tải danh sách lớp…</p> : classes.length === 0 ? <p className="s2l-note">BE1 chưa trả lớp nào cho tài khoản này.</p> : (
            <ul className="s2l-class-list">
              {classes.map((item) => (
                <li key={item.class_id}>
                  <button type="button" onClick={() => { setSelectedId(item.class_id); setPendingCommand(null); }} className={selected?.class_id === item.class_id ? "is-selected" : ""} aria-pressed={selected?.class_id === item.class_id}>
                    <span className="s2l-class-mark"><School size={18} aria-hidden="true" /></span>
                    <span className="s2l-class-copy"><strong>{item.display_name}</strong><small>{item.class_id}</small></span>
                    <span className={"s2l-class-state" + (item.state === "active" ? " is-active" : "")}>{classStateLabel(item.state)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <aside className="s2l-data-card">
          <h2>Thông tin lớp</h2>
          {selected ? (
            <dl className="s2l-class-details">
              <div><dt>Tên lớp</dt><dd>{selected.display_name}</dd></div>
              <div><dt>Mã lớp</dt><dd className="is-mono">{selected.class_id}</dd></div>
              <div><dt>Trạng thái BE1</dt><dd>{classStateLabel(selected.state)}</dd></div>
            </dl>
          ) : <p>Chọn một lớp trong danh sách để xem thông tin BE1 đã trả.</p>}
          {selected?.state === "suspended" && <p className="s2l-note">Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.</p>}
          {selected?.state === "archived" && <p className="s2l-note">Lớp đã lưu trữ: chỉ School Manager còn xem được; không có thao tác khôi phục.</p>}
          {selected && commands.length > 0 && (
            <div className="manager-business-lifecycle">
              {selected.class_revision === undefined ? (
                <p className="manager-business-subtle">Máy chủ chưa trả phiên bản lớp; tạm thời chưa thể đổi trạng thái lớp.</p>
              ) : pendingCommand ? (
                <div className="cozy-form-section cozy-form-stack" role="group" aria-labelledby="class-state-confirm">
                  <p id="class-state-confirm" className="manager-business-subtle" style={{ marginTop: 0 }}>
                    {pendingCommand === "suspend"
                      ? `Tạm ngưng lớp “${selected.display_name}”? Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.`
                      : `Lưu trữ lớp “${selected.display_name}”? Lưu trữ là bước cuối: Teacher không còn thấy lớp, dữ liệu vẫn được giữ và không có thao tác khôi phục.`}
                  </p>
                  {stateError && <Alert role="alert" tone="danger">{stateError}</Alert>}
                  <div className="cozy-form-actions" style={{ marginTop: 0 }}>
                    <Button type="button" variant="secondary" onClick={() => { setPendingCommand(null); setStateError(""); }} disabled={changingState}>Hủy</Button>
                    <Button type="button" variant={pendingCommand === "archive" ? "danger" : "primary"} loading={changingState} onClick={() => void changeState(pendingCommand)} disabled={changingState}>
                      {changingState ? "Đang gửi…" : pendingCommand === "suspend" ? "Xác nhận tạm ngưng" : "Xác nhận lưu trữ"}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="cozy-form-stack">
                  {stateError && <Alert role="alert" tone="danger">{stateError}</Alert>}
                  <div className="cozy-form-actions" style={{ marginTop: 0 }}>
                    {commands.includes("archive") && <Button type="button" variant="danger" className="cozy-form-action-danger" onClick={() => { setPendingCommand("archive"); setStateError(""); }} disabled={changingState || loading}>Lưu trữ lớp</Button>}
                    {commands.includes("suspend") && <Button type="button" variant="secondary" onClick={() => { setPendingCommand("suspend"); setStateError(""); }} disabled={changingState || loading}>Tạm ngưng lớp</Button>}
                  </div>
                </div>
              )}
            </div>
          )}
          <p className="s2l-note">BE1 hiện chưa cung cấp capacity hoặc thao tác khôi phục lớp đã lưu trữ.</p>
        </aside>
      </section>
    </div>
  );
}
