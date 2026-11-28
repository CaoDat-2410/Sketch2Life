import { useState } from "react";
import { BackendApiError } from "../../../shared/api/backendApi";
import { teacherWorkspaceApi, type TeacherPortfolioItem } from "../../../shared/api/teacherWorkspaceApi";

function portfolioError(cause: unknown): string {
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.status === 403) return "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
    if (cause.status === 409 && cause.code === "CONSENT_NOT_EFFECTIVE") return "Hồ sơ chưa đủ điều kiện chia sẻ dữ liệu này.";
    if (cause.status === 400) return "Yêu cầu tải trang hồ sơ không hợp lệ.";
    if (cause.status === 503 || cause.status === 0) return "Chưa thể tải hồ sơ nổi bật. Hãy thử lại sau.";
  }
  return "Chưa thể tải hồ sơ nổi bật. Hãy thử lại sau.";
}

export function TeacherPortfolioCard({ organizationId, classId, childId }: { organizationId: string; classId: string; childId: string }) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<TeacherPortfolioItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (pageCursor?: string) => {
    setLoading(true);
    setError(null);
    try {
      const page = await teacherWorkspaceApi.portfolio(organizationId, classId, childId, { limit: 25, cursor: pageCursor });
      setItems((current) => pageCursor ? [...current, ...page.items] : page.items);
      setNextCursor(page.next_cursor);
      setLoaded(true);
    } catch (cause) {
      setError(portfolioError(cause));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className={"s2l-data-card teacher-portfolio-card" + (open ? " is-open" : "")} aria-label="Hồ sơ nổi bật">
      <button type="button" className="s2l-secondary-link" aria-expanded={open} onClick={() => {
        const next = !open;
        setOpen(next);
        if (next && !loaded && !loading) void load();
      }}>Hồ sơ nổi bật</button>
      {open && <div>
        {loading && <p role="status">Đang tải hồ sơ nổi bật…</p>}
        {error && <p className="s2l-alert" role="alert">{error}</p>}
        {loaded && !loading && !error && items.length === 0 && <p>Chưa có ghi nhận trong hồ sơ nổi bật.</p>}
        {!error && items.map((item) => <article key={item.observation_id} className="s2l-note">
          <strong>{item.kind === "observation" ? "Quan sát" : item.kind === "reflection" ? "Suy ngẫm" : "Đánh giá"}</strong>
          <time dateTime={item.created_at}> · {item.created_at.slice(0, 10)}</time>
          <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{JSON.stringify(item.content, null, 2)}</pre>
        </article>)}
        {!error && nextCursor && <button type="button" className="s2l-button" disabled={loading} onClick={() => void load(nextCursor)}>Tải thêm</button>}
        {loaded && !error && <button type="button" className="s2l-secondary-link" disabled={loading} onClick={() => { setItems([]); setNextCursor(null); setLoaded(false); void load(); }}>Tải lại</button>}
      </div>}
    </section>
  );
}
