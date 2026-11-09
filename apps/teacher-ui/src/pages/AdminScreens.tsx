import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { MgIcon } from "../components/MgIcon";
import "../styles/mg-manage.css";

type Toast = (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
type Status = "Đang công khai" | "Chờ duyệt" | "Đã ẩn";
type Scope = "Toàn nền tảng" | "Trong trường";

interface LessonRow {
  id: string;
  title: string;
  version: string;
  owner: string;
  initials: string;
  category: string;
  scope: Scope;
  status: Status;
  updatedAt: string;
  emoji: string;
  bg: string;
}

/* Chỉ metadata — không có ảnh/video do trẻ tạo */
const INITIAL: LessonRow[] = [
  { id: "mod-1", title: "Hệ Mặt Trời", version: "Bản 2", owner: "Trần Minh Anh", initials: "MA", category: "Vũ trụ", scope: "Toàn nền tảng", status: "Đang công khai", updatedAt: "28/10/2026", emoji: "🪐", bg: "#E0E7FF" },
  { id: "mod-2", title: "Cây xanh quanh em", version: "Bản 1", owner: "Nguyễn Hoài Nam", initials: "HN", category: "Thực vật", scope: "Trong trường", status: "Chờ duyệt", updatedAt: "29/10/2026", emoji: "🌱", bg: "#D1FAE5" },
  { id: "mod-3", title: "Vòng đời bướm", version: "Bản 3", owner: "Lê Thu Hà", initials: "TH", category: "Khoa học tự nhiên", scope: "Toàn nền tảng", status: "Đang công khai", updatedAt: "30/10/2026", emoji: "🦋", bg: "#FEF3C7" },
  { id: "mod-4", title: "Đại dương kỳ thú", version: "Bản 1", owner: "Phạm Gia Bảo", initials: "GB", category: "Động vật", scope: "Trong trường", status: "Đang công khai", updatedAt: "27/10/2026", emoji: "🐬", bg: "#DBEAFE" },
  { id: "mod-5", title: "Tái chế rác thải", version: "Bản 2", owner: "Đỗ Quang Huy", initials: "QH", category: "Môi trường", scope: "Toàn nền tảng", status: "Đã ẩn", updatedAt: "25/10/2026", emoji: "♻️", bg: "#F1F5F9" },
  { id: "mod-6", title: "Khủng long thời tiền sử", version: "Bản 1", owner: "Ngô Thùy Linh", initials: "TL", category: "Lịch sử tự nhiên", scope: "Toàn nền tảng", status: "Đang công khai", updatedAt: "21/10/2026", emoji: "🦖", bg: "#FEE2E2" },
  { id: "mod-7", title: "Vòng tuần hoàn nước", version: "Bản 1", owner: "Vũ Đức Tài", initials: "ĐT", category: "Khoa học tự nhiên", scope: "Trong trường", status: "Chờ duyệt", updatedAt: "20/10/2026", emoji: "💧", bg: "#EFF6FF" },
  { id: "mod-8", title: "Cơ thể con người", version: "Bản 1", owner: "Nguyễn Thảo Vy", initials: "TV", category: "Sinh học", scope: "Toàn nền tảng", status: "Đã ẩn", updatedAt: "18/10/2026", emoji: "🫀", bg: "#F5F3FF" },
];

const STATUS_FILTERS: ("Tất cả" | Status)[] = ["Tất cả", "Đang công khai", "Chờ duyệt", "Đã ẩn"];
const SCOPE_FILTERS: ("Tất cả" | Scope)[] = ["Tất cả", "Toàn nền tảng", "Trong trường"];

function StatusPill({ status }: { status: Status }) {
  if (status === "Đang công khai") return <span className="mg-pill ok"><MgIcon name="check" size={13} /> Công khai</span>;
  if (status === "Chờ duyệt") return <span className="mg-pill warn"><MgIcon name="clock" size={13} /> Chờ duyệt</span>;
  return <span className="mg-pill off"><MgIcon name="eyeoff" size={13} /> Đã ẩn</span>;
}

/* ══════════════════════════════════════════════════════════════════
   A01 — Kiểm duyệt nội dung
   ══════════════════════════════════════════════════════════════════ */
export function A01ContentModerationPage({ showToast }: { showToast: Toast }) {
  const navigate = useNavigate();
  const [rows, setRows] = useState<LessonRow[]>(INITIAL);
  const [selectedId, setSelectedId] = useState("mod-3");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"Tất cả" | Status>("Tất cả");
  const [scopeFilter, setScopeFilter] = useState<"Tất cả" | Scope>("Tất cả");
  const [target, setTarget] = useState<LessonRow | null>(null);
  const [reason, setReason] = useState("");

  const q = search.trim().toLowerCase();
  const filtered = rows.filter(
    (r) =>
      (!q || r.title.toLowerCase().includes(q) || r.owner.toLowerCase().includes(q)) &&
      (statusFilter === "Tất cả" || r.status === statusFilter) &&
      (scopeFilter === "Tất cả" || r.scope === scopeFilter)
  );
  const selected = rows.find((r) => r.id === selectedId) ?? rows[0];

  const confirm = () => {
    if (!target) return;
    const reopening = target.status === "Đã ẩn";
    if (!reopening && !reason.trim()) {
      showToast("Hãy nhập lý do ẩn bài học.", "warn");
      return;
    }
    const next: Status = reopening ? "Đang công khai" : "Đã ẩn";
    setRows((p) => p.map((r) => (r.id === target.id ? { ...r, status: next } : r)));
    showToast(reopening ? "Đã hiện lại bài học." : "Đã ẩn bài học khỏi thư viện.", "ok");
    setTarget(null);
    setReason("");
  };

  return (
    <div className="mg-page">
      <div className="mg-hero">
        <div className="mg-hero-left">
          <span className="mg-hero-badge" aria-hidden="true">
            <MgIcon name="book" size={30} />
          </span>
          <div>
            <h1 className="mg-title">Thư viện bài học toàn nền tảng</h1>
            <div className="mg-sub">Kiểm duyệt phạm vi hiển thị, ẩn hoặc mở lại các giáo án đã phát hành</div>
          </div>
        </div>
        <div className="mg-hero-pills">
          <span className="mg-pill ok"><MgIcon name="check" size={13} /> Công khai: {rows.filter((r) => r.status === "Đang công khai").length}</span>
          <span className="mg-pill warn"><MgIcon name="clock" size={13} /> Chờ duyệt: {rows.filter((r) => r.status === "Chờ duyệt").length}</span>
          <span className="mg-pill off"><MgIcon name="eyeoff" size={13} /> Đã ẩn: {rows.filter((r) => r.status === "Đã ẩn").length}</span>
          <button type="button" className="mg-btn sm soft" onClick={() => navigate("/a02-platform-operations")}>
            <MgIcon name="shield" size={15} /> Về vận hành
          </button>
        </div>
      </div>

      <div className="mg-filters">
        <div style={{ position: "relative", flex: "1 1 260px", maxWidth: 360 }}>
          <span style={{ position: "absolute", left: 14, top: 12, color: "#94A3B8" }}><MgIcon name="search" size={20} /></span>
          <input className="mg-input" style={{ paddingLeft: 44 }} aria-label="Tìm bài học" placeholder="Tìm bài học, tác giả" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {STATUS_FILTERS.map((s) => (
          <button key={s} type="button" className={`mg-chip-btn${statusFilter === s ? " is-active" : ""}`} aria-pressed={statusFilter === s} onClick={() => setStatusFilter(s)}>{s}</button>
        ))}
        <span style={{ width: 1, height: 24, background: "#CBD5E1" }} />
        {SCOPE_FILTERS.map((s) => (
          <button key={s} type="button" className={`mg-chip-btn${scopeFilter === s ? " is-active" : ""}`} aria-pressed={scopeFilter === s} onClick={() => setScopeFilter(s)}>{s}</button>
        ))}
      </div>

      <div className="mg-grid-split" style={{ gridTemplateColumns: "2fr minmax(300px, 1fr)" }}>
        <section className="mg-card">
          <div className="mg-table-wrap">
            <table className="mg-table">
              <thead><tr><th>Bài học</th><th>Chủ sở hữu</th><th>Phạm vi</th><th>Trạng thái</th><th>Cập nhật</th></tr></thead>
              <tbody>
                {filtered.map((r) => (
                  <tr
                    key={r.id}
                    className={`is-clickable${r.id === selected.id ? " is-active" : ""}`}
                    tabIndex={0}
                    onClick={() => setSelectedId(r.id)}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSelectedId(r.id); } }}
                  >
                    <td>
                      <div className="mg-cell">
                        <span className="mg-thumb" style={{ width: 40, height: 40, background: r.bg, fontSize: 20, borderRadius: 12 }}>{r.emoji}</span>
                        <span>{r.title}<div className="mg-item-sub">{r.version}</div></span>
                      </div>
                    </td>
                    <td><div className="mg-cell"><span className="mg-avatar" style={{ width: 28, height: 28, background: "#DBEAFE", color: "#1D4ED8", fontSize: 11 }}>{r.initials}</span><span style={{ fontWeight: 600 }}>{r.owner}</span></div></td>
                    <td><span className={`mg-pill ${r.scope === "Toàn nền tảng" ? "info" : "off"}`}><MgIcon name={r.scope === "Toàn nền tảng" ? "globe" : "school"} size={13} /> {r.scope}</span></td>
                    <td><StatusPill status={r.status} /></td>
                    <td className="mg-item-sub">{r.updatedAt}</td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={5} style={{ textAlign: "center", color: "#64748B" }}>Không có bài phù hợp</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mg-item-sub">Hiển thị {filtered.length}/{rows.length} bài</div>
        </section>

        <aside className="mg-card" aria-label="Chi tiết bài học">
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span className="mg-thumb" style={{ width: 64, height: 64, background: selected.bg, fontSize: 32 }}>{selected.emoji}</span>
            <div className="mg-grow">
              <h2 className="mg-card-title" style={{ fontSize: 19 }}>{selected.title}</h2>
              <div className="mg-item-sub">{selected.version}</div>
            </div>
            <StatusPill status={selected.status} />
          </div>
          <div className="mg-meta">
            <div className="mg-meta-row"><span>Chủ sở hữu</span><span>{selected.owner}</span></div>
            <div className="mg-meta-row"><span>Danh mục</span><span>{selected.category}</span></div>
            <div className="mg-meta-row"><span>Phạm vi</span><span>{selected.scope}</span></div>
            <div className="mg-meta-row"><span>Cập nhật</span><span>{selected.updatedAt}</span></div>
          </div>
          <div className="mg-privacy">
            <MgIcon name="lock" size={18} />
            Chỉ xem thông tin. Ảnh, video của trẻ được ẩn.
          </div>
          {selected.status === "Đã ẩn" ? (
            <button type="button" className="mg-btn mint block" onClick={() => setTarget(selected)}>
              <MgIcon name="eye" size={18} /> Hiện lại
            </button>
          ) : (
            <button type="button" className="mg-btn rose block" onClick={() => setTarget(selected)}>
              <MgIcon name="eyeoff" size={18} /> Ẩn khỏi thư viện
            </button>
          )}
        </aside>
      </div>

      {target && (
        <div className="mg-modal-bg" onClick={() => setTarget(null)}>
          <div className="mg-modal" role="dialog" aria-modal="true" aria-label="Xác nhận" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span className={`mg-ico-chip ${target.status === "Đã ẩn" ? "mg-tone-mint" : "mg-tone-rose"}`}>
                <MgIcon name={target.status === "Đã ẩn" ? "eye" : "eyeoff"} size={22} />
              </span>
              <h2 className="mg-card-title">{target.status === "Đã ẩn" ? "Hiện lại bài học?" : "Ẩn bài học?"}</h2>
            </div>
            <div className="mg-item-title">{target.title} · {target.version}</div>
            {target.status !== "Đã ẩn" && (
              <textarea className="mg-textarea" aria-label="Lý do ẩn" placeholder="Lý do ẩn" value={reason} onChange={(e) => setReason(e.target.value)} />
            )}
            <div className="mg-actions">
              <button type="button" className="mg-btn soft" onClick={() => { setTarget(null); setReason(""); }}>Hủy</button>
              <button type="button" className={`mg-btn ${target.status === "Đã ẩn" ? "mint" : "rose"}`} onClick={confirm}>Xác nhận</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════
   A02 — Vận hành nền tảng
   ══════════════════════════════════════════════════════════════════ */
const AUDIT = [
  { time: "30/10/2026 10:24", who: "Nguyễn Thị Mai", initials: "TM", action: "Duyệt tổ chức", target: "Trường Tiểu học Ánh Dương" },
  { time: "30/10/2026 09:17", who: "Trần Minh Quân", initials: "MQ", action: "Tạo gói dịch vụ", target: "Gói Trường học cơ bản" },
  { time: "29/10/2026 16:40", who: "Nguyễn Thị Mai", initials: "TM", action: "Ẩn bài học", target: "Tái chế rác thải" },
];

export function A02PlatformOperationsPage({ showToast }: { showToast: Toast }) {
  const navigate = useNavigate();
  const location = useLocation();
  const panel = new URLSearchParams(location.search).get("panel");
  const [activities, setActivities] = useState([
    "Quan sát vòng đời bướm ngoài vườn (3–10 tuổi)",
    "Nhặt lá rụng và phân loại hình dáng lá (3–10 tuổi)",
  ]);
  const [newAct, setNewAct] = useState("");

  const showOrgs = panel === "orgs";
  const showCatalog = panel === "catalog";
  const showQuota = panel === "quota";
  const showAudit = panel === "audit";

  const stat = (num: string, label: string, tone: string, icon: Parameters<typeof MgIcon>[0]["name"], msg: string) => (
    <button type="button" className="mg-stat-row" onClick={() => showToast(msg, "info")}>
      <span className={`mg-ico-chip sm ${tone}`}><MgIcon name={icon} size={18} /></span>
      <span className="mg-stat-num">{num}</span>
      <span className="mg-stat-label mg-grow">{label}</span>
      <MgIcon name="chevron" size={16} color="#94A3B8" />
    </button>
  );

  return (
    <div className="mg-page">
      <div className="mg-hero">
        <div className="mg-hero-left">
          <span className="mg-hero-badge" aria-hidden="true">
            <MgIcon name="shield" size={30} />
          </span>
          <div>
            <h1 className="mg-title">Vận hành nền tảng</h1>
            <div className="mg-sub">Tổ chức, nội dung, chính sách</div>
          </div>
        </div>
      </div>

      {!panel && (
        <section className="mg-card">
          <div className="mg-card-head"><h2 className="mg-card-title">Tổng quan nền tảng</h2></div>
          <div className="mg-stack">
            <button type="button" className="mg-stat-row" onClick={() => navigate("/a02-platform-operations?panel=orgs")}>
              <span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="building" size={18} /></span>
              <span className="mg-stat-label mg-grow">Tổ chức trường học</span>
              <span className="mg-pill info">12 trường</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/a01-content-moderation")}>
              <span className="mg-ico-chip sm mg-tone-amber"><MgIcon name="book" size={18} /></span>
              <span className="mg-stat-label mg-grow">Bài học &amp; kiểm duyệt</span>
              <span className="mg-pill info">28 công khai</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/a02-platform-operations?panel=catalog")}>
              <span className="mg-ico-chip sm mg-tone-mint"><MgIcon name="grid" size={18} /></span>
              <span className="mg-stat-label mg-grow">Danh mục hoạt động</span>
              <span className="mg-pill info">{activities.length} mục</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/a02-platform-operations?panel=quota")}>
              <span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="shield" size={18} /></span>
              <span className="mg-stat-label mg-grow">Hạn mức &amp; chính sách</span>
              <span className="mg-pill info">Theo tháng</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/a02-platform-operations?panel=audit")}>
              <span className="mg-ico-chip sm mg-tone-slate"><MgIcon name="doc" size={18} /></span>
              <span className="mg-stat-label mg-grow">Nhật ký gần đây</span>
              <span className="mg-pill info">{AUDIT.length} mục</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
          </div>
        </section>
      )}

      {/* Các panel quản lý */}
      {(showOrgs || showCatalog || showQuota) && (
        <div className={panel ? "mg-page" : "mg-grid-3"}>
          {showOrgs && (
            <section className="mg-card">
              <div className="mg-card-head">
                <h2 className="mg-card-title"><span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="building" size={18} /></span>Quản lý tổ chức</h2>
                <span className="mg-pill ok">Hoạt động</span>
              </div>
              <div className="mg-stack">
                {stat("8/10", "Trường Mầm non Ánh Dương (Gói 10 slot)", "mg-tone-blue", "school", "Trường Mầm non Ánh Dương đang dùng 8/10 slot lớp.")}
                {stat("6/10", "Trường Mầm non Sao Mai (Gói 10 slot)", "mg-tone-mint", "school", "Trường Mầm non Sao Mai đang dùng 6/10 slot lớp.")}
              </div>
              <button type="button" className="mg-btn soft block" onClick={() => navigate("/a01-content-moderation")}>
                <MgIcon name="book" size={18} /> Xem bài học từ các trường
              </button>
            </section>
          )}

          {showCatalog && (
            <section className="mg-card">
              <div className="mg-card-head">
                <h2 className="mg-card-title"><span className="mg-ico-chip sm mg-tone-mint"><MgIcon name="grid" size={18} /></span>Danh mục hoạt động</h2>
                <span className="mg-pill info">Toàn cục</span>
              </div>
              <div className="mg-stack">
                {activities.map((act) => (
                  <div key={act} className="mg-meta-row">
                    <span style={{ color: "#0F172A", fontWeight: 700 }}>{act}</span>
                    <span className="mg-pill ok">Đang phát hành</span>
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  className="mg-input"
                  placeholder="Thêm hoạt động ngoài trời chuẩn"
                  aria-label="Tên hoạt động ngoài trời"
                  value={newAct}
                  onChange={(e) => setNewAct(e.target.value)}
                />
                <button
                  type="button"
                  className="mg-btn sm primary"
                  onClick={() => {
                    if (!newAct.trim()) {
                      showToast("Hãy nhập tên hoạt động trước khi thêm.", "warn");
                      return;
                    }
                    setActivities((p) => [...p, newAct.trim()]);
                    setNewAct("");
                    showToast("Đã phát hành hoạt động mới vào danh mục chuẩn.", "ok");
                  }}
                >
                  <MgIcon name="plus" size={15} /> Thêm
                </button>
              </div>
            </section>
          )}

          {showQuota && (
            <section className="mg-card">
              <div className="mg-card-head">
                <h2 className="mg-card-title"><span className="mg-ico-chip sm mg-tone-amber"><MgIcon name="shield" size={18} /></span>Chính sách &amp; quota</h2>
                <span className="mg-pill ok">Đang áp dụng</span>
              </div>
              <div className="mg-stack">
                <div className="mg-meta-row"><span>Kiểm duyệt nội dung</span><span className="mg-pill info">Trước khi công khai</span></div>
                {stat("Tháng", "Quota tách biệt Phụ huynh và Tổ chức trường", "mg-tone-amber", "clock", "Kỳ quota tính theo tháng dương lịch.")}
              </div>
              <div className="mg-privacy">
                <MgIcon name="lock" size={18} />
                Quản trị viên không xem tranh, giọng nói hay video của trẻ.
              </div>
            </section>
          )}
        </div>
      )}

      {/* Nhật ký */}
      {showAudit && (
        <section className="mg-card">
          <div className="mg-card-head">
            <h2 className="mg-card-title"><span className="mg-ico-chip sm mg-tone-slate"><MgIcon name="doc" size={18} /></span>Nhật ký kiểm duyệt gần đây</h2>
            <span className="mg-pill off">Chỉ siêu dữ liệu, không lưu media trẻ</span>
          </div>
          <div className="mg-table-wrap">
            <table className="mg-table">
              <thead><tr><th>Thời gian</th><th>Người thực hiện</th><th>Hành động</th><th>Đối tượng</th><th>Kết quả</th></tr></thead>
              <tbody>
                {AUDIT.map((a) => (
                  <tr key={a.time + a.action}>
                    <td className="mg-item-sub">{a.time}</td>
                    <td><div className="mg-cell"><span className="mg-avatar" style={{ width: 28, height: 28, background: "#DBEAFE", color: "#1D4ED8", fontSize: 11 }}>{a.initials}</span>{a.who}</div></td>
                    <td>{a.action}</td>
                    <td>{a.target}</td>
                    <td><span className="mg-pill ok"><MgIcon name="check" size={13} /> Thành công</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
