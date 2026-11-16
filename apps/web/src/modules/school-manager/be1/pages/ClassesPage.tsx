import { useEffect, useState, type FormEvent } from "react";
import { Plus, RefreshCw, School } from "lucide-react";
import { classService, type Be1Class } from "../services/classService";
import { PageHeading } from "../../../../shared/FeatureAvailability";

export function ClassesPage() {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const selected = classes.find((item) => item.class_id === selectedId) ?? classes[0];

  const refresh = async () => {
    setError("");
    setLoading(true);
    try {
      const items = await classService.listClasses();
      setClasses(items);
      setSelectedId((current) => items.some((item) => item.class_id === current) ? current : items[0]?.class_id ?? "");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được danh sách lớp từ BE1.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void refresh(); }, []);

  const createClass = async (event: FormEvent) => {
    event.preventDefault();
    const name = displayName.trim();
    if (!name) return;
    setCreating(true);
    setError("");
    try {
      const created = await classService.createClass(name);
      setDisplayName("");
      await refresh();
      setSelectedId(created.class_id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "BE1 chưa tạo được lớp.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading
        eyebrow="School Manager · BE1"
        title="Lớp học"
        description="Danh sách và tạo lớp dùng API được cấp quyền theo tài khoản school_admin."
        action={<button type="button" className="s2l-button" onClick={() => void refresh()} disabled={loading}><RefreshCw size={16} aria-hidden="true" />Làm mới từ BE1</button>}
      />

      {error && <div role="alert" className="s2l-alert">{error}</div>}

      <form onSubmit={(event) => void createClass(event)} className="s2l-create-form">
        <label className="s2l-field" htmlFor="school-class-name">Tên lớp mới
          <input id="school-class-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} maxLength={200} required placeholder="Ví dụ: Lớp Lá 1" />
        </label>
        <button type="submit" disabled={creating || !displayName.trim()} className="s2l-button is-primary"><Plus size={17} aria-hidden="true" />{creating ? "Đang lưu…" : "Tạo lớp trên BE1"}</button>
      </form>

      <section className="s2l-data-grid" aria-label="Lớp học trong phạm vi được cấp quyền">
        <div className="s2l-data-card">
          <h2>Danh sách được cấp quyền</h2>
          {loading ? <p role="status">Đang tải danh sách lớp…</p> : classes.length === 0 ? <p className="s2l-note">BE1 chưa trả lớp nào cho tài khoản này.</p> : (
            <ul className="s2l-class-list">
              {classes.map((item) => (
                <li key={item.class_id}>
                  <button type="button" onClick={() => setSelectedId(item.class_id)} className={selected?.class_id === item.class_id ? "is-selected" : ""} aria-pressed={selected?.class_id === item.class_id}>
                    <span className="s2l-class-mark"><School size={18} aria-hidden="true" /></span>
                    <span className="s2l-class-copy"><strong>{item.display_name}</strong><small>{item.class_id}</small></span>
                    <span className={"s2l-class-state" + (item.state === "active" ? " is-active" : "")}>{item.state}</span>
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
              <div><dt>Trạng thái BE1</dt><dd>{selected.state}</dd></div>
            </dl>
          ) : <p>Chọn một lớp trong danh sách để xem thông tin BE1 đã trả.</p>}
          <p className="s2l-note">API chưa trả nhóm tuổi, giáo viên phụ trách, sĩ số, consent tổng hợp, chỉnh sửa hoặc lưu trữ lớp. Các trường này không được giả lập.</p>
        </aside>
      </section>
    </div>
  );
}
