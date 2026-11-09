import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { MgIcon } from "../components/MgIcon";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  isLocalPreview,
  type AccessGrant,
  type Be1Class,
  type LessonSummary,
} from "../../../shared/backendApi";
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

function ManagerApiReviewPage({ showToast }: { showToast: Toast }) {
  const [grants, setGrants] = useState<AccessGrant[]>([]);
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [checks, setChecks] = useState([false, false, false, false]);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    const organizationId = configuredOrganizationId();
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có Firebase ID token để kiểm tra quyền School Manager.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setError("Chưa cấu hình organization_id cho các API quản lý trường.");
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    setError(null);
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "school_admin")) {
          throw new BackendApiError("Tài khoản không có assignment school_admin trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return Promise.all([
          backendApi.accessGrants(organizationId, { state: "PENDING_REVIEW", audience_kind: "PUBLIC" }),
          backendApi.lessons(organizationId),
        ]);
      })
      .then(([grantPage, lessonPage]) => {
        if (!active) return;
        const pending = grantPage.items.filter((grant) => grant.audience_kind === "PUBLIC" && grant.state === "PENDING_REVIEW");
        setGrants(pending);
        setLessons(lessonPage.items);
        setSelectedId((current) => pending.some((grant) => grant.access_grant_id === current) ? current : pending[0]?.access_grant_id ?? "");
      })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  const selected = grants.find((grant) => grant.access_grant_id === selectedId) ?? grants[0];
  const lesson = selected ? lessons.find((item) => item.lesson_id === selected.lesson_id) : undefined;
  const checkedCount = checks.filter(Boolean).length;

  const decide = async (decision: "APPROVE" | "REQUEST_CHANGES") => {
    if (!selected) return;
    if (decision === "APPROVE" && checkedCount !== CRITERIA.length) {
      showToast("Hãy xác nhận đủ 4 tiêu chí trước khi duyệt.", "warn");
      return;
    }
    if (decision === "REQUEST_CHANGES" && !reason.trim()) {
      showToast("Nhập lý do yêu cầu chỉnh sửa theo hợp đồng API.", "warn");
      return;
    }
    const organizationId = configuredOrganizationId();
    setBusy(true);
    setError(null);
    try {
      await backendApi.decideAccessGrant(organizationId, selected, decision, reason.trim() || undefined);
      showToast(decision === "APPROVE" ? "Đã duyệt yêu cầu công khai." : "Đã gửi yêu cầu chỉnh sửa.", "ok");
      setChecks([false, false, false, false]);
      setReason("");
      setReload((value) => value + 1);
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mg-page">
      <BackendModeNotice roleLabel="Quản lý trường" />
      <div className="mg-hero">
        <div className="mg-hero-left"><span className="mg-hero-badge mint"><MgIcon name="check" size={30} /></span><div><h1 className="mg-title">Duyệt yêu cầu công khai</h1><div className="mg-sub">Chỉ xử lý grant PUBLIC đang chờ duyệt từ API Lesson Library.</div></div></div>
        <div className="mg-hero-pills"><span className="mg-pill warn"><MgIcon name="clock" size={13} /> Chờ duyệt: {grants.length}</span><button type="button" className="mg-btn sm soft" disabled={loading} onClick={() => setReload((value) => value + 1)}><MgIcon name="list" size={15} /> Tải lại</button></div>
      </div>
      {error && <BackendNotice title="Không tải hoặc cập nhật được hàng đợi" tone="error">{error}</BackendNotice>}
      {loading && <BackendNotice title="Đang tải dữ liệu">Đang xác nhận assignment school_admin, grant và metadata giáo án.</BackendNotice>}
      {!loading && !error && grants.length === 0 && <BackendNotice title="Không có yêu cầu công khai đang chờ">API không trả về grant PUBLIC ở trạng thái PENDING_REVIEW.</BackendNotice>}
      {selected && <div className="mg-grid-split">
        <section className="mg-card" aria-label="Yêu cầu đang chờ">
          <div className="mg-card-head"><h2 className="mg-card-title">Yêu cầu công khai</h2><span className="mg-pill warn">{grants.length}</span></div>
          <div className="mg-list">{grants.map((grant) => {
            const item = lessons.find((candidate) => candidate.lesson_id === grant.lesson_id);
            return <button key={grant.access_grant_id} type="button" className={`mg-item${grant.access_grant_id === selected.access_grant_id ? " is-active" : ""}`} onClick={() => { setSelectedId(grant.access_grant_id); setChecks([false, false, false, false]); setReason(""); }} aria-pressed={grant.access_grant_id === selected.access_grant_id}>
              <span className="mg-ico-chip sm mg-tone-amber"><MgIcon name="book" size={17} /></span><span className="mg-grow"><span className="mg-item-title">{item?.title ?? `Giáo án ${grant.lesson_id}`}</span><span className="mg-item-sub">Bản {item?.current_version_no ?? "—"} · revision {grant.revision}</span></span><span className="mg-pill warn">{grant.state}</span>
            </button>;
          })}</div>
        </section>
        <section className="mg-card" aria-label="Chi tiết yêu cầu công khai">
          <div className="mg-card-head"><h2 className="mg-card-title">{lesson?.title ?? `Giáo án ${selected.lesson_id}`}</h2><span className="mg-pill info">{selected.capability}</span></div>
          <div className="mg-meta"><div className="mg-meta-row"><span>Chủ đề</span><span>{lesson?.topic ?? "Chưa có metadata trong trang hiện tại"}</span></div><div className="mg-meta-row"><span>Phiên bản</span><span>{lesson ? `Bản ${lesson.current_version_no}` : selected.version_id}</span></div><div className="mg-meta-row"><span>Revision grant</span><span>{selected.revision}</span></div><div className="mg-meta-row"><span>Hoạt động</span><span>{lesson?.activity_count ?? "—"}</span></div></div>
          <div className="mg-privacy"><MgIcon name="lock" size={18} /> Hàng đợi này chỉ là yêu cầu xuất bản metadata; API không trả media của trẻ.</div>
          <div className="mg-card-head"><strong>Tiêu chí rà soát</strong><span className={`mg-pill ${checkedCount === 4 ? "ok" : "off"}`}>{checkedCount}/4</span></div>
          <div className="mg-list" style={{ gap: 8 }}>{CRITERIA.map((criterion, index) => <button key={criterion} type="button" className={`mg-check${checks[index] ? " is-on" : ""}`} aria-pressed={checks[index]} onClick={() => setChecks((prior) => prior.map((value, i) => i === index ? !value : value))}><span className="mg-check-box"><MgIcon name="check" size={15} /></span>{criterion}</button>)}</div>
          <label className="mg-item-sub" style={{ display: "block", marginTop: 14 }}>Lý do yêu cầu chỉnh sửa (bắt buộc khi trả về)
            <textarea className="mg-textarea" maxLength={1000} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Nêu rõ phần cần chỉnh sửa" />
          </label>
          <div className="mg-actions"><button type="button" className="mg-btn soft" disabled={busy} onClick={() => void decide("REQUEST_CHANGES")}><MgIcon name="pencil" size={17} /> Yêu cầu chỉnh sửa</button><button type="button" className="mg-btn mint" disabled={busy || checkedCount !== 4} onClick={() => void decide("APPROVE")}><MgIcon name="check" size={17} /> Duyệt công khai</button></div>
        </section>
      </div>}
    </div>
  );
}

export function M01PublicationReviewPage({ showToast }: { showToast: Toast }) {
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState("rev-1");
  const [tab, setTab] = useState<"CONTENT" | "DIFF">("CONTENT");
  const [publicScope, setPublicScope] = useState(false);
  const [checks, setChecks] = useState([false, false, false, false]);
  const [feedback, setFeedback] = useState("");
  const [done, setDone] = useState<string[]>([]);

  if (!isLocalPreview()) return <ManagerApiReviewPage showToast={showToast} />;

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
    if (!feedback.trim()) {
      showToast("Hãy ghi rõ nội dung cần chỉnh sửa trước khi gửi.", "warn");
      return;
    }
    showToast(`Đã ghi nhận góp ý cho ${lesson.teacher}: “${feedback.trim()}”`, "info");
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
                placeholder="Ghi rõ nội dung cần chỉnh sửa (tối đa 500 ký tự)"
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

function ManagerApiOrganizationPage({ showToast }: { showToast: Toast }) {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    const organizationId = configuredOrganizationId();
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có Firebase ID token để xác nhận role và tải lớp.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setError("Chưa cấu hình organization_id cho API BE1.");
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    setError(null);
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "school_admin")) {
          throw new BackendApiError("Tài khoản không có assignment school_admin trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.classes(organizationId);
      })
      .then((page) => { if (active) setClasses(page.items); })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    const name = displayName.trim();
    if (!name || name.length > 200) {
      setError("Tên lớp phải có từ 1 đến 200 ký tự.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await backendApi.createClass(configuredOrganizationId(), name);
      setDisplayName("");
      showToast(`Đã tạo lớp “${created.display_name}”.`, "ok");
      setReload((value) => value + 1);
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mg-page">
      <BackendModeNotice roleLabel="Quản lý trường" />
      <div className="mg-hero">
        <div className="mg-hero-left"><span className="mg-hero-badge"><MgIcon name="school" size={30} /></span><div><h1 className="mg-title">Lớp học trong tổ chức</h1><div className="mg-sub">Danh sách và tạo lớp theo assignment school_admin của tài khoản.</div></div></div>
        <div className="mg-hero-pills"><span className="mg-pill info">{classes.length} lớp trong phạm vi API</span><button type="button" className="mg-btn sm soft" disabled={loading} onClick={() => setReload((value) => value + 1)}><MgIcon name="list" size={15} /> Tải lại</button></div>
      </div>
      {error && <BackendNotice title="Không tải hoặc tạo được lớp" tone="error">{error}</BackendNotice>}
      {loading && <BackendNotice title="Đang tải lớp">Đang kiểm tra assignment và phạm vi được backend cấp.</BackendNotice>}
      <section className="mg-card">
        <div className="mg-card-head"><h2 className="mg-card-title"><span className="mg-ico-chip sm mg-tone-mint"><MgIcon name="calendar" size={18} /></span>Lớp được API trả về</h2></div>
        <div className="mg-table-wrap"><table className="mg-table"><thead><tr><th>Tên lớp</th><th>class_id</th><th>Trạng thái</th></tr></thead><tbody>
          {classes.map((item) => <tr key={item.class_id}><td><div className="mg-cell"><span className="mg-ico-chip sm mg-tone-blue"><MgIcon name="school" size={16} /></span>{item.display_name}</div></td><td><code>{item.class_id}</code></td><td><span className="mg-pill ok">{item.state}</span></td></tr>)}
          {!loading && classes.length === 0 && <tr><td colSpan={3} style={{ textAlign: "center", color: "#475569" }}>Backend chưa trả về lớp nào trong phạm vi tài khoản.</td></tr>}
        </tbody></table></div>
      </section>
      <section className="mg-card">
        <div className="mg-card-head"><h2 className="mg-card-title">Tạo lớp</h2></div>
        <form onSubmit={(event) => void create(event)} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <input className="mg-input" style={{ flex: "1 1 260px" }} aria-label="Tên lớp mới" maxLength={200} value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Tên lớp, tối đa 200 ký tự" />
          <button type="submit" className="mg-btn primary" disabled={saving || loading || !displayName.trim()}><MgIcon name="plus" size={16} />{saving ? "Đang tạo…" : "Tạo lớp"}</button>
        </form>
      </section>
      <BackendNotice title="Các mục quản lý chưa có API trong BE đã đọc" tone="warn">
        Hệ thống hiện hỗ trợ xem danh sách và tạo lớp. Chưa có chức năng quản lý giáo viên, nhóm phụ huynh, hạn mức video, thanh toán và cài đặt gói ở màn này.
      </BackendNotice>
    </div>
  );
}

export function M02OrganizationManagementPage({ showToast }: { showToast: Toast }) {
  const location = useLocation();
  const navigate = useNavigate();
  const section = new URLSearchParams(location.search).get("section");
  const [extraSlots, setExtraSlots] = useState(0);
  const [extraQuota, setExtraQuota] = useState(0);
  const [autoRenew, setAutoRenew] = useState(true);

  if (!isLocalPreview()) return <ManagerApiOrganizationPage showToast={showToast} />;

  const usedSlots = 8;
  const totalSlots = 10 + extraSlots;
  const quotaLeft = 86 + extraQuota;
  const quotaTotal = 100 + extraQuota;

  const showTeachers = section === "teachers";
  const showClasses = section === "classes";
  const showQuota = section === "quota";
  const showSettings = section === "settings";

  return (
    <div className={"mg-page" + (!section ? " s2l-dashboard is-school-dashboard" : "")}>
      <div className={"mg-hero" + (!section ? " s2l-dashboard-banner" : "")}>
        <div className="mg-hero-left">
          <span className="mg-hero-badge" aria-hidden="true">
            <MgIcon name="school" size={30} />
          </span>
          <div>
            <h1 className="mg-title">Quản lý trường</h1>
            <div className="mg-sub">{section ? "Mầm non Ánh Dương" : "Mầm non Ánh Dương · Theo dõi lớp, nhân sự và hạn mức."}</div>
          </div>
        </div>
        {!section && (
          <button type="button" className="mg-btn primary" onClick={() => navigate("/m01-publication-review")}>
            <MgIcon name="check" size={17} /> Duyệt bài học công khai
          </button>
        )}
      </div>

      {!section && (
        <>
          <section className="s2l-dashboard-summary is-three" aria-label="Tình hình trường">
            <div className="s2l-dashboard-summary-item">
              <span className="s2l-dashboard-summary-value">{TEACHERS.length}</span>
              <span className="s2l-dashboard-summary-label">giáo viên · {PARENT_GROUPS.length} nhóm phụ huynh</span>
            </div>
            <div className="s2l-dashboard-summary-item">
              <span className="s2l-dashboard-summary-value">{CLASSES.length}</span>
              <span className="s2l-dashboard-summary-label">lớp · {usedSlots}/{totalSlots} suất đang dùng</span>
            </div>
            <div className="s2l-dashboard-summary-item">
              <span className="s2l-dashboard-summary-value">{quotaLeft}</span>
              <span className="s2l-dashboard-summary-label">lượt tạo video còn lại</span>
            </div>
          </section>

          <section className="s2l-dashboard-panel">
            <div className="s2l-dashboard-panel-head">
              <div>
                <h2>Truy cập nhanh</h2>
                <p>Chọn một mục để xem hoặc cập nhật thông tin của trường.</p>
              </div>
            </div>
            <div className="s2l-dashboard-list">
              <button type="button" className="s2l-dashboard-row" onClick={() => navigate("/m02-organization-management?section=teachers")}>
                <span className="s2l-dashboard-row-icon" aria-hidden="true"><MgIcon name="users" size={17} /></span>
                <span className="s2l-dashboard-row-main">
                  <span className="s2l-dashboard-row-title">Giáo viên và nhóm phụ huynh</span>
                  <span className="s2l-dashboard-row-sub">Quản lý thành viên và nhóm liên lạc.</span>
                </span>
                <span className="s2l-dashboard-row-value">{TEACHERS.length} GV · {PARENT_GROUPS.length} nhóm</span>
                <MgIcon name="chevron" size={16} color="#94A3B8" />
              </button>
              <button type="button" className="s2l-dashboard-row" onClick={() => navigate("/m02-organization-management?section=classes")}>
                <span className="s2l-dashboard-row-icon is-mint" aria-hidden="true"><MgIcon name="school" size={17} /></span>
                <span className="s2l-dashboard-row-main">
                  <span className="s2l-dashboard-row-title">Lớp học và sức chứa</span>
                  <span className="s2l-dashboard-row-sub">Xem sĩ số, phân công và số chỗ còn lại.</span>
                </span>
                <span className="s2l-dashboard-row-value">{CLASSES.length} lớp · {totalSlots - usedSlots} chỗ trống</span>
                <MgIcon name="chevron" size={16} color="#94A3B8" />
              </button>
              <button type="button" className="s2l-dashboard-row" onClick={() => navigate("/m02-organization-management?section=quota")}>
                <span className="s2l-dashboard-row-icon is-amber" aria-hidden="true"><MgIcon name="play" size={17} /></span>
                <span className="s2l-dashboard-row-main">
                  <span className="s2l-dashboard-row-title">Lượt tạo video</span>
                  <span className="s2l-dashboard-row-sub">Theo dõi hạn mức của trường trong tháng.</span>
                </span>
                <span className="s2l-dashboard-row-value">{quotaLeft} lượt</span>
                <MgIcon name="chevron" size={16} color="#94A3B8" />
              </button>
              <button type="button" className="s2l-dashboard-row" onClick={() => navigate("/m02-organization-management?section=settings")}>
                <span className="s2l-dashboard-row-icon is-slate" aria-hidden="true"><MgIcon name="gear" size={17} /></span>
                <span className="s2l-dashboard-row-main">
                  <span className="s2l-dashboard-row-title">Gói trường và quyền riêng tư</span>
                  <span className="s2l-dashboard-row-sub">Xem cấu hình gói và các tùy chọn hiện có.</span>
                </span>
                <span className="s2l-dashboard-row-value">Cài đặt</span>
                <MgIcon name="chevron" size={16} color="#94A3B8" />
              </button>
            </div>
          </section>
        </>
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
                  showToast("Đã minh họa thêm 1 suất lớp; không phát sinh thanh toán.", "info");
                }}
              >
                <MgIcon name="plus" size={15} /> Thêm suất lớp
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
                  showToast("Đã minh họa thêm 10 lượt video; không phát sinh thanh toán.", "info");
                }}
              >
                <MgIcon name="plus" size={15} /> Mua +10 lượt
              </button>
            </div>
            <div className="mg-bar" role="progressbar" aria-valuenow={quotaLeft} aria-valuemin={0} aria-valuemax={quotaTotal} aria-label="Lượt video còn lại">
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
              <button type="button" className="mg-btn sm primary" onClick={() => showToast("Đã minh họa lời mời; chưa gửi email thật.", "info")}>
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
              <button type="button" className="mg-btn sm soft" onClick={() => showToast("Bản xem thử chưa đồng bộ dữ liệu phụ huynh.", "info")}>
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
                Lớp &amp; suất học <span className="mg-pill info">{CLASSES.length}</span>
            </h2>
            <div style={{ display: "flex", gap: 10 }}>
              <button type="button" className="mg-btn sm primary" onClick={() => showToast("Bản xem thử chưa tạo lớp thật. Mục này sẽ mở biểu mẫu khi backend hỗ trợ.", "info")}>
                <MgIcon name="plus" size={16} /> Tạo lớp mới
              </button>
              <button type="button" className="mg-btn sm soft" onClick={() => navigate("/m02-organization-management?section=quota")}>
                <MgIcon name="chart" size={16} /> Xem lượt video
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
                  showToast("Đã thay đổi tùy chọn gia hạn minh họa trong phiên.", "info");
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
