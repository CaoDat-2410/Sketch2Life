import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { MgIcon } from "../components/MgIcon";
import "../styles/mg-manage.css";

type Toast = (text: string, kind?: "ok" | "info" | "warn" | "err") => void;

/* ══════════════════════════════════════════════════════════════════
   M01 — Duyệt công khai (chỉ metadata, không có ảnh/video của trẻ)
   ══════════════════════════════════════════════════════════════════ */
const PENDING = [
  { id: "rev-1", title: "Vòng đời bướm (Bản 3)", teacher: "Cô Thảo", initials: "CT", timeAgo: "2 giờ trước", emoji: "🦋", bg: "#FEF3C7" },
  { id: "rev-2", title: "Cây xanh quanh em (Bản 1)", teacher: "Cô Lan", initials: "CL", timeAgo: "1 ngày trước", emoji: "🌱", bg: "#D1FAE5" },
  { id: "rev-3", title: "Đại dương kỳ thú (Bản 2)", teacher: "Cô Mai", initials: "CM", timeAgo: "2 ngày trước", emoji: "🐬", bg: "#DBEAFE" },
];

const CRITERIA = [
  "Phù hợp lứa tuổi và an toàn",
  "Kiến thức chính xác",
  "Nội dung có quyền sử dụng hợp lệ",
  "Đạt chất lượng sư phạm",
];

export function M01PublicationReviewPage({ showToast }: { showToast: Toast }) {
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState("rev-1");
  const [tab, setTab] = useState<"CONTENT" | "DIFF">("CONTENT");
  const [publicScope, setPublicScope] = useState(false);
  const [checks, setChecks] = useState([false, false, false, false]);
  const [feedback, setFeedback] = useState("");
  const [done, setDone] = useState<string[]>([]);

  const queue = PENDING.filter((p) => !done.includes(p.id));
  const lesson = queue.find((l) => l.id === selectedId) ?? queue[0];
  const doneCount = checks.filter(Boolean).length;
  const ready = doneCount === 4 && publicScope;

  const resetForm = () => {
    setChecks([false, false, false, false]);
    setFeedback("");
    setPublicScope(false);
  };

  const select = (id: string) => {
    setSelectedId(id);
    resetForm();
  };

  const finish = (id: string) => {
    const rest = queue.filter((q) => q.id !== id);
    setDone((d) => [...d, id]);
    if (rest[0]) setSelectedId(rest[0].id);
    resetForm();
  };

  const approve = () => {
    if (!lesson) return;
    if (!ready) {
      showToast("Hãy chọn phạm vi Công khai và tích đủ 4 tiêu chí.", "warn");
      return;
    }
    showToast(`Đã duyệt công khai "${lesson.title}".`, "ok");
    finish(lesson.id);
  };

  const reject = () => {
    if (!lesson) return;
    showToast(`Đã gửi yêu cầu chỉnh sửa cho ${lesson.teacher}.`, "info");
    finish(lesson.id);
  };

  return (
    <div className="mg-page">
      <div className="mg-hero">
        <div className="mg-hero-left">
          <span className="mg-hero-badge mint" aria-hidden="true">
            <MgIcon name="check" size={30} />
          </span>
          <div>
            <h1 className="mg-title">Duyệt giáo án công khai</h1>
            <div className="mg-sub">Kiểm tra 4 tiêu chí sư phạm trước khi phát hành cho toàn trường</div>
          </div>
        </div>
        <div className="mg-hero-pills">
          <span className="mg-pill warn"><MgIcon name="clock" size={13} /> Chờ duyệt: {queue.length}</span>
          <span className="mg-pill ok"><MgIcon name="check" size={13} /> Đã duyệt: {done.length}</span>
          <button type="button" className="mg-btn sm soft" onClick={() => navigate("/m02-organization-management")}>
            <MgIcon name="school" size={15} /> Về tổng quan trường
          </button>
        </div>
      </div>

      <div className="mg-grid-split">
        {/* Hàng đợi */}
        <section className="mg-card" aria-label="Hàng đợi chờ duyệt">
          <div className="mg-card-head">
            <h2 className="mg-card-title">
              <span className="mg-ico-chip sm mg-tone-amber"><MgIcon name="clock" size={18} /></span>
              Chờ duyệt
            </h2>
            <span className="mg-pill warn">{queue.length}</span>
          </div>
          <div className="mg-list">
            {queue.length === 0 && (
              <div className="mg-item" style={{ cursor: "default", justifyContent: "center" }}>
                <span className="mg-pill ok"><MgIcon name="check" size={14} /> Đã duyệt hết</span>
              </div>
            )}
            {queue.map((q) => (
              <button
                key={q.id}
                type="button"
                className={`mg-item${lesson?.id === q.id ? " is-active" : ""}`}
                onClick={() => select(q.id)}
                aria-pressed={lesson?.id === q.id}
              >
                <span className="mg-thumb" style={{ width: 48, height: 48, background: q.bg, fontSize: 24 }}>{q.emoji}</span>
                <span className="mg-grow">
                  <div className="mg-item-title">{q.title}</div>
                  <div className="mg-item-sub">{q.teacher} · {q.timeAgo}</div>
                </span>
                <span className="mg-pill warn"><MgIcon name="clock" size={13} /> Chờ</span>
              </button>
            ))}
          </div>
        </section>

        {/* Chi tiết */}
        {lesson ? (
          <section className="mg-card" aria-label="Chi tiết bài học">
            <div className="mg-row" style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span className="mg-thumb" style={{ width: 64, height: 64, background: lesson.bg, fontSize: 32 }}>{lesson.emoji}</span>
              <div className="mg-grow">
                <h2 className="mg-card-title" style={{ fontSize: 20 }}>{lesson.title}</h2>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 6, flexWrap: "wrap" }}>
                  <span className="mg-avatar" style={{ width: 28, height: 28, background: "#DBEAFE", color: "#1D4ED8", fontSize: 11 }}>{lesson.initials}</span>
                  <span className="mg-item-sub" style={{ fontWeight: 700 }}>{lesson.teacher}</span>
                  <span className="mg-pill warn"><MgIcon name="clock" size={13} /> Chờ duyệt</span>
                </div>
              </div>
            </div>

            <div className="mg-tabs" role="tablist">
              <button type="button" role="tab" aria-selected={tab === "CONTENT"} className={`mg-tab${tab === "CONTENT" ? " is-active" : ""}`} onClick={() => setTab("CONTENT")}>Nội dung</button>
              <button type="button" role="tab" aria-selected={tab === "DIFF"} className={`mg-tab${tab === "DIFF" ? " is-active" : ""}`} onClick={() => setTab("DIFF")}>So sánh phiên bản</button>
            </div>

            {tab === "DIFF" && (
              <div className="mg-meta">
                <div className="mg-meta-row"><span>Bản trước</span><span>Bản 2</span></div>
                <div className="mg-meta-row"><span>Bản đề nghị</span><span>Bản 3</span></div>
                <div className="mg-meta-row"><span>Thay đổi</span><span className="mg-pill info">3 cảnh</span></div>
              </div>
            )}

            {/* Phạm vi */}
            <div className="mg-scope">
              <div className="mg-scope-box from">
                <MgIcon name="school" size={24} />
                <div>
                  <div className="mg-scope-hint">Hiện tại</div>
                  <div className="mg-scope-name">Trong trường</div>
                </div>
              </div>
              <MgIcon name="arrow" size={20} color="#94A3B8" />
              <button
                type="button"
                className={`mg-scope-box to${publicScope ? " is-on" : ""}`}
                onClick={() => setPublicScope((v) => !v)}
                aria-pressed={publicScope}
              >
                <MgIcon name="globe" size={24} />
                <div>
                  <div className="mg-scope-hint">{publicScope ? "Đã chọn" : "Chạm để chọn"}</div>
                  <div className="mg-scope-name">Công khai</div>
                </div>
              </button>
            </div>

            {/* Tiêu chí */}
            <div className="mg-card-head">
              <strong style={{ fontSize: 15 }}>Tiêu chí</strong>
              <span className={`mg-pill ${doneCount === 4 ? "ok" : "off"}`}>{doneCount}/4</span>
            </div>
            <div className="mg-bar" aria-hidden="true"><span className="mint" style={{ width: `${(doneCount / 4) * 100}%` }} /></div>
            <div className="mg-list" style={{ gap: 8 }}>
              {CRITERIA.map((c, i) => (
                <button
                  key={c}
                  type="button"
                  className={`mg-check${checks[i] ? " is-on" : ""}`}
                  aria-pressed={checks[i]}
                  onClick={() => setChecks((p) => p.map((v, k) => (k === i ? !v : v)))}
                >
                  <span className="mg-check-box"><MgIcon name="check" size={15} /></span>
                  {c}
                </button>
              ))}
            </div>

            <div>
              <textarea
                className="mg-textarea"
                aria-label="Phản hồi cho giáo viên"
                placeholder="Phản hồi cho giáo viên (tùy chọn)"
                maxLength={500}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
              />
              <div className="mg-item-sub" style={{ textAlign: "right" }}>{feedback.length}/500</div>
            </div>

            <div className="mg-privacy">
              <MgIcon name="lock" size={18} />
              Chỉ xem thông tin bài học. Ảnh, video của trẻ được ẩn.
            </div>

            <div className="mg-actions">
              <button type="button" className="mg-btn soft" onClick={reject}>
                <MgIcon name="pencil" size={18} /> Yêu cầu chỉnh sửa
              </button>
              <button type="button" className="mg-btn mint" disabled={!ready} onClick={approve}>
                <MgIcon name="check" size={18} /> Duyệt công khai
              </button>
            </div>
          </section>
        ) : (
          <section className="mg-card" style={{ alignItems: "center", padding: 48 }}>
            <span className="mg-ico-chip mg-tone-mint"><MgIcon name="check" size={24} /></span>
            <strong>Không còn bài chờ duyệt</strong>
          </section>
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════
   M02 — Quản lý trường
   ══════════════════════════════════════════════════════════════════ */
const TEACHERS = [
  { id: "t1", name: "Cô Thảo", role: "Giáo viên", initials: "CT", bg: "#DBEAFE", fg: "#1D4ED8" },
  { id: "t2", name: "Cô Mai", role: "Giáo viên", initials: "CM", bg: "#FEF3C7", fg: "#92400E" },
];

const PARENT_GROUPS = [
  { id: "pg1", name: "Phụ huynh Mầm 2", count: 18, cls: "Lớp Mầm 2", tone: "mg-tone-rose" },
  { id: "pg2", name: "Phụ huynh Mầm 1", count: 24, cls: "Lớp Mầm 1", tone: "mg-tone-blue" },
];

const CLASSES = [
  { id: "c1", name: "Lớp Mầm 2", level: "Mẫu giáo", teacher: "Cô Thảo", slot: "Sáng (08:00–11:00)", parents: 18, tone: "mg-tone-rose" },
  { id: "c2", name: "Lớp Mầm 1", level: "Mẫu giáo", teacher: "Cô Mai", slot: "Sáng (08:00–11:00)", parents: 24, tone: "mg-tone-blue" },
];

const ActivePill = () => (
  <span className="mg-pill ok"><MgIcon name="check" size={13} /> Hoạt động</span>
);

export function M02OrganizationManagementPage({ showToast }: { showToast: Toast }) {
  const location = useLocation();
  const navigate = useNavigate();
  const section = new URLSearchParams(location.search).get("section");
  const [extraSlots, setExtraSlots] = useState(0);
  const [extraQuota, setExtraQuota] = useState(0);
  const [autoRenew, setAutoRenew] = useState(true);

  const usedSlots = 8;
  const totalSlots = 10 + extraSlots;
  const quotaLeft = 86 + extraQuota;
  const quotaTotal = 100 + extraQuota;

  const showTeachers = section === "teachers";
  const showClasses = section === "classes";
  const showQuota = section === "quota";
  const showSettings = section === "settings";

  return (
    <div className="mg-page">
      <div className="mg-hero">
        <div className="mg-hero-left">
          <span className="mg-hero-badge" aria-hidden="true">
            <MgIcon name="school" size={30} />
          </span>
          <div>
            <h1 className="mg-title">Quản lý trường</h1>
            <div className="mg-sub">Mầm non Ánh Dương</div>
          </div>
        </div>
      </div>

      {!section && (
        <section className="mg-card">
          <div className="mg-card-head"><h2 className="mg-card-title">Quản lý trường</h2></div>
          <div className="mg-stack">
            <button type="button" className="mg-stat-row" onClick={() => navigate("/m02-organization-management?section=teachers")}>
              <span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="users" size={18} /></span>
              <span className="mg-stat-label mg-grow">Giáo viên &amp; nhóm phụ huynh</span>
              <span className="mg-pill info">{TEACHERS.length} GV · {PARENT_GROUPS.length} nhóm</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/m02-organization-management?section=classes")}>
              <span className="mg-ico-chip sm mg-tone-mint"><MgIcon name="school" size={18} /></span>
              <span className="mg-stat-label mg-grow">Lớp &amp; sức chứa</span>
              <span className="mg-pill info">{CLASSES.length} lớp · {usedSlots}/{totalSlots} suất</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/m02-organization-management?section=quota")}>
              <span className="mg-ico-chip sm mg-tone-amber"><MgIcon name="play" size={18} /></span>
              <span className="mg-stat-label mg-grow">Lượt tạo video</span>
              <span className="mg-pill info">{quotaLeft} lượt còn</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
            <button type="button" className="mg-stat-row" onClick={() => navigate("/m02-organization-management?section=settings")}>
              <span className="mg-ico-chip sm mg-tone-slate"><MgIcon name="gear" size={18} /></span>
              <span className="mg-stat-label mg-grow">Gói trường &amp; quyền riêng tư</span>
              <MgIcon name="chevron" size={16} color="#94A3B8" />
            </button>
          </div>
        </section>
      )}

      {showQuota && (
        <div className="mg-grid-2">
          <div className="mg-kpi blue">
            <div className="mg-kpi-row">
              <span className="mg-ico-chip mg-tone-blue"><MgIcon name="school" size={24} /></span>
              <div className="mg-grow">
                <div className="mg-kpi-num blue">{usedSlots}/{totalSlots}</div>
                <div className="mg-kpi-label">lớp đang dùng trong gói trường</div>
              </div>
              <button
                type="button"
                className="mg-btn sm soft"
                onClick={() => {
                  setExtraSlots((s) => s + 1);
                  showToast("Đã mua thêm 1 slot lớp qua cổng thanh toán.", "ok");
                }}
              >
                <MgIcon name="plus" size={15} /> Mua thêm slot
              </button>
            </div>
            <div className="mg-bar" role="progressbar" aria-valuenow={usedSlots} aria-valuemin={0} aria-valuemax={totalSlots} aria-label="Lớp đang dùng">
              <span className="blue" style={{ width: `${Math.min(100, (usedSlots / totalSlots) * 100)}%` }} />
            </div>
          </div>

          <div className="mg-kpi mint">
            <div className="mg-kpi-row">
              <span className="mg-ico-chip mg-tone-mint"><MgIcon name="play" size={22} /></span>
              <div className="mg-grow">
                <div className="mg-kpi-num mint">{quotaLeft}</div>
                <div className="mg-kpi-label">lượt tạo video mẫu còn lại trong tháng</div>
              </div>
              <button
                type="button"
                className="mg-btn sm mint"
                onClick={() => {
                  setExtraQuota((q) => q + 10);
                  showToast("Đã nạp thêm 10 lượt tạo video cho trường.", "ok");
                }}
              >
                <MgIcon name="plus" size={15} /> Mua +10 lượt
              </button>
            </div>
            <div className="mg-bar" role="progressbar" aria-valuenow={quotaLeft} aria-valuemin={0} aria-valuemax={quotaTotal} aria-label="Quota còn lại">
              <span className="mint" style={{ width: `${Math.min(100, (quotaLeft / quotaTotal) * 100)}%` }} />
            </div>
          </div>
        </div>
      )}

      {showTeachers && (
        <div className="mg-grid-2">
          <section className="mg-card">
            <div className="mg-card-head">
              <h2 className="mg-card-title">
                <span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="users" size={18} /></span>
                Giáo viên phụ trách <span className="mg-pill info">{TEACHERS.length}</span>
              </h2>
              <button type="button" className="mg-btn sm primary" onClick={() => showToast("Đã gửi email mời giáo viên mới.", "ok")}>
                <MgIcon name="userplus" size={16} /> Mời giáo viên
              </button>
            </div>
            <div className="mg-table-wrap">
              <table className="mg-table">
                <thead><tr><th>Họ tên</th><th>Vai trò</th><th>Trạng thái</th></tr></thead>
                <tbody>
                  {TEACHERS.map((t) => (
                    <tr key={t.id}>
                      <td><div className="mg-cell"><span className="mg-avatar" style={{ background: t.bg, color: t.fg }}>{t.initials}</span>{t.name}</div></td>
                      <td>{t.role}</td>
                      <td><ActivePill /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="mg-card">
            <div className="mg-card-head">
              <h2 className="mg-card-title">
                <span className="mg-ico-chip sm mg-tone-amber"><MgIcon name="users" size={18} /></span>
                Nhóm phụ huynh <span className="mg-pill info">{PARENT_GROUPS.length}</span>
              </h2>
              <button type="button" className="mg-btn sm soft" onClick={() => showToast("Đang đồng bộ danh sách phụ huynh theo lớp.", "info")}>
                <MgIcon name="gear" size={16} /> Đồng bộ
              </button>
            </div>
            <div className="mg-table-wrap">
              <table className="mg-table">
                <thead><tr><th>Nhóm</th><th>Số PH</th><th>Lớp</th></tr></thead>
                <tbody>
                  {PARENT_GROUPS.map((g) => (
                    <tr key={g.id}>
                      <td><div className="mg-cell"><span className={`mg-ico-chip sm ${g.tone}`}><MgIcon name="users" size={16} /></span>{g.name}</div></td>
                      <td><span className="mg-pill off">{g.count}</span></td>
                      <td>{g.cls}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {showClasses && (
        <section className="mg-card">
          <div className="mg-card-head">
            <h2 className="mg-card-title">
              <span className="mg-ico-chip sm mg-tone-mint"><MgIcon name="calendar" size={18} /></span>
              Lớp &amp; slot <span className="mg-pill info">{CLASSES.length}</span>
            </h2>
            <div style={{ display: "flex", gap: 10 }}>
              <button type="button" className="mg-btn sm primary" onClick={() => showToast("Đã mở tạo lớp mới trong hạn mức slot.", "info")}>
                <MgIcon name="plus" size={16} /> Tạo lớp mới
              </button>
              <button type="button" className="mg-btn sm soft" onClick={() => navigate("/m02-organization-management?section=quota")}>
                <MgIcon name="chart" size={16} /> Xem quota
              </button>
            </div>
          </div>
          <div className="mg-table-wrap">
            <table className="mg-table">
              <thead><tr><th>Lớp</th><th>Khối</th><th>Giáo viên</th><th>Khung giờ</th><th>PH</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {CLASSES.map((c) => (
                  <tr key={c.id}>
                    <td><div className="mg-cell"><span className={`mg-ico-chip sm ${c.tone}`}><MgIcon name="school" size={16} /></span>{c.name}</div></td>
                    <td>{c.level}</td>
                    <td>{c.teacher}</td>
                    <td><span className="mg-pill info"><MgIcon name="clock" size={13} /> {c.slot}</span></td>
                    <td>{c.parents}</td>
                    <td><ActivePill /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {showSettings && (
        <section className="mg-card">
          <div className="mg-card-head">
            <h2 className="mg-card-title">
              <span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="gear" size={18} /></span>
              Cài đặt gói trường và quyền riêng tư
            </h2>
            <span className="mg-pill ok">Gói 10 lớp cơ bản</span>
          </div>
          <div className="mg-meta">
            <div className="mg-meta-row">
              <span>Tự động gia hạn gói hàng tháng (MoMo / VNPAY)</span>
              <button
                type="button"
                className={`mg-btn sm ${autoRenew ? "mint" : "soft"}`}
                onClick={() => {
                  setAutoRenew((v) => !v);
                  showToast(autoRenew ? "Đã tắt tự động gia hạn cuối kỳ." : "Đã bật tự động gia hạn.", "info");
                }}
              >
                {autoRenew ? "Đang bật" : "Đang tắt"}
              </button>
            </div>
            <div className="mg-meta-row">
              <span>Quyền xem tranh và video của trẻ</span>
              <span className="mg-pill warn"><MgIcon name="lock" size={13} /> Chỉ giáo viên phụ trách lớp</span>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
