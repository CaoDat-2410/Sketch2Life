import { useEffect, useState } from "react";
import { RefreshCw, School } from "lucide-react";
import { classService, type Be1Class } from "../services/classService";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";

export function ClassesPage() {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const selected = classes.find((item) => item.class_id === selectedId) ?? classes[0];

  const refresh = async () => {
    try {
      const items = await classService.listClasses();
      setClasses(items);
      setError("");
      setSelectedId((current) =>
        items.some((item) => item.class_id === current) ? current : items[0]?.class_id ?? "",
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được danh sách lớp từ BE1.");
      setClasses([]);
      setSelectedId("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let current = true;
    classService.listClasses()
      .then((items) => {
        if (!current) return;
        setClasses(items);
        setError("");
        setSelectedId((selectedId) =>
          items.some((item) => item.class_id === selectedId) ? selectedId : items[0]?.class_id ?? "",
        );
      })
      .catch((cause: unknown) => {
        if (!current) return;
        setError(cause instanceof Error ? cause.message : "Không tải được danh sách lớp từ BE1.");
        setClasses([]);
        setSelectedId("");
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => { current = false; };
  }, []);

  return (
    <div className="s2l-page s2l-data-page manager-business-page">
      <PageHeading
        eyebrow="School Manager · BE1"
        title="Lớp học"
        description="Danh sách lớp đọc từ API trong organization đã xác minh."
        action={
          <button type="button" className="manager-business-button" onClick={() => { setLoading(true); setError(""); void refresh(); }} disabled={loading}>
            <RefreshCw size={16} aria-hidden="true" />Làm mới từ BE1
          </button>
        }
      />

      <div className="manager-business-alert" role="status">
        Tạo lớp đang tạm khóa: API hiện chưa kiểm tra giới hạn capacity bắt buộc theo SRS FR-T-03.
      </div>
      {error && <div role="alert" className="manager-business-alert">{error}</div>}

      <section className="s2l-data-grid" aria-label="Lớp học trong phạm vi được cấp quyền">
        <div className="s2l-data-card">
          <h2>Danh sách lớp</h2>
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
          <p className="s2l-note">BE1 hiện chưa cung cấp capacity, Teacher phụ trách hoặc thao tác lưu trữ lớp.</p>
        </aside>
      </section>
    </div>
  );
}
