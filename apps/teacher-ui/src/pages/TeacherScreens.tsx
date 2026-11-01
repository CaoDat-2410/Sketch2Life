import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { TeacherUi05Mode, useTeacher } from "../context/TeacherContext";
import { Icon, IconBadge } from "../components/Icon";

/* ── UI08 Access Grants Two-Table Component ── */
function AccessGrantsTablesSection() {
  const { grants, revokeTeacherGrant, addLessonGrant } = useTeacher();
  const lessonGrants = grants.filter((g) => g.kind === "LESSON");
  const profileGrants = grants.filter((g) => g.kind === "CHILD_PROFILE");

  const StatusPill = ({ status }: { status: string }) => (
    <span
      className={`pill ${
        status === "Đang hiệu lực" ? "ok" : status === "Đang chờ" ? "warn" : "off"
      }`}
      style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
    >
      <Icon
        name={status === "Đang hiệu lực" ? "check" : status === "Đang chờ" ? "clock" : "close"}
        size={12}
      />
      {status}
    </span>
  );

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* Table 1: Chia sẻ giáo án */}
      <div className="card col" style={{ gap: 12 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="share" tone="primary" size={38} />
            <div>
              <div style={{ fontWeight: 800 }}>Chia sẻ giáo án</div>
              <div className="tiny muted">Bảng UI08 · Nhóm phụ huynh & giáo viên</div>
            </div>
          </div>
          <button
            type="button"
            className="btn small"
            onClick={() =>
              addLessonGrant("Nhóm phụ huynh Lớp Chồi 1", "Giáo án: Vòng đời bướm · Bản 3")
            }
          >
            <Icon name="plus" size={14} color="#FFF" /> Chia sẻ
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Người nhận</th>
              <th>Phạm vi</th>
              <th>Hết hạn</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {lessonGrants.map((g) => (
              <tr key={g.id}>
                <td style={{ fontWeight: 700 }}>{g.recipient}</td>
                <td>{g.scope}</td>
                <td>{g.expiresAt}</td>
                <td><StatusPill status={g.status} /></td>
                <td>
                  {g.status === "Đang hiệu lực" ? (
                    <button
                      type="button"
                      className="btn danger small"
                      onClick={() => revokeTeacherGrant(g.id)}
                    >
                      Thu hồi
                    </button>
                  ) : (
                    <span className="tiny muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table 2: Chia sẻ hồ sơ trẻ */}
      <div className="card col" style={{ gap: 12 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="user" tone="mint" size={38} />
            <div>
              <div style={{ fontWeight: 800 }}>Chia sẻ hồ sơ trẻ</div>
              <div className="tiny muted">Bảng UI08 · Do phụ huynh cấp quyền</div>
            </div>
          </div>
          <span className="pill">Lớp Mầm 2</span>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Người nhận</th>
              <th>Phạm vi</th>
              <th>Hết hạn</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {profileGrants.map((g) => (
              <tr key={g.id}>
                <td style={{ fontWeight: 700 }}>{g.recipient}</td>
                <td>{g.scope}</td>
                <td>{g.expiresAt}</td>
                <td><StatusPill status={g.status} /></td>
                <td>
                  {g.status === "Đang hiệu lực" ? (
                    <button
                      type="button"
                      className="btn danger small"
                      onClick={() => revokeTeacherGrant(g.id)}
                    >
                      Thu hồi
                    </button>
                  ) : (
                    <span className="tiny muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── T01 — Teacher Lesson Workspace Dashboard ── */
export function T01LessonWorkspacePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    lessons,
    restoreDefaultLessons,
    ui05Mode,
    setUi05Mode,
    setArchiveModalTarget,
    feedbackThread,
    replyToFeedback,
    showToast,
  } = useTeacher();
  const [replyDraft, setReplyDraft] = useState("");

  const viewParam = new URLSearchParams(location.search).get("view");

  /* ── Phản hồi view ── */
  if (viewParam === "feedback") {
    return (
      <div className="col" style={{ gap: 20 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="message" tone="primary" size={44} />
            <div>
              <h1>Phản hồi phụ huynh</h1>
              <p className="muted small">Bài học "Vòng đời bướm · Bản 3" · Lớp Mầm 2</p>
            </div>
          </div>
          <button
            type="button"
            className="btn ghost small"
            onClick={() => navigate("/t01-lesson-workspace")}
          >
            <Icon name="arrow-left" size={16} /> Tổng quan
          </button>
        </div>

        {/* UI09 Feedback Thread */}
        <div className="card col" style={{ gap: 14 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div style={{ fontWeight: 800 }}>Vòng đời bướm · Bản 3 (Bảng UI09)</div>
              <div className="tiny muted">Chỉ nhận văn bản · Không đính kèm ảnh/video trẻ</div>
            </div>
            <span className="pill ok"><Icon name="check" size={12} /> Đã phản hồi</span>
          </div>

          <div className="col" style={{ gap: 10 }}>
            {feedbackThread.map((item) => (
              <div
                key={item.id}
                style={{
                  padding: "10px 14px",
                  borderRadius: 12,
                  background: item.sender === "Phụ huynh bé Minh" ? "var(--primary-50)" : "var(--mint-50)",
                  border: "1px solid var(--line)",
                }}
              >
                <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontWeight: 800, fontSize: 13 }}>{item.sender}</span>
                  <span className="tiny muted">{item.date}</span>
                </div>
                <p className="small">{item.text}</p>
              </div>
            ))}
          </div>

          <div className="field">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <label htmlFor="teacher-reply">Phản hồi của giáo viên</label>
              <span className="tiny muted">{replyDraft.length}/300</span>
            </div>
            <textarea
              id="teacher-reply"
              className="input"
              maxLength={300}
              rows={2}
              placeholder="Nhập phản hồi cho phụ huynh bé Minh..."
              value={replyDraft}
              onChange={(e) => setReplyDraft(e.target.value)}
            />
          </div>

          <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
            <button type="button" className="btn ghost small" onClick={() => setReplyDraft("")}>
              Hủy
            </button>
            <button
              type="button"
              className="btn accent small"
              onClick={() => { replyToFeedback(replyDraft); setReplyDraft(""); }}
            >
              <Icon name="share" size={14} color="#FFF" /> Gửi
            </button>
          </div>
        </div>

        <AccessGrantsTablesSection />
      </div>
    );
  }

  /* ── Cài đặt view ── */
  if (viewParam === "settings") {
    return (
      <div className="col" style={{ gap: 20 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="settings" tone="primary" size={44} />
            <div>
              <h1>Cài đặt không gian làm việc</h1>
              <p className="muted small">Cô Thảo · Lớp Mầm 2 · Trường Mầm non Ánh Dương</p>
            </div>
          </div>
          <button
            type="button"
            className="btn ghost small"
            onClick={() => navigate("/t01-lesson-workspace")}
          >
            <Icon name="arrow-left" size={16} /> Tổng quan
          </button>
        </div>

        <div className="card col" style={{ gap: 10 }}>
          <div className="row" style={{ gap: 8 }}>
            <Icon name="users" size={18} color="var(--primary)" />
            <div style={{ fontWeight: 800 }}>Thông tin phân công</div>
          </div>
          <p className="small muted">
            Lớp phụ trách: <strong>Lớp Mầm 2 (24 trẻ · 4–5 tuổi)</strong>. Quyền truy cập giáo án và hồ sơ trẻ đồng bộ tự động theo phân công của Quản lý trường.
          </p>
        </div>

        <AccessGrantsTablesSection />
      </div>
    );
  }

  /* ── Main dashboard ── */
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
        <div>
          <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 2 }}>Xin chào 👋</div>
          <h1 style={{ color: "#FFFFFF", margin: 0 }}>Cô Thảo</h1>
          <div style={{ fontSize: 13, opacity: 0.8, marginTop: 2 }}>
            Trường Mầm non Ánh Dương · 30/10/2026
          </div>
        </div>
        <div className="row" style={{ gap: 10 }}>
          <button
            type="button"
            className="btn secondary small"
            style={{ background: "rgba(255,255,255,0.15)", borderColor: "rgba(255,255,255,0.3)", color: "#FFF" }}
            onClick={() => navigate("/t03-document-import-review")}
          >
            <Icon name="download" size={15} color="#FFF" /> Nhập giáo án
          </button>
          <button
            type="button"
            style={{
              background: "#FFFFFF",
              color: "var(--primary)",
              border: "none",
              borderRadius: 12,
              padding: "9px 18px",
              fontWeight: 800,
              fontSize: 14,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
            onClick={() => navigate("/t02-lesson-authoring")}
          >
            <Icon name="plus" size={15} color="var(--primary)" /> Tạo giáo án
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
        <div className="card col" style={{ gap: 10 }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="users" tone="primary" size={38} />
            <div>
              <div style={{ fontWeight: 800 }}>Lớp Mầm 2</div>
              <div className="tiny muted">24 trẻ · 4–5 tuổi</div>
            </div>
            <span className="pill ok" style={{ marginLeft: "auto", fontSize: 11 }}>Đang phụ trách</span>
          </div>
          <button
            type="button"
            className="btn secondary small"
            style={{ alignSelf: "flex-start" }}
            onClick={() => navigate("/t05-classes-and-children")}
          >
            Xem danh sách lớp
          </button>
        </div>

        <div className="card col" style={{ gap: 10 }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="palette" tone="accent" size={38} />
            <div>
              <div style={{ fontWeight: 800 }}>Vòng đời bướm</div>
              <div className="tiny muted">30/10/2026 · Lớp Mầm 2</div>
            </div>
            <span className="pill" style={{ marginLeft: "auto", fontSize: 11 }}>Sắp tới</span>
          </div>
          <button
            type="button"
            className="btn small"
            style={{ alignSelf: "flex-start" }}
            onClick={() => navigate("/t04-session-sketch-deck")}
          >
            <Icon name="palette" size={14} color="#FFF" /> Chuẩn bị buổi học
          </button>
        </div>

        <div className="card col" style={{ gap: 10 }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="message" tone="accent" size={38} />
            <div>
              <div style={{ fontWeight: 800 }}>Vòng đời bướm · Bản 3</div>
              <div className="tiny muted">Phản hồi từ phụ huynh bé Minh</div>
            </div>
            <span className="pill warn" style={{ marginLeft: "auto", fontSize: 11 }}>2 mới</span>
          </div>
          <button
            type="button"
            className="btn secondary small"
            style={{ alignSelf: "flex-start" }}
            onClick={() => navigate("/t01-lesson-workspace?view=feedback")}
          >
            Xem phản hồi
          </button>
        </div>
      </div>

      {/* Lesson Cards */}
      <div className="card col" style={{ gap: 14 }}>
        <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="book" tone="primary" size={38} />
            <div>
              <div style={{ fontWeight: 800 }}>Giáo án của Cô Thảo</div>
              <div className="tiny muted">{lessons.length} giáo án đang mở</div>
            </div>
          </div>

          <details style={{ fontSize: 12 }}>
            <summary style={{ cursor: "pointer", fontWeight: 700, color: "var(--ink-2)", listStyle: "none", display: "flex", alignItems: "center", gap: 6 }}>
              <Icon name="settings" size={14} color="var(--ink-3)" /> Trạng thái UI05
            </summary>
            <div style={{ marginTop: 8 }}>
              <select
                aria-label="Chọn trạng thái UI05"
                className="input"
                style={{ width: 230, padding: "5px 10px", fontSize: 12 }}
                value={ui05Mode}
                onChange={(e) => setUi05Mode(e.target.value as TeacherUi05Mode)}
              >
                <option value="NORMAL">Mặc định</option>
                <option value="LOADING">UI05 · Đang tải</option>
                <option value="EMPTY">UI05 · Chưa có giáo án</option>
                <option value="STALE_409">UI05 · Đã thay đổi (409)</option>
                <option value="FORBIDDEN_403">UI05 · Không có quyền (403)</option>
              </select>
            </div>
          </details>
        </div>

        {ui05Mode === "LOADING" && (
          <div className="card col" style={{ padding: 28, textAlign: "center", alignItems: "center", gap: 10 }}>
            <IconBadge name="refresh" tone="primary" size={48} />
            <div style={{ fontWeight: 700 }}>Đang tải giáo án...</div>
          </div>
        )}

        {ui05Mode === "EMPTY" && (
          <div className="card col" style={{ padding: 28, textAlign: "center", alignItems: "center", gap: 12 }}>
            <IconBadge name="book" tone="primary" size={48} />
            <div style={{ fontWeight: 700 }}>Chưa có giáo án</div>
            <p className="muted small">Hãy tạo giáo án đầu tiên để bắt đầu dạy học.</p>
            <button type="button" className="btn" onClick={() => navigate("/t02-lesson-authoring")}>
              <Icon name="plus" size={16} color="#FFF" /> Tạo giáo án
            </button>
          </div>
        )}

        {ui05Mode === "STALE_409" && (
          <div
            className="card row"
            style={{ justifyContent: "space-between", background: "var(--warn-50)", borderColor: "var(--warn-100)", gap: 12 }}
          >
            <div className="row" style={{ gap: 10 }}>
              <Icon name="alert" size={20} color="var(--warn-700)" />
              <div>
                <div style={{ fontWeight: 800, color: "var(--warn-700)" }}>Giáo án đã thay đổi</div>
                <p className="small muted">Phiên bản mới có sẵn.</p>
              </div>
            </div>
            <button
              type="button"
              className="btn accent"
              onClick={() => { setUi05Mode("NORMAL"); showToast("Đã làm mới phiên bản mới nhất.", "ok"); }}
            >
              <Icon name="refresh" size={15} color="#FFF" /> Làm mới
            </button>
          </div>
        )}

        {ui05Mode === "FORBIDDEN_403" && (
          <div
            className="card row"
            style={{ justifyContent: "space-between", background: "var(--danger-50)", borderColor: "#FECACA", gap: 12 }}
          >
            <div className="row" style={{ gap: 10 }}>
              <Icon name="lock" size={20} color="var(--danger)" />
              <div>
                <div style={{ fontWeight: 800, color: "var(--danger)" }}>Không có quyền xem</div>
                <p className="small muted">Vui lòng liên hệ quản trị viên để được cấp quyền.</p>
              </div>
            </div>
            <button type="button" className="btn secondary small" onClick={() => setUi05Mode("NORMAL")}>
              Quay lại
            </button>
          </div>
        )}

        {ui05Mode === "NORMAL" && (
          <>
            {lessons.length === 0 ? (
              <div className="card col" style={{ textAlign: "center", padding: 24, alignItems: "center", gap: 10 }}>
                <div style={{ fontWeight: 700 }}>Chưa có giáo án đang mở</div>
                <button type="button" className="btn secondary small" onClick={restoreDefaultLessons}>
                  Khôi phục giáo án mẫu
                </button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 14 }}>
                {lessons.map((les) => (
                  <div key={les.id} className="card col" style={{ gap: 10 }}>
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <div>
                        <div style={{ fontWeight: 800 }}>{les.title} · {les.version}</div>
                        <div className="tiny muted">{les.ageBand} · Cập nhật {les.updatedAt}</div>
                      </div>
                      <span className={`pill ${les.visibility === "Trong trường" ? "ok" : "warn"}`}>
                        {les.visibility}
                      </span>
                    </div>
                    <p className="small muted">{les.objectives}</p>
                    <div className="row" style={{ gap: 8, marginTop: 4 }}>
                      <button type="button" className="btn small" onClick={() => navigate("/t02-lesson-authoring")}>
                        <Icon name="book" size={14} color="#FFF" /> Chỉnh sửa
                      </button>
                      <button type="button" className="btn secondary small" onClick={() => navigate("/t04-session-sketch-deck")}>
                        <Icon name="palette" size={14} color="var(--primary)" /> Buổi học
                      </button>
                      <span className="spacer" />
                      <button type="button" className="btn danger small" onClick={() => setArchiveModalTarget(les)}>
                        <Icon name="download" size={14} color="var(--danger)" /> Lưu trữ
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ── T02 — Structured Lesson Authoring ── */
export function T02LessonAuthoringPage() {
  const navigate = useNavigate();
  const { showToast } = useTeacher();
  const [activeStepTab, setActiveStepTab] = useState(0);
  const [topic, setTopic] = useState("Vòng đời bướm");
  const [ageBand, setAgeBand] = useState("4–5 tuổi (Mẫu giáo)");
  const [objectives, setObjectives] = useState(
    "Giúp trẻ nhận biết hành trình sâu hóa bướm, phát triển khả năng quan sát màu sắc và vận động ngoài sân trường."
  );
  const [drawingStepsText, setDrawingStepsText] = useState(
    "1. Vẽ thân bướm ở giữa trang giấy\n2. Vẽ hai cánh trên mở rộng\n3. Vẽ hai cánh dưới và râu cong\n4. Tô màu sáp tự do"
  );
  const [knowledgeText, setKnowledgeText] = useState(
    "Bướm trải qua 4 giai đoạn: trứng nhỏ trên lá, sâu bướm ăn lá, kén nhộng nghỉ ngơi và bướm trưởng thành xòe cánh."
  );
  const [videoDirection, setVideoDirection] = useState(
    "Giữ đúng màu sáp trên cánh bướm của trẻ, giọng kể nhẹ nhàng khuyến khích trẻ quan sát lá cây ngoài sân trường."
  );
  const [visibility, setVisibility] = useState<"Riêng tư" | "Trong trường" | "Công khai">("Trong trường");
  const [safetyCheck1, setSafetyCheck1] = useState(true);
  const [safetyCheck2, setSafetyCheck2] = useState(true);

  const stepTabs = [
    { label: "Tổng quan", icon: "sun" as const },
    { label: "Vẽ & kiến thức", icon: "palette" as const },
    { label: "Hoạt động", icon: "leaf" as const },
    { label: "Rà soát", icon: "check" as const },
  ];
  const isAgeMissing = !ageBand.trim();

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="book" tone="primary" size={44} />
          <div>
            <h1>Tạo giáo án</h1>
            <p className="muted small">Lớp Mầm 2 · Phương pháp khám phá</p>
          </div>
        </div>
        <span className="pill">Vòng đời bướm · Bản 3</span>
      </div>

      {/* Step Tabs */}
      <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
        {stepTabs.map((tab, idx) => (
          <button
            key={tab.label}
            type="button"
            className={`btn small ${activeStepTab === idx ? "" : "secondary"}`}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
            onClick={() => setActiveStepTab(idx)}
          >
            <Icon name={tab.icon} size={14} color={activeStepTab === idx ? "#FFF" : "var(--primary)"} />
            {idx + 1}. {tab.label}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.15fr 1fr", gap: 16 }}>
        {/* Left Column */}
        <div className="col" style={{ gap: 16 }}>
          <div className="card col" style={{ gap: 12 }}>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="sun" size={18} color="var(--primary)" />
              <h2 style={{ margin: 0 }}>1. Tổng quan & Mục tiêu</h2>
            </div>
            <div className="row" style={{ gap: 12, alignItems: "flex-start" }}>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="t02-topic">Chủ đề</label>
                <input id="t02-topic" className="input" value={topic} onChange={(e) => setTopic(e.target.value)} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="t02-age">Độ tuổi gợi ý</label>
                <select
                  id="t02-age"
                  className={`input ${isAgeMissing ? "error" : ""}`}
                  value={ageBand}
                  onChange={(e) => setAgeBand(e.target.value)}
                >
                  <option value="">-- Chọn độ tuổi --</option>
                  <option value="3–4 tuổi (Mầm)">3–4 tuổi (Mầm)</option>
                  <option value="4–5 tuổi (Mẫu giáo)">4–5 tuổi (Mẫu giáo)</option>
                  <option value="5–6 tuổi (Lá)">5–6 tuổi (Lá)</option>
                </select>
                {isAgeMissing && (
                  <span className="tiny" style={{ color: "var(--danger)", fontWeight: 700 }}>
                    <Icon name="alert" size={12} color="var(--danger)" /> Vui lòng chọn độ tuổi
                  </span>
                )}
              </div>
            </div>
            <div className="field">
              <label htmlFor="t02-obj">Mục tiêu</label>
              <textarea id="t02-obj" className="input" rows={2} value={objectives} onChange={(e) => setObjectives(e.target.value)} />
            </div>
          </div>

          <div className="card col" style={{ gap: 12 }}>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="palette" size={18} color="var(--primary)" />
              <h2 style={{ margin: 0 }}>2. Vẽ & kiến thức</h2>
            </div>
            <div className="field">
              <label htmlFor="t02-steps">Các bước vẽ</label>
              <textarea id="t02-steps" className="input" rows={4} value={drawingStepsText} onChange={(e) => setDrawingStepsText(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="t02-knowledge">Kiến thức về chủ đề</label>
              <textarea id="t02-knowledge" className="input" rows={3} value={knowledgeText} onChange={(e) => setKnowledgeText(e.target.value)} />
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="col" style={{ gap: 16 }}>
          <div className="card col" style={{ gap: 12 }}>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="leaf" size={18} color="var(--mint-700)" />
              <h2 style={{ margin: 0 }}>3. Hoạt động ngoài trời</h2>
            </div>

            <div className="card col" style={{ padding: 12, gap: 6, background: "var(--bg)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>Hoạt động 1: Quan sát vòng đời bướm</div>
                <span className="pill ok" style={{ fontSize: 11 }}>Ngoài trời</span>
              </div>
              <p className="small muted">Vật liệu: Kính lúp nhựa an toàn, thẻ tranh chiếc lá.</p>
              <label className="row small" style={{ marginTop: 4, fontWeight: 600, gap: 6 }}>
                <input type="checkbox" checked={safetyCheck1} onChange={(e) => setSafetyCheck1(e.target.checked)} />
                <span>Lưu ý an toàn: Không chạm tay trực tiếp vào côn trùng lạ.</span>
              </label>
            </div>

            <div className="card col" style={{ padding: 12, gap: 6, background: "var(--bg)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>Hoạt động 2: Đôi cánh bướm mùa xuân</div>
                <span className="pill ok" style={{ fontSize: 11 }}>Sân cỏ</span>
              </div>
              <p className="small muted">Vật liệu: Vòng thể dục nhựa đặt trên thảm cỏ.</p>
              <label className="row small" style={{ marginTop: 4, fontWeight: 600, gap: 6 }}>
                <input type="checkbox" checked={safetyCheck2} onChange={(e) => setSafetyCheck2(e.target.checked)} />
                <span>Lưu ý an toàn: Sân phẳng, khô ráo và có giáo viên quan sát.</span>
              </label>
            </div>
          </div>

          <div className="card col" style={{ gap: 12 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="video" size={18} color="var(--primary)" />
                <h2 style={{ margin: 0 }}>4. Hướng kể & Phạm vi</h2>
              </div>
              <span className="tiny muted">{videoDirection.length}/500</span>
            </div>
            <div className="field">
              <label htmlFor="t02-dir">Hướng kể cho video (tùy chọn)</label>
              <textarea id="t02-dir" className="input" maxLength={500} rows={3} value={videoDirection} onChange={(e) => setVideoDirection(e.target.value)} />
            </div>

            <div className="field">
              <label>Phạm vi hiển thị</label>
              <div className="row" style={{ gap: 8 }}>
                {(["Riêng tư", "Trong trường", "Công khai"] as const).map((scope) => (
                  <button
                    key={scope}
                    type="button"
                    className={`btn small ${visibility === scope ? "" : "secondary"}`}
                    onClick={() => setVisibility(scope)}
                  >
                    {scope}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="card row" style={{ justifyContent: "space-between" }}>
        <button
          type="button"
          className="btn secondary"
          onClick={() => showToast("Đã lưu thay đổi bản nháp giáo án Vòng đời bướm.", "ok")}
        >
          <Icon name="download" size={16} color="var(--ink-2)" /> Lưu nháp
        </button>
        <div className="row" style={{ gap: 10 }}>
          <button type="button" className="btn secondary" onClick={() => navigate("/t04-session-sketch-deck")}>
            Xem trước
          </button>
          <button
            type="button"
            className="btn"
            disabled={!safetyCheck1 || !safetyCheck2 || isAgeMissing}
            onClick={() => {
              showToast("Đã gửi giáo án Vòng đời bướm · Bản 3 tới Quản lý trường duyệt.", "ok");
              navigate("/t01-lesson-workspace");
            }}
          >
            <Icon name="share" size={16} color="#FFF" /> Gửi quản lý duyệt
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── T03 — Document Import & Extraction Review (2-column side-by-side) ── */
export function T03DocumentImportReviewPage() {
  const navigate = useNavigate();
  const { importErrorMode, setImportErrorMode, showToast } = useTeacher();
  const [selectedDocPage, setSelectedDocPage] = useState<1 | 2 | 3>(1);

  const [topic, setTopic] = useState("Vòng đời bướm");
  const [ageBand, setAgeBand] = useState("4–5 tuổi (Mẫu giáo)");
  const [objectives, setObjectives] = useState(
    "Trẻ nhận biết vòng đời 4 giai đoạn của bướm và vẽ tranh con bướm trên giấy A4."
  );
  const [drawingSteps, setDrawingSteps] = useState(
    "Bước 1: Vẽ thân bướm · Bước 2: Vẽ cánh trên · Bước 3: Vẽ cánh dưới · Bước 4: Tô màu sáp"
  );
  const [activities, setActivities] = useState(
    "Quan sát vòng đời bướm ngoài vườn trường; Trò chơi vận động Đôi cánh bướm."
  );
  const [materials, setMaterials] = useState("Giấy trắng A4, bút sáp màu, kính lúp nhựa trẻ em.");
  const [safetyNote, setSafetyNote] = useState(
    "Giáo viên kiểm tra khu vực sân vườn trước giờ học; trẻ không tự ý chạm vào côn trùng."
  );

  const isAgeMissing = ageBand.trim().length === 0;
  const isSafetyMissing = safetyNote.trim().length === 0;

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="download" tone="primary" size={44} />
          <div>
            <h1>Nhập giáo án</h1>
            <p className="muted small">PDF · PPTX · DOCX · tối đa 25 MB / 100 trang</p>
          </div>
        </div>
        <span className="pill ok">
          <Icon name="check" size={12} /> Giao_an_vong_doi_buom.docx · 2,4 MB
        </span>
      </div>

      {/* Stepper */}
      <div className="card row" style={{ gap: 10, padding: "10px 14px", flexWrap: "wrap", alignItems: "center" }}>
        <span className="pill ok"><Icon name="check" size={12} /> Tải tệp</span>
        <Icon name="arrow-right" size={14} color="var(--ink-3)" />
        <span className="pill ok"><Icon name="check" size={12} /> Lọc & trích xuất</span>
        <Icon name="arrow-right" size={14} color="var(--ink-3)" />
        <span className="pill">Giáo viên rà soát</span>
        <span className="spacer" />
        <details style={{ fontSize: 12 }}>
          <summary style={{ cursor: "pointer", fontWeight: 700, color: "var(--ink-2)", listStyle: "none" }}>
            <Icon name="settings" size={13} color="var(--ink-3)" /> Mô phỏng lỗi
          </summary>
          <div style={{ marginTop: 6 }}>
            <select
              aria-label="Xem thử trạng thái kiểm tra tệp (UI06)"
              className="input"
              style={{ width: 260, padding: "5px 10px", fontSize: 12 }}
              value={importErrorMode}
              onChange={(e) => setImportErrorMode(e.target.value as typeof importErrorMode)}
            >
              <option value="NONE">Hợp lệ (2,4 MB · 6 trang)</option>
              <option value="TOO_LARGE">Lỗi UI06: Tệp vượt 25 MB</option>
              <option value="TOO_MANY_PAGES">Lỗi UI06: Hơn 100 trang</option>
              <option value="SCANNED_PDF">Lỗi UI06: PDF scan</option>
              <option value="PASSWORD_PROTECTED">Lỗi UI06: Có mật khẩu</option>
            </select>
          </div>
        </details>
      </div>

      {/* UI06 Error Banner */}
      {importErrorMode !== "NONE" && (
        <div
          className="card row"
          style={{ background: "var(--danger-50)", borderColor: "#FECACA", justifyContent: "space-between", gap: 12 }}
        >
          <div className="row" style={{ gap: 10 }}>
            <Icon name="alert" size={20} color="var(--danger)" />
            <div>
              <div style={{ fontWeight: 800, color: "var(--danger)" }}>
                {importErrorMode === "TOO_LARGE" && "Tệp vượt quá giới hạn 25 MB"}
                {importErrorMode === "TOO_MANY_PAGES" && "Tài liệu có hơn 100 trang"}
                {importErrorMode === "SCANNED_PDF" && "Không hỗ trợ PDF scan"}
                {importErrorMode === "PASSWORD_PROTECTED" && "Không hỗ trợ tệp có mật khẩu"}
              </div>
              <div className="small muted">Vui lòng chọn tệp PDF, PPTX hoặc DOCX có lớp văn bản.</div>
            </div>
          </div>
          <button type="button" className="btn secondary small" onClick={() => setImportErrorMode("NONE")}>
            Chọn tệp hợp lệ
          </button>
        </div>
      )}

      {/* 2-Column Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.25fr", gap: 16 }}>
        {/* Left: Document content */}
        <div className="col" style={{ gap: 16 }}>
          <div className="card col" style={{ gap: 10 }}>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="download" size={16} color="var(--primary)" />
              <h2 style={{ margin: 0 }}>Tệp đã tải lên</h2>
            </div>
            <div
              style={{
                border: "2px dashed var(--primary-100)",
                borderRadius: 12,
                padding: 16,
                background: "var(--primary-50)",
                textAlign: "center",
              }}
            >
              <div style={{ fontWeight: 700, color: "var(--primary)" }}>
                Giao_an_vong_doi_buom.docx · 2,4 MB (6 trang)
              </div>
              <p className="tiny muted" style={{ marginTop: 4 }}>
                Tệp gốc được giữ riêng tư · Không gửi thô sang AI
              </p>
            </div>
          </div>

          <div className="card col" style={{ gap: 10 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="book" size={16} color="var(--primary)" />
                <h2 style={{ margin: 0 }}>Nội dung trích xuất</h2>
              </div>
              <div className="row" style={{ gap: 6 }}>
                {([1, 2, 3] as const).map((pg) => (
                  <button
                    key={pg}
                    type="button"
                    className={`btn small ${selectedDocPage === pg ? "" : "secondary"}`}
                    style={{ padding: "4px 9px", fontSize: 11.5 }}
                    onClick={() => setSelectedDocPage(pg)}
                  >
                    Tr.{pg}
                  </button>
                ))}
              </div>
            </div>

            <div
              style={{
                padding: 12, borderRadius: 10, background: "var(--bg)",
                border: "1px solid var(--line)", fontSize: 13, lineHeight: 1.55,
              }}
            >
              {selectedDocPage === 1 && (
                <>
                  <strong>[Trang 1 — Thông tin chung]</strong>
                  <p className="small muted" style={{ marginTop: 4 }}>
                    Đề tài: Khám phá Vòng đời của bướm · Lứa tuổi: Mẫu giáo 4–5 tuổi. Mục tiêu: Trẻ gọi đúng tên 4 giai đoạn.
                  </p>
                </>
              )}
              {selectedDocPage === 2 && (
                <>
                  <strong>[Trang 2 — Hoạt động vẽ]</strong>
                  <p className="small muted" style={{ marginTop: 4 }}>
                    Chuẩn bị giấy trắng A4, bút sáp màu. Hướng dẫn 4 bước: vẽ thân, vẽ hai cánh trên, vẽ hai cánh dưới và tô màu.
                  </p>
                </>
              )}
              {selectedDocPage === 3 && (
                <>
                  <strong>[Trang 3 — Ngoài trời & An toàn]</strong>
                  <p className="small muted" style={{ marginTop: 4 }}>
                    Dẫn trẻ ra vườn quan sát lá cây bằng kính lúp. Lưu ý: Giáo viên kiểm tra sân trước giờ học.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right: Editable fields */}
        <div className="card col" style={{ gap: 12 }}>
          <div>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="check" size={18} color="var(--primary)" />
              <h2 style={{ margin: 0 }}>Giáo viên rà soát & xác nhận</h2>
            </div>
            <p className="muted small" style={{ marginTop: 4 }}>
              Chỉ các trường đã xác nhận bên dưới mới được lưu thành bản nháp giáo án.
            </p>
          </div>

          <div className="row" style={{ gap: 12, alignItems: "flex-start" }}>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="imp-topic">Chủ đề</label>
              <input id="imp-topic" className="input" value={topic} onChange={(e) => setTopic(e.target.value)} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="imp-age">Độ tuổi *</label>
              <input
                id="imp-age"
                className={`input ${isAgeMissing ? "error" : ""}`}
                placeholder="Ví dụ: 4–5 tuổi"
                value={ageBand}
                onChange={(e) => setAgeBand(e.target.value)}
              />
              {isAgeMissing && (
                <span className="tiny" style={{ color: "var(--danger)", fontWeight: 700 }}>
                  Vui lòng chọn độ tuổi phù hợp.
                </span>
              )}
            </div>
          </div>

          <div className="field">
            <label htmlFor="imp-obj">Mục tiêu</label>
            <textarea id="imp-obj" className="input" rows={2} value={objectives} onChange={(e) => setObjectives(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="imp-steps">Các bước vẽ</label>
            <textarea id="imp-steps" className="input" rows={2} value={drawingSteps} onChange={(e) => setDrawingSteps(e.target.value)} />
          </div>

          <div className="row" style={{ gap: 12 }}>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="imp-act">Hoạt động</label>
              <textarea id="imp-act" className="input" rows={2} value={activities} onChange={(e) => setActivities(e.target.value)} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="imp-mat">Vật liệu</label>
              <textarea id="imp-mat" className="input" rows={2} value={materials} onChange={(e) => setMaterials(e.target.value)} />
            </div>
          </div>

          <div className="field">
            <label htmlFor="imp-safety">Lưu ý an toàn *</label>
            <textarea
              id="imp-safety"
              className={`input ${isSafetyMissing ? "error" : ""}`}
              rows={2}
              value={safetyNote}
              onChange={(e) => setSafetyNote(e.target.value)}
            />
            {isSafetyMissing && (
              <span className="tiny" style={{ color: "var(--danger)", fontWeight: 700 }}>
                Vui lòng bổ sung Lưu ý an toàn.
              </span>
            )}
          </div>

          <div className="row" style={{ justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
            <button
              type="button"
              className="btn secondary"
              onClick={() => showToast("Đã lưu chỉnh sửa các trường trích xuất.", "ok")}
            >
              Lưu chỉnh sửa
            </button>
            <button
              type="button"
              className="btn"
              disabled={isAgeMissing || isSafetyMissing || importErrorMode !== "NONE"}
              onClick={() => {
                showToast("Đã xác nhận nội dung đã lọc và tạo bản nháp giáo án.", "ok");
                navigate("/t04-session-sketch-deck");
              }}
            >
              <Icon name="check" size={16} color="#FFF" /> Xác nhận nội dung đã lọc
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── T04 — Session Preparation & Optional Teacher Sketch Deck ── */
export function T04SessionSketchDeckPage() {
  const navigate = useNavigate();
  const {
    sketchDeckEnabled,
    setSketchDeckEnabled,
    activeDeckStep,
    setActiveDeckStep,
    deckRevision,
    regenerateDeckStep,
    showToast,
  } = useTeacher();

  const deckSteps = [
    { step: 1, title: "Bước 1: Thân bướm ở giữa trang", hint: "Đặt thân hình bầu dục dọc ở chính giữa tờ giấy A4." },
    { step: 2, title: "Bước 2: Hai cánh trên xòe rộng", hint: "Vẽ hai nét cong lớn cân đối sang trái và phải." },
    { step: 3, title: "Bước 3: Hai cánh dưới tròn", hint: "Vẽ tiếp hai cánh nhỏ phía dưới nối liền vào thân." },
    { step: 4, title: "Bước 4: Râu cong & họa tiết", hint: "Thêm hai râu cong trên đầu và các vòng tròn trên cánh." },
  ];

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="palette" tone="primary" size={44} />
          <div>
            <h1>Chuẩn bị buổi học</h1>
            <p className="muted small">Vòng đời bướm · Lớp Mầm 2 · 30/10/2026</p>
          </div>
        </div>
        <button type="button" className="btn ghost small" onClick={() => navigate("/t01-lesson-workspace")}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
      </div>

      {/* Single switch — single .switch-track */}
      <div className="card row" style={{ justifyContent: "space-between" }}>
        <div>
          <div style={{ fontWeight: 800 }}>Bật gợi ý nét vẽ cho buổi này</div>
          <p className="muted small">Bộ gợi ý dùng nền trắng chung cho cả lớp · Không lấy hồ sơ trẻ</p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={sketchDeckEnabled}
          className="switch-wrap"
          style={{ background: "transparent", border: "none" }}
          onClick={() => setSketchDeckEnabled(!sketchDeckEnabled)}
        >
          <span className={`switch-track ${sketchDeckEnabled ? "on" : ""}`}>
            <span className="switch-thumb" />
          </span>
          <span>{sketchDeckEnabled ? "Đang bật" : "Đã tắt"}</span>
        </button>
      </div>

      {sketchDeckEnabled ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 16 }}>
          {/* 16:9 projection surface */}
          <div className="card col" style={{ gap: 12 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="video" size={16} color="var(--primary)" />
                <h3 style={{ margin: 0 }}>Bề mặt trình chiếu 16:9 · Bản {deckRevision}</h3>
              </div>
              <span className="pill ok" style={{ fontSize: 11 }}>4 bước</span>
            </div>

            <div
              style={{
                background: "#FFFFFF",
                border: "2px solid #0F172A",
                borderRadius: 14,
                aspectRatio: "16 / 9",
                padding: 20,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ fontWeight: 800, fontSize: 18, color: "#0F172A" }}>
                {deckSteps[activeDeckStep - 1].title}
              </div>

              <svg viewBox="0 0 220 110" width="240" height="120" aria-label="Minh họa nét vẽ">
                <ellipse cx="110" cy="58" rx="8" ry="32" fill="none" stroke="#0F172A" strokeWidth="3.5" />
                <circle cx="110" cy="20" r="7" fill="none" stroke="#0F172A" strokeWidth="3.5" />
                {activeDeckStep >= 2 && (
                  <>
                    <path d="M102 40 C45 10, 42 70, 102 62" fill="none" stroke="#0F172A" strokeWidth="3.5" />
                    <path d="M118 40 C175 10, 178 70, 118 62" fill="none" stroke="#0F172A" strokeWidth="3.5" />
                  </>
                )}
                {activeDeckStep >= 3 && (
                  <>
                    <path d="M102 62 C58 68, 64 102, 104 84" fill="none" stroke="#0F172A" strokeWidth="3.5" />
                    <path d="M118 62 C162 68, 156 102, 116 84" fill="none" stroke="#0F172A" strokeWidth="3.5" />
                  </>
                )}
                {activeDeckStep >= 4 && (
                  <>
                    <path d="M106 14 Q92 2 84 8" fill="none" stroke="#0F172A" strokeWidth="3" />
                    <path d="M114 14 Q128 2 136 8" fill="none" stroke="#0F172A" strokeWidth="3" />
                    <circle cx="76" cy="45" r="8" fill="none" stroke="#2563EB" strokeWidth="2.5" />
                    <circle cx="144" cy="45" r="8" fill="none" stroke="#2563EB" strokeWidth="2.5" />
                  </>
                )}
              </svg>

              <div className="small muted" style={{ fontWeight: 600 }}>
                {deckSteps[activeDeckStep - 1].hint}
              </div>
            </div>

            {/* Step thumbnails */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
              {deckSteps.map((s) => (
                <button
                  key={s.step}
                  type="button"
                  className={`btn small ${activeDeckStep === s.step ? "" : "secondary"}`}
                  onClick={() => setActiveDeckStep(s.step)}
                >
                  Bước {s.step}
                </button>
              ))}
            </div>

            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <button
                  type="button"
                  className="btn secondary small"
                  disabled={activeDeckStep <= 1}
                  onClick={() => setActiveDeckStep(Math.max(1, activeDeckStep - 1))}
                >
                  <Icon name="arrow-left" size={14} /> Trước
                </button>
                <button
                  type="button"
                  className="btn secondary small"
                  disabled={activeDeckStep >= 4}
                  onClick={() => setActiveDeckStep(Math.min(4, activeDeckStep + 1))}
                >
                  Tiếp <Icon name="arrow-right" size={14} />
                </button>
              </div>
              <button type="button" className="btn secondary small" onClick={regenerateDeckStep}>
                <Icon name="refresh" size={14} color="var(--ink-2)" /> Tạo lại bước này
              </button>
            </div>
          </div>

          {/* Right: Activities + CTAs */}
          <div className="col" style={{ gap: 14 }}>
            <div className="card col" style={{ gap: 10 }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="leaf" size={16} color="var(--mint-700)" />
                <h3 style={{ margin: 0 }}>Hoạt động trong buổi học</h3>
              </div>
              <div className="card col" style={{ padding: 12, gap: 4, background: "var(--bg)" }}>
                <div style={{ fontWeight: 700 }}>1. Quan sát vòng đời bướm</div>
                <p className="small muted">Trẻ vẽ trên giấy trắng trước khi cùng cô ra sân.</p>
              </div>
              <div className="card col" style={{ padding: 12, gap: 4, background: "var(--bg)" }}>
                <div style={{ fontWeight: 700 }}>2. Đôi cánh bướm mùa xuân</div>
                <p className="small muted">Hoạt động tập thể ngoài thảm cỏ sân trường.</p>
              </div>
            </div>

            <div className="card col" style={{ gap: 10 }}>
              <button
                type="button"
                className="btn block"
                onClick={() => showToast("Đang mở chế độ trình chiếu bộ gợi ý 16:9 cho Lớp Mầm 2.", "ok")}
              >
                <Icon name="play" size={16} color="#FFF" fill="#FFF" /> Trình chiếu bộ gợi ý
              </button>
              <button
                type="button"
                className="btn secondary block"
                onClick={() => navigate("/t06-sample-story-run")}
              >
                <Icon name="video" size={16} color="var(--primary)" /> Tạo video mẫu (T06)
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="card col" style={{ padding: 24, gap: 12, alignItems: "center", textAlign: "center" }}>
          <IconBadge name="palette" tone="primary" size={52} />
          <div style={{ fontWeight: 800 }}>Đã tắt gợi ý nét vẽ</div>
          <p className="muted small">
            Khi tắt, hệ thống không tạo yêu cầu sinh bộ gợi ý. Giáo viên có thể chuyển thẳng sang tạo video mẫu.
          </p>
          <button type="button" className="btn" onClick={() => navigate("/t06-sample-story-run")}>
            <Icon name="video" size={16} color="#FFF" /> Chuyển sang tạo video mẫu (T06)
          </button>
        </div>
      )}
    </div>
  );
}

/* ── T05 — Assigned Classes & Children Roster (UI08 two separate tables) ── */
export function T05ClassesAndChildrenPage() {
  const navigate = useNavigate();
  const { roster, addRosterChild, showToast } = useTeacher();
  const [filter, setFilter] = useState("Đang phụ trách");
  const [newChildLabel, setNewChildLabel] = useState("");
  const [newChildMonths, setNewChildMonths] = useState(60);
  const [selectedProfileModal, setSelectedProfileModal] = useState<string | null>(null);

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="users" tone="primary" size={44} />
          <div>
            <h1>Lớp học</h1>
            <p className="muted small">Chỉ hiển thị lớp được phân công & hồ sơ có quyền truy cập</p>
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <span className="pill ok">
            <Icon name="users" size={12} /> Lớp Mầm 2 · 24 trẻ
          </span>
          <select
            aria-label="Bộ lọc lớp"
            className="input"
            style={{ width: 170, padding: "6px 10px" }}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="Đang phụ trách">Đang phụ trách</option>
          </select>
        </div>
      </div>

      {/* Roster Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Hồ sơ trẻ</th>
              <th>Lớp</th>
              <th>Tháng tuổi</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {roster.map((row) => (
              <tr key={row.id}>
                <td style={{ fontWeight: 700 }}>{row.displayLabel}</td>
                <td>{row.className}</td>
                <td>{row.ageText}</td>
                <td>
                  {row.profileShared ? (
                    <span className="pill ok" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                      <Icon name="check" size={12} /> Được chia sẻ
                    </span>
                  ) : (
                    <span className="pill off" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                      <Icon name="lock" size={12} /> Chỉ danh sách
                    </span>
                  )}
                </td>
                <td>
                  <div className="row" style={{ gap: 6 }}>
                    <button
                      type="button"
                      className="btn small"
                      disabled={!row.profileShared}
                      onClick={() => setSelectedProfileModal(row.displayLabel)}
                    >
                      <Icon name="user" size={13} color="#FFF" /> Hồ sơ
                    </button>
                    <button
                      type="button"
                      className="btn secondary small"
                      onClick={() => navigate("/t04-session-sketch-deck")}
                    >
                      <Icon name="palette" size={13} color="var(--primary)" /> Lớp
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedProfileModal && (
        <div
          className="card col"
          style={{ borderColor: "var(--primary)", background: "var(--primary-50)", gap: 8 }}
        >
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="user" size={18} color="var(--primary)" />
              <h3 style={{ margin: 0 }}>Hồ sơ được chia sẻ: {selectedProfileModal}</h3>
            </div>
            <button type="button" className="btn ghost small" onClick={() => setSelectedProfileModal(null)}>
              <Icon name="close" size={14} /> Đóng
            </button>
          </div>
          <p className="small">
            Nhóm tuổi: 4–5 tuổi (60 tháng) · Sở thích: Thích vẽ động vật, màu sắc tươi sáng, khám phá thiên nhiên. (Không lưu ngày sinh chính xác).
          </p>
        </div>
      )}

      {/* Quick-Add Child Form */}
      <div className="card row" style={{ gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
        <div className="field" style={{ flex: 2, minWidth: 200 }}>
          <label htmlFor="roster-name">Thêm trẻ vào Lớp Mầm 2 (Tên hiển thị / Chữ viết tắt)</label>
          <input
            id="roster-name"
            className="input"
            placeholder="Ví dụ: Bé N.K"
            value={newChildLabel}
            onChange={(e) => setNewChildLabel(e.target.value)}
          />
        </div>
        <div className="field" style={{ flex: 1, minWidth: 140 }}>
          <label htmlFor="roster-months">Tháng tuổi (36–155)</label>
          <input
            id="roster-months"
            type="number"
            min={36}
            max={155}
            className="input"
            value={newChildMonths}
            onChange={(e) => setNewChildMonths(Number(e.target.value))}
          />
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => {
            if (!newChildLabel.trim()) {
              showToast("Vui lòng nhập tên hiển thị hoặc chữ viết tắt của trẻ.", "warn");
              return;
            }
            addRosterChild(newChildLabel.trim(), newChildMonths);
            setNewChildLabel("");
          }}
        >
          <Icon name="plus" size={16} color="#FFF" /> Thêm vào danh sách
        </button>
      </div>

      {/* UI08 Two Separate Access Grants Tables */}
      <AccessGrantsTablesSection />
    </div>
  );
}

/* ── T06 — One-Child Sample Story Run Review ── */
export function T06SampleStoryRunPage() {
  const navigate = useNavigate();
  const {
    followLessonDirection,
    setFollowLessonDirection,
    sampleScenes,
    sampleRewriteCount,
    sampleRewriteHint,
    setSampleRewriteHint,
    requestSampleRewrite,
    confirmSampleScript,
    showToast,
  } = useTeacher();

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="video" tone="primary" size={44} />
          <div>
            <h1>Video mẫu cho buổi học</h1>
            <p className="muted small">Vòng đời bướm · Lớp Mầm 2 · 30/10/2026</p>
          </div>
        </div>
        <span className="pill">1 video mẫu / buổi học</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.35fr", gap: 16 }}>
        {/* Left: Child selection + artwork */}
        <div className="col" style={{ gap: 14 }}>
          <div className="card col" style={{ gap: 8 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <IconBadge name="user" tone="primary" size={38} />
                <div>
                  <div style={{ fontWeight: 800 }}>Minh · 5 tuổi</div>
                  <div className="tiny muted">Học sinh đại diện Lớp Mầm 2</div>
                </div>
              </div>
              <span className="pill ok" style={{ fontSize: 11 }}>
                <Icon name="sparkle" size={11} /> Chọn ngẫu nhiên
              </span>
            </div>
            <button
              type="button"
              className="btn secondary small"
              style={{ alignSelf: "flex-start" }}
              onClick={() =>
                showToast("Đã kiểm tra danh sách đủ điều kiện: Minh · 5 tuổi được chọn cho buổi này.", "info")
              }
            >
              <Icon name="refresh" size={14} color="var(--ink-2)" /> Chọn ngẫu nhiên lại
            </button>
          </div>

          <div className="card col" style={{ gap: 10 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="image" size={16} color="var(--primary)" />
                <h3 style={{ margin: 0 }}>Tranh nguồn của trẻ</h3>
              </div>
              <span className="pill ok" style={{ fontSize: 11 }}>
                <Icon name="check" size={11} /> Đã xác nhận
              </span>
            </div>
            <img
              src="/child-butterfly-art.png"
              alt="Tranh con bướm của bé Minh"
              style={{
                width: "100%",
                maxHeight: 220,
                objectFit: "contain",
                borderRadius: 12,
                border: "1px solid var(--line)",
                background: "#FFFFFF",
              }}
            />
          </div>

          <div className="card row" style={{ justifyContent: "space-between" }}>
            <div>
              <div style={{ fontWeight: 700 }}>Theo hướng kịch bản giáo án</div>
              <div className="small muted">Dùng mục tiêu và hướng kể đã duyệt</div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={followLessonDirection}
              className="switch-wrap"
              style={{ background: "transparent", border: "none" }}
              onClick={() => setFollowLessonDirection(!followLessonDirection)}
            >
              <span className={`switch-track ${followLessonDirection ? "on" : ""}`}>
                <span className="switch-thumb" />
              </span>
            </button>
          </div>
        </div>

        {/* Right: 5 read-only scenes + AI rewrite + confirm */}
        <div className="col" style={{ gap: 14 }}>
          <div className="card col" style={{ gap: 10 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="book" size={16} color="var(--primary)" />
                <h2 style={{ margin: 0 }}>Kịch bản phân cảnh</h2>
              </div>
              <span className="pill">5 cảnh</span>
            </div>

            <div className="col" style={{ gap: 8 }}>
              {sampleScenes.map((sc) => (
                <div
                  key={sc.index}
                  className="row"
                  style={{
                    padding: "10px 12px",
                    borderRadius: 10,
                    border: "1px solid var(--line)",
                    background: "var(--bg)",
                    alignItems: "flex-start",
                    gap: 10,
                  }}
                >
                  <span
                    style={{
                      width: 26,
                      height: 26,
                      borderRadius: 999,
                      background: "var(--primary-50)",
                      color: "var(--primary)",
                      fontWeight: 800,
                      fontSize: 12,
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {sc.index}
                  </span>
                  <div className="col" style={{ gap: 2 }}>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{sc.title}</div>
                    <div className="small muted">{sc.narration}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card col" style={{ gap: 10 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <label htmlFor="t06-rewrite" style={{ fontWeight: 700 }}>
                <Icon name="wand" size={15} color="var(--primary)" /> Gợi ý viết lại cho AI
              </label>
              <span className={`pill ${sampleRewriteCount >= 3 ? "off" : "warn"}`}>
                {sampleRewriteCount}/3
              </span>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <input
                id="t06-rewrite"
                className="input"
                value={sampleRewriteHint}
                onChange={(e) => setSampleRewriteHint(e.target.value)}
              />
              <button
                type="button"
                className="btn secondary"
                style={{ whiteSpace: "nowrap" }}
                disabled={sampleRewriteCount >= 3}
                onClick={requestSampleRewrite}
              >
                Gửi
              </button>
            </div>

            <button
              type="button"
              className="btn block"
              style={{ marginTop: 4 }}
              onClick={() => {
                confirmSampleScript();
                navigate("/t07-video-presentation-confirmation");
              }}
            >
              <Icon name="check" size={16} color="#FFF" /> Xác nhận kịch bản & tạo video
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── T07 — Sample Video Preview & Classroom Presentation Confirmation ── */
export function T07VideoPresentationConfirmationPage() {
  const navigate = useNavigate();
  const {
    presentationConfirmed,
    confirmClassroomPresentation,
    captionsOn,
    setCaptionsOn,
  } = useTeacher();

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="video" tone="mint" size={44} />
          <div>
            <h1>Video mẫu sẵn sàng</h1>
            <p className="muted small">Vòng đời bướm · Lớp Mầm 2 · 30/10/2026</p>
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <span className="pill"><Icon name="lock" size={12} /> Video riêng tư</span>
          <span className="pill ok"><Icon name="check" size={12} /> Đã qua kiểm tra an toàn</span>
        </div>
      </div>

      {/* 16:9 Classroom Player */}
      <div className="card col" style={{ padding: 18, background: "#0F172A", color: "#FFFFFF", gap: 12 }}>
        <div
          style={{
            position: "relative",
            borderRadius: 14,
            overflow: "hidden",
            background: "#FFFBF7",
            aspectRatio: "16 / 9",
            maxHeight: 420,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <img
            src="/child-butterfly-art.png"
            alt="Video mẫu từ tranh con bướm của bé Minh"
            style={{ width: "80%", height: "80%", objectFit: "contain" }}
          />
          {captionsOn && (
            <div
              style={{
                position: "absolute",
                bottom: 14,
                left: 24,
                right: 24,
                background: "rgba(15, 23, 42, 0.84)",
                color: "#FFFFFF",
                padding: "8px 14px",
                borderRadius: 10,
                fontSize: 14,
                textAlign: "center",
              }}
            >
              "Từ chiếc kén nhỏ trên cành cây, chú bướm mang đôi cánh màu sáp bay lên..."
            </div>
          )}
        </div>

        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <div className="row" style={{ gap: 8, color: "#CBD5E1", fontSize: 13 }}>
            <Icon name="play" size={16} color="#CBD5E1" fill="#CBD5E1" />
            <span>0:00 / 1:00 · Lời kể tiếng Việt trung tính</span>
          </div>
          <button
            type="button"
            className="btn secondary small"
            style={{
              background: captionsOn ? "var(--primary)" : "#334155",
              color: "#FFFFFF",
              borderColor: "transparent",
            }}
            onClick={() => setCaptionsOn(!captionsOn)}
          >
            CC · {captionsOn ? "Đang bật" : "Đã tắt"}
          </button>
        </div>
      </div>

      {/* Presentation Confirmation */}
      <div className="card row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div className="row" style={{ gap: 8, marginBottom: 4 }}>
            <Icon name="check" size={18} color="var(--primary)" />
            <h2 style={{ margin: 0 }}>Xác nhận trình chiếu tại lớp</h2>
          </div>
          <p className="muted small">
            Ghi nhận trình chiếu video mẫu cho Lớp Mầm 2. Không tạo liên kết công khai hay tải tệp xuống.
          </p>
        </div>
        <div className="row" style={{ gap: 10 }}>
          <button
            type="button"
            className="btn secondary"
            onClick={() => navigate("/t04-session-sketch-deck")}
          >
            <Icon name="arrow-left" size={16} color="var(--ink-2)" /> Quay lại buổi học
          </button>
          <button type="button" className="btn" onClick={confirmClassroomPresentation}>
            {presentationConfirmed ? (
              <><Icon name="check" size={16} color="#FFF" /> Đã xác nhận trình chiếu</>
            ) : (
              <><Icon name="play" size={16} color="#FFF" fill="#FFF" /> Xác nhận trình chiếu</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
