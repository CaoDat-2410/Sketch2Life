import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Icon, IconBadge } from "../components/Icon";

interface ModerationLessonRow {
  id: string;
  title: string;
  version: string;
  owner: string;
  school: string;
  currentScope: "Công khai" | "Trong trường";
  requestedScope: "Công khai";
  status: "Đang công khai" | "Đã ẩn" | "Chờ duyệt";
  updatedAt: string;
  summary: string;
}

const INITIAL_MODERATION_ROWS: ModerationLessonRow[] = [
  {
    id: "mod-1",
    title: "Vòng đời bướm",
    version: "Bản 3",
    owner: "Cô Thảo",
    school: "Trường Mầm non Ánh Dương",
    currentScope: "Công khai",
    requestedScope: "Công khai",
    status: "Đang công khai",
    updatedAt: "30/10/2026",
    summary:
      "Giáo án khám phá vòng đời 4 giai đoạn của bướm kèm 2 hoạt động ngoài sân trường cho trẻ 4–5 tuổi.",
  },
  {
    id: "mod-2",
    title: "Cây xanh quanh em",
    version: "Bản 2",
    owner: "Cô Mai",
    school: "Trường Mầm non Ánh Dương",
    currentScope: "Trong trường",
    requestedScope: "Công khai",
    status: "Đã ẩn",
    updatedAt: "30/10/2026",
    summary:
      "Giáo án quan sát thân cây và tán lá ngoài sân trường, đã tạm ẩn để cập nhật hướng dẫn vật liệu.",
  },
  {
    id: "mod-3",
    title: "Khám phá bầu trời đêm",
    version: "Bản 1",
    owner: "Cô Lan",
    school: "Trường Mầm non Sao Mai",
    currentScope: "Trong trường",
    requestedScope: "Công khai",
    status: "Chờ duyệt",
    updatedAt: "30/10/2026",
    summary:
      "Yêu cầu mở phạm vi Công khai từ Trường Mầm non Sao Mai; phạm vi hiện tại vẫn là Trong trường.",
  },
];

/* A01 — Platform Admin Public-Catalog Content Moderation (a01-content-moderation + UI03 Specimen 3) */
export function A01ContentModerationPage({
  showToast,
}: {
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}) {
  const [rows, setRows] = useState<ModerationLessonRow[]>(INITIAL_MODERATION_ROWS);
  const [selectedId, setSelectedId] = useState("mod-1");
  const [search, setSearch] = useState("");
  const [scopeFilter, setScopeFilter] = useState("Tất cả");
  const [statusFilter, setStatusFilter] = useState("Tất cả");
  const [ownerFilter, setOwnerFilter] = useState("Tất cả");
  const [hideModalTarget, setHideModalTarget] = useState<ModerationLessonRow | null>(null);
  const [hideReason, setHideReason] = useState("");
  const [ui05State, setUi05State] = useState<"normal" | "loading" | "empty" | "conflict">("normal");

  const filtered = rows.filter((r) => {
    const matchText =
      r.title.toLowerCase().includes(search.trim().toLowerCase()) ||
      r.owner.toLowerCase().includes(search.trim().toLowerCase());
    const matchScope = scopeFilter === "Tất cả" || r.currentScope === scopeFilter;
    const matchStatus = statusFilter === "Tất cả" || r.status === statusFilter;
    const matchOwner = ownerFilter === "Tất cả" || r.school === ownerFilter;
    return matchText && matchScope && matchStatus && matchOwner;
  });

  const selectedRow = rows.find((r) => r.id === selectedId) || rows[0];

  const reopenPublic = (id: string) => {
    setRows((prev) =>
      prev.map((r) =>
        r.id === id
          ? { ...r, status: "Đang công khai", currentScope: "Công khai", updatedAt: "30/10/2026" }
          : r
      )
    );
    showToast("Đã mở lại công khai bài học trong thư viện.", "ok");
  };

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div className="row" style={{ gap: 12 }}>
          <IconBadge name="book" tone="primary" size={44} />
          <div>
            <h1>Thư viện bài học</h1>
            <p className="muted small">
              Kiểm duyệt danh mục công khai · Tách biệt phạm vi hiện tại và phạm vi yêu cầu
            </p>
          </div>
        </div>

        {/* UI05 State Switcher inside collapsible details */}
        <details style={{ fontSize: 12 }}>
          <summary
            style={{
              cursor: "pointer",
              fontWeight: 700,
              color: "var(--ink-2)",
              listStyle: "none",
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 12px",
              borderRadius: 999,
              border: "1px solid var(--line)",
              background: "#FFFFFF",
            }}
          >
            <Icon name="settings" size={14} color="var(--ink-3)" /> Trạng thái UI05
          </summary>
          <div
            className="row"
            style={{
              gap: 4,
              background: "#FFFFFF",
              padding: 4,
              borderRadius: 999,
              border: "1px solid var(--line)",
              marginTop: 6,
            }}
          >
            {(
              [
                { id: "normal", label: "Mặc định" },
                { id: "loading", label: "Đang tải" },
                { id: "empty", label: "Trống" },
                { id: "conflict", label: "409" },
              ] as const
            ).map((st) => (
              <button
                key={st.id}
                type="button"
                onClick={() => setUi05State(st.id)}
                style={{
                  border: "none",
                  background: ui05State === st.id ? "var(--primary-50)" : "transparent",
                  color: ui05State === st.id ? "var(--primary)" : "var(--ink-3)",
                  fontWeight: 700,
                  fontSize: 12,
                  padding: "5px 10px",
                  borderRadius: 999,
                  cursor: "pointer",
                }}
              >
                {st.label}
              </button>
            ))}
          </div>
        </details>
      </div>

      {/* UI05 State Previews */}
      {ui05State === "loading" && (
        <div className="card col" style={{ gap: 12 }}>
          <div className="row" style={{ gap: 8 }}>
            <Icon name="refresh" size={16} color="var(--primary)" />
            <span className="muted small" style={{ fontWeight: 700 }}>
              Đang tải danh sách kiểm duyệt...
            </span>
          </div>
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="skeleton"
              style={{ height: 52, borderRadius: 12 }}
            />
          ))}
        </div>
      )}

      {ui05State === "empty" && (
        <div className="card col" style={{ alignItems: "center", textAlign: "center", padding: 32, gap: 10 }}>
          <IconBadge name="book" tone="primary" size={48} />
          <h3>Chưa có bài học trong hàng đợi</h3>
          <p className="small muted">
            Khi các trường gửi yêu cầu mở phạm vi Công khai, bài học sẽ xuất hiện tại đây.
          </p>
          <button type="button" className="btn secondary small" onClick={() => setUi05State("normal")}>
            Quay lại danh sách mẫu
          </button>
        </div>
      )}

      {ui05State === "conflict" && (
        <div
          className="card row"
          style={{
            justifyContent: "space-between",
            background: "var(--warn-50)",
            borderColor: "var(--accent)",
            gap: 12,
          }}
        >
          <div className="row" style={{ gap: 10 }}>
            <Icon name="alert" size={20} color="var(--warn-700)" />
            <div className="col" style={{ gap: 2 }}>
              <h3 style={{ color: "var(--warn-700)", margin: 0 }}>Nội dung vừa được cập nhật</h3>
              <p className="small" style={{ color: "var(--warn-700)" }}>
                Trạng thái kiểm duyệt vừa được cập nhật. Vui lòng tải lại bản mới nhất.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn small"
            onClick={() => {
              setUi05State("normal");
              showToast("Đã tải lại trạng thái mới nhất của thư viện bài học.", "ok");
            }}
          >
            <Icon name="refresh" size={14} color="#FFF" /> Tải lại
          </button>
        </div>
      )}

      {ui05State === "normal" && (
        <>
          {/* Search & 3 Filters: Phạm vi, Trạng thái, Chủ sở hữu */}
          <div className="card row" style={{ gap: 12, flexWrap: "wrap" }}>
            <div className="field" style={{ flex: 2, minWidth: 200 }}>
              <label htmlFor="a01-search">
                <Icon name="search" size={13} color="var(--ink-3)" /> Tìm bài học
              </label>
              <input
                id="a01-search"
                className="input"
                placeholder="Tên bài học hoặc giáo viên..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="field" style={{ flex: 1, minWidth: 140 }}>
              <label htmlFor="a01-scope">Phạm vi</label>
              <select
                id="a01-scope"
                className="input"
                value={scopeFilter}
                onChange={(e) => setScopeFilter(e.target.value)}
              >
                <option value="Tất cả">Tất cả</option>
                <option value="Công khai">Công khai</option>
                <option value="Trong trường">Trong trường</option>
              </select>
            </div>
            <div className="field" style={{ flex: 1, minWidth: 150 }}>
              <label htmlFor="a01-status">Trạng thái</label>
              <select
                id="a01-status"
                className="input"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="Tất cả">Tất cả</option>
                <option value="Đang công khai">Đang công khai</option>
                <option value="Đã ẩn">Đã ẩn</option>
                <option value="Chờ duyệt">Chờ duyệt</option>
              </select>
            </div>
            <div className="field" style={{ flex: 1, minWidth: 180 }}>
              <label htmlFor="a01-owner">Chủ sở hữu</label>
              <select
                id="a01-owner"
                className="input"
                value={ownerFilter}
                onChange={(e) => setOwnerFilter(e.target.value)}
              >
                <option value="Tất cả">Tất cả</option>
                <option value="Trường Mầm non Ánh Dương">Trường Mầm non Ánh Dương</option>
                <option value="Trường Mầm non Sao Mai">Trường Mầm non Sao Mai</option>
              </select>
            </div>
          </div>

          {/* Data Table + Right-Side Detail Panel */}
          <div style={{ display: "grid", gridTemplateColumns: "1.45fr 1fr", gap: 16 }}>
            <div className="card" style={{ padding: 0, overflow: "hidden", alignSelf: "flex-start" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Bài học</th>
                    <th>Chủ sở hữu</th>
                    <th>Hiện tại</th>
                    <th>Yêu cầu</th>
                    <th>Trạng thái</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((row) => {
                    const isSelected = row.id === selectedRow.id;
                    return (
                      <tr
                        key={row.id}
                        onClick={() => setSelectedId(row.id)}
                        style={{
                          cursor: "pointer",
                          background: isSelected ? "var(--primary-50)" : "transparent",
                        }}
                      >
                        <td>
                          <div style={{ fontWeight: 700 }}>
                            {row.title} · {row.version}
                          </div>
                          <div className="tiny muted">{row.updatedAt}</div>
                        </td>
                        <td>
                          <div style={{ fontWeight: 600 }}>{row.owner}</div>
                          <div className="tiny muted">{row.school}</div>
                        </td>
                        <td>
                          <span className="pill">{row.currentScope}</span>
                        </td>
                        <td>
                          <span className="pill warn">{row.requestedScope}</span>
                        </td>
                        <td>
                          <span
                            className={`pill ${
                              row.status === "Đang công khai"
                                ? "ok"
                                : row.status === "Chờ duyệt"
                                ? "warn"
                                : "off"
                            }`}
                            style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                          >
                            <Icon
                              name={
                                row.status === "Đang công khai"
                                  ? "check"
                                  : row.status === "Chờ duyệt"
                                  ? "clock"
                                  : "lock"
                              }
                              size={12}
                            />
                            {row.status}
                          </span>
                        </td>
                        <td onClick={(e) => e.stopPropagation()}>
                          {row.status === "Đang công khai" && (
                            <button
                              type="button"
                              className="btn danger small"
                              onClick={() => {
                                setHideReason("");
                                setHideModalTarget(row);
                              }}
                            >
                              Ẩn khỏi thư viện
                            </button>
                          )}
                          {row.status === "Đã ẩn" && (
                            <button
                              type="button"
                              className="btn secondary small"
                              onClick={() => reopenPublic(row.id)}
                            >
                              Mở lại công khai
                            </button>
                          )}
                          {row.status === "Chờ duyệt" && (
                            <button
                              type="button"
                              className="btn small"
                              onClick={() => reopenPublic(row.id)}
                            >
                              Duyệt công khai
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Right-Side Detail Panel */}
            <div className="card col" style={{ gap: 12, alignSelf: "flex-start" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div className="row" style={{ gap: 10 }}>
                  <IconBadge name="book" tone="primary" size={38} />
                  <div>
                    <h2 style={{ margin: 0 }}>
                      {selectedRow.title} · {selectedRow.version}
                    </h2>
                    <div className="tiny muted">
                      {selectedRow.owner} · {selectedRow.school}
                    </div>
                  </div>
                </div>
                <span
                  className={`pill ${
                    selectedRow.status === "Đang công khai"
                      ? "ok"
                      : selectedRow.status === "Chờ duyệt"
                      ? "warn"
                      : "off"
                  }`}
                >
                  {selectedRow.status}
                </span>
              </div>

              <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
                <span className="pill">Hiện tại: {selectedRow.currentScope}</span>
                <Icon name="arrow-right" size={14} color="var(--ink-3)" />
                <span className="pill warn">Yêu cầu: {selectedRow.requestedScope}</span>
              </div>

              <div className="card col" style={{ background: "var(--bg)", gap: 6, padding: 14 }}>
                <div className="row" style={{ gap: 6 }}>
                  <Icon name="info" size={15} color="var(--primary)" />
                  <h3 style={{ margin: 0 }}>Tóm tắt nội dung</h3>
                </div>
                <p className="small">{selectedRow.summary}</p>
                <p className="tiny muted">Cập nhật: {selectedRow.updatedAt}</p>
              </div>

              {/* State-Specific Action Only */}
              {selectedRow.status === "Đang công khai" && (
                <button
                  type="button"
                  className="btn danger block"
                  onClick={() => {
                    setHideReason("");
                    setHideModalTarget(selectedRow);
                  }}
                >
                  <Icon name="lock" size={16} color="var(--danger)" /> Ẩn khỏi thư viện
                </button>
              )}
              {selectedRow.status === "Đã ẩn" && (
                <button
                  type="button"
                  className="btn block"
                  onClick={() => reopenPublic(selectedRow.id)}
                >
                  <Icon name="refresh" size={16} color="#FFF" /> Mở lại công khai
                </button>
              )}
              {selectedRow.status === "Chờ duyệt" && (
                <button
                  type="button"
                  className="btn block"
                  onClick={() => reopenPublic(selectedRow.id)}
                >
                  <Icon name="check" size={16} color="#FFF" /> Duyệt mở công khai
                </button>
              )}
            </div>
          </div>
        </>
      )}

      {/* UI03 Specimen 3: Quản trị nền tảng · Ẩn bài học công khai (Required reason field) */}
      {hideModalTarget && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
        >
          <div className="card col" style={{ width: 460, padding: 24, gap: 14 }}>
            <div className="row" style={{ gap: 10 }}>
              <IconBadge name="lock" tone="danger" size={40} />
              <div>
                <h2 style={{ margin: 0 }}>Quản trị nền tảng · Ẩn bài học công khai</h2>
                <div className="small muted">
                  {hideModalTarget.title} · {hideModalTarget.version} ({hideModalTarget.school})
                </div>
              </div>
            </div>
            <div className="field">
              <label htmlFor="hide-reason">Lý do ẩn khỏi thư viện công khai (bắt buộc)</label>
              <textarea
                id="hide-reason"
                className="input"
                rows={3}
                placeholder="Nhập lý do kiểm duyệt để ghi vào nhật ký hệ thống..."
                value={hideReason}
                onChange={(e) => setHideReason(e.target.value)}
              />
            </div>
            <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
              <button
                type="button"
                className="btn ghost"
                onClick={() => setHideModalTarget(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className="btn danger"
                disabled={!hideReason.trim()}
                onClick={() => {
                  setRows((prev) =>
                    prev.map((r) =>
                      r.id === hideModalTarget.id
                        ? {
                            ...r,
                            status: "Đã ẩn",
                            currentScope: "Trong trường",
                            updatedAt: "30/10/2026",
                          }
                        : r
                    )
                  );
                  setHideModalTarget(null);
                  showToast("Đã ẩn bài học khỏi thư viện công khai và ghi nhận nhật ký.", "info");
                }}
              >
                <Icon name="lock" size={15} color="var(--danger)" /> Ẩn khỏi thư viện
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* A02 — Platform Admin Operations Dashboard (a02-platform-operations) */
export function A02PlatformOperationsPage({
  showToast,
}: {
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const activePanel = searchParams.get("panel"); // "organizations" | "activities" | "policy" | "audit" | null

  const [catalogItems, setCatalogItems] = useState([
    {
      id: "cat-1",
      title: "Quan sát vòng đời bướm ngoài vườn",
      ageBand: "36–155 tháng (3–12 tuổi)",
      version: "Phiên bản 2 · Đang phát hành",
    },
    {
      id: "cat-2",
      title: "Nhặt lá rụng và phân loại hình dáng lá",
      ageBand: "36–155 tháng (3–12 tuổi)",
      version: "Phiên bản 1 · Đang phát hành",
    },
  ]);

  const [newActivityTitle, setNewActivityTitle] = useState("");

  const highlightStyle = (panelKey: string): React.CSSProperties =>
    activePanel === panelKey
      ? {
          borderColor: "var(--primary)",
          boxShadow: "0 0 0 3px var(--primary-100)",
        }
      : {};

  return (
    <div className="col" style={{ gap: 20 }}>
      {/* Hero Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)",
          borderRadius: 18,
          padding: "20px 24px",
          color: "#FFFFFF",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div className="row" style={{ gap: 12 }}>
          <div
            style={{
              width: 46,
              height: 46,
              borderRadius: 14,
              background: "rgba(255,255,255,0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon name="sun" size={24} color="#FFF" />
          </div>
          <div>
            <h1 style={{ color: "#FFFFFF", margin: 0 }}>Vận hành nền tảng</h1>
            <div style={{ fontSize: 13, opacity: 0.85 }}>
              Tổ chức · Danh mục hoạt động ngoài trời · Chính sách & Nhật ký
            </div>
          </div>
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <button
            type="button"
            className="btn secondary small"
            style={{ background: "rgba(255,255,255,0.16)", borderColor: "rgba(255,255,255,0.3)", color: "#FFF" }}
            onClick={() => {
              navigate("/a02-platform-operations?panel=organizations");
              showToast("Đang mở danh sách các trường/tổ chức trên nền tảng.", "info");
            }}
          >
            <Icon name="users" size={14} color="#FFF" /> Tổ chức
          </button>
          <button
            type="button"
            className="btn secondary small"
            style={{ background: "rgba(255,255,255,0.16)", borderColor: "rgba(255,255,255,0.3)", color: "#FFF" }}
            onClick={() => {
              navigate("/a02-platform-operations?panel=activities");
              showToast("Đang mở danh mục hoạt động ngoài trời toàn cục.", "info");
            }}
          >
            <Icon name="leaf" size={14} color="#FFF" /> Hoạt động
          </button>
          <button
            type="button"
            style={{
              background: "#FFFFFF",
              color: "var(--primary)",
              border: "none",
              borderRadius: 12,
              padding: "8px 16px",
              fontWeight: 800,
              fontSize: 13,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
            onClick={() => {
              navigate("/a02-platform-operations?panel=policy");
              showToast("Đã mở cấu hình chính sách an toàn và hạn mức nền tảng.", "info");
            }}
          >
            <Icon name="lock" size={14} color="var(--primary)" /> Chính sách
          </button>
        </div>
      </div>

      {/* 3 Summary Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 14,
        }}
      >
        <div className="card row" style={{ gap: 12 }}>
          <IconBadge name="users" tone="primary" size={44} />
          <div>
            <div className="tiny muted">Tổ chức</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "var(--primary)" }}>
              12 trường mầm non
            </div>
            <div className="tiny muted">Tách biệt theo từng tổ chức</div>
          </div>
        </div>

        <div className="card row" style={{ gap: 12 }}>
          <IconBadge name="book" tone="mint" size={44} />
          <div>
            <div className="tiny muted">Bài học công khai</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "var(--mint-700)" }}>
              28 bài học
            </div>
            <div className="tiny muted">Đã qua kiểm duyệt 2 cấp</div>
          </div>
        </div>

        <div className="card row" style={{ gap: 12 }}>
          <IconBadge name="leaf" tone="accent" size={44} />
          <div>
            <div className="tiny muted">Hoạt động</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "var(--ink)" }}>
              {catalogItems.length} danh mục chuẩn
            </div>
            <div className="tiny muted">Hoạt động ngoài trời đã phát hành</div>
          </div>
        </div>
      </div>

      {/* 3 Clear Panels */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 16,
        }}
      >
        <div className="card col" style={{ gap: 10, ...highlightStyle("organizations") }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row" style={{ gap: 8 }}>
              <IconBadge name="users" tone="primary" size={36} />
              <h2 style={{ margin: 0 }}>Quản lý tổ chức</h2>
            </div>
            <span className="pill ok">Hoạt động</span>
          </div>
          <div className="card col" style={{ padding: 12, background: "var(--bg)", gap: 4 }}>
            <div style={{ fontWeight: 700 }}>Trường Mầm non Ánh Dương</div>
            <div className="small muted">8/10 slot lớp đang dùng · Gói 10 slot</div>
          </div>
          <div className="card col" style={{ padding: 12, background: "var(--bg)", gap: 4 }}>
            <div style={{ fontWeight: 700 }}>Trường Mầm non Sao Mai</div>
            <div className="small muted">6/10 slot lớp đang dùng · Gói 10 slot</div>
          </div>
          <button
            type="button"
            className="btn secondary small"
            style={{ alignSelf: "flex-start" }}
            onClick={() => navigate("/a01-content-moderation")}
          >
            <Icon name="book" size={14} color="var(--primary)" /> Xem bài học từ các trường
          </button>
        </div>

        <div className="card col" style={{ gap: 10, ...highlightStyle("activities") }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row" style={{ gap: 8 }}>
              <IconBadge name="leaf" tone="mint" size={36} />
              <h2 style={{ margin: 0 }}>Danh mục hoạt động</h2>
            </div>
            <span className="pill">Toàn cục</span>
          </div>
          {catalogItems.map((item) => (
            <div key={item.id} className="card col" style={{ padding: 12, background: "var(--bg)", gap: 4 }}>
              <div style={{ fontWeight: 700 }}>{item.title}</div>
              <div className="small muted">
                {item.ageBand} · {item.version}
              </div>
            </div>
          ))}
          <div className="row" style={{ gap: 6, marginTop: 4 }}>
            <input
              className="input"
              style={{ minHeight: 36, padding: "6px 10px", fontSize: 13 }}
              placeholder="Thêm hoạt động ngoài trời chuẩn..."
              value={newActivityTitle}
              onChange={(e) => setNewActivityTitle(e.target.value)}
            />
            <button
              type="button"
              className="btn secondary small"
              onClick={() => {
                const title = newActivityTitle.trim() || "Quan sát mây và bóng nắng trên sân";
                setCatalogItems((prev) => [
                  ...prev,
                  {
                    id: `cat-${Date.now()}`,
                    title,
                    ageBand: "36–155 tháng (3–12 tuổi)",
                    version: "Phiên bản 1 · Đang phát hành",
                  },
                ]);
                setNewActivityTitle("");
                showToast(`Đã phát hành hoạt động "${title}" vào danh mục toàn cục.`, "ok");
              }}
            >
              <Icon name="plus" size={14} color="var(--primary)" /> Thêm
            </button>
          </div>
        </div>

        <div className="card col" style={{ gap: 10, ...highlightStyle("policy") }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row" style={{ gap: 8 }}>
              <IconBadge name="lock" tone="accent" size={36} />
              <h2 style={{ margin: 0 }}>Chính sách và quota</h2>
            </div>
            <span className="pill ok">Đang áp dụng</span>
          </div>
          <div className="card col" style={{ padding: 12, background: "var(--bg)", gap: 4 }}>
            <div style={{ fontWeight: 700 }}>An toàn nội dung trẻ em</div>
            <div className="small muted">
              Kiểm tra tự động kịch bản, khung hình video, lời kể và phụ đề.
            </div>
          </div>
          <div className="card col" style={{ padding: 12, background: "var(--bg)", gap: 4 }}>
            <div style={{ fontWeight: 700 }}>Quota & giới hạn tốc độ</div>
            <div className="small muted">
              Kỳ tháng dương lịch · Tách biệt Phụ huynh và Tổ chức trường.
            </div>
          </div>
        </div>
      </div>

      {/* Recent Moderation Log */}
      <div className="card col" style={{ gap: 10, ...highlightStyle("audit") }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="clock" tone="primary" size={38} />
            <div>
              <h2 style={{ margin: 0 }}>Nhật ký kiểm duyệt gần đây</h2>
              <div className="tiny muted">Chỉ siêu dữ liệu · Không lưu media trẻ</div>
            </div>
          </div>
          <span className="pill">30/10/2026</span>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Hành động</th>
              <th>Đối tượng</th>
              <th>Kết quả</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>30/10/2026 · 14:20</td>
              <td>Duyệt công khai bài học</td>
              <td>Vòng đời bướm · Bản 3 (Trường Mầm non Ánh Dương)</td>
              <td>
                <span className="pill ok" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Icon name="check" size={12} /> Đang công khai
                </span>
              </td>
            </tr>
            <tr>
              <td>30/10/2026 · 10:05</td>
              <td>Phát hành danh mục hoạt động ngoài trời</td>
              <td>Quan sát vòng đời bướm ngoài vườn · Phiên bản 2</td>
              <td>
                <span className="pill ok" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Icon name="check" size={12} /> Thành công
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
