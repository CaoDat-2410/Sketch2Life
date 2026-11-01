import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import { Icon, IconBadge } from "../components/Icon";

/* M01 — School Manager Public Lesson Review (m01-publication-review + UI03 Specimen 1) */
export function M01PublicationReviewPage({
  showToast,
}: {
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}) {
  const [activeTab, setActiveTab] = useState<"CONTENT" | "DIFF">("CONTENT");
  // All 4 checklist items start UNCHECKED per M01 & UI03 requirements
  const [checks, setChecks] = useState([false, false, false, false]);
  const [feedback, setFeedback] = useState("");
  const [status, setStatus] = useState<"Chờ duyệt" | "Đã duyệt công khai" | "Yêu cầu chỉnh sửa">("Chờ duyệt");
  const [decisionDialogOpen, setDecisionDialogOpen] = useState(false);

  const checklistLabels = [
    "Nội dung và ngôn ngữ phù hợp độ tuổi mầm non (4–5 tuổi)",
    "Không chứa dữ liệu cá nhân hoặc hình ảnh trẻ thật trong giáo án",
    "Các hoạt động ngoài trời có đầy đủ vật liệu và lưu ý an toàn",
    "Mục tiêu bài học và các bước hướng dẫn vẽ rõ ràng, đúng phạm vi",
  ];

  const allChecked = checks.every(Boolean);
  const checkedCount = checks.filter(Boolean).length;

  const toggleCheck = (idx: number) => {
    setChecks((prev) => prev.map((v, i) => (i === idx ? !v : v)));
  };

  return (
    <div className="col" style={{ gap: 18 }}>
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div className="row" style={{ gap: 12 }}>
          <IconBadge name="check" tone="primary" size={44} />
          <div>
            <h1>Duyệt công khai</h1>
            <p className="muted small">Kiểm tra phiên bản giáo án trước khi mở phạm vi Công khai</p>
          </div>
        </div>
        <button
          type="button"
          className="btn secondary small"
          onClick={() => setDecisionDialogOpen(true)}
        >
          <Icon name="sparkle" size={14} color="var(--primary)" /> Hộp thoại quyết định (UI03)
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16 }}>
        {/* Left Queue Panel */}
        <div className="card col" style={{ gap: 12, alignSelf: "flex-start" }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row" style={{ gap: 8 }}>
              <Icon name="clock" size={16} color="var(--warn-700)" />
              <h2 style={{ margin: 0 }}>Chờ duyệt</h2>
            </div>
            <span className="pill warn">1</span>
          </div>

          <div
            className="card col"
            style={{
              padding: 14,
              gap: 8,
              borderColor: "var(--primary)",
              background: "linear-gradient(135deg, var(--primary-50) 0%, #FFFFFF 100%)",
            }}
          >
            <div className="row" style={{ gap: 10 }}>
              <IconBadge name="book" tone="primary" size={38} />
              <div>
                <div style={{ fontWeight: 800 }}>Vòng đời bướm · Bản 3</div>
                <div className="tiny muted">Cô Thảo · Mầm non Ánh Dương</div>
              </div>
            </div>
            <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
              <span className="pill" style={{ fontSize: 11 }}>Trong trường</span>
              <Icon name="arrow-right" size={12} color="var(--ink-3)" />
              <span className="pill warn" style={{ fontSize: 11 }}>Công khai</span>
            </div>
          </div>
        </div>

        {/* Right Review Detail & Checklist */}
        <div className="col" style={{ gap: 16 }}>
          <div className="card col" style={{ gap: 14 }}>
            <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div className="row" style={{ gap: 10 }}>
                <IconBadge name="book" tone="mint" size={42} />
                <div>
                  <h2 style={{ margin: 0 }}>Vòng đời bướm · Bản 3</h2>
                  <p className="muted small">Cô Thảo · Cập nhật 30/10/2026</p>
                </div>
              </div>
              <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                <span className="pill"><Icon name="lock" size={12} /> Hiện tại: Trong trường</span>
                <span className="pill warn"><Icon name="share" size={12} /> Yêu cầu: Công khai</span>
                <span className={`pill ${status === "Đã duyệt công khai" ? "ok" : "warn"}`}>
                  <Icon name={status === "Đã duyệt công khai" ? "check" : "clock"} size={12} /> {status}
                </span>
              </div>
            </div>

            {/* Tabs */}
            <div className="row" style={{ gap: 8 }}>
              <button
                type="button"
                className={`btn small ${activeTab === "CONTENT" ? "" : "secondary"}`}
                onClick={() => setActiveTab("CONTENT")}
              >
                <Icon name="book" size={14} color={activeTab === "CONTENT" ? "#FFF" : "var(--primary)"} /> Nội dung
              </button>
              <button
                type="button"
                className={`btn small ${activeTab === "DIFF" ? "" : "secondary"}`}
                onClick={() => setActiveTab("DIFF")}
              >
                <Icon name="refresh" size={14} color={activeTab === "DIFF" ? "#FFF" : "var(--primary)"} /> So sánh phiên bản
              </button>
            </div>

            {activeTab === "CONTENT" ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div className="card col" style={{ background: "var(--bg)", gap: 6, padding: 14 }}>
                  <div className="row" style={{ gap: 8 }}>
                    <Icon name="palette" size={16} color="var(--primary)" />
                    <h3 style={{ margin: 0 }}>Mục tiêu & 4 bước vẽ (4–5 tuổi)</h3>
                  </div>
                  <p className="small muted">
                    Nhận biết 4 giai đoạn (trứng, sâu, nhộng, bướm) và vẽ bướm theo 4 bước trên giấy A4.
                  </p>
                </div>
                <div className="card col" style={{ background: "var(--bg)", gap: 6, padding: 14 }}>
                  <div className="row" style={{ gap: 8 }}>
                    <Icon name="leaf" size={16} color="var(--mint-700)" />
                    <h3 style={{ margin: 0 }}>Hoạt động ngoài trời & An toàn</h3>
                  </div>
                  <p className="small muted">
                    1. Quan sát vườn trường bằng kính lúp nhựa.<br />
                    2. Vận động Đôi cánh bướm trên sân cỏ phẳng.
                  </p>
                </div>
              </div>
            ) : (
              <div className="card col" style={{ background: "var(--bg)", gap: 8, padding: 14 }}>
                <div className="row" style={{ gap: 8 }}>
                  <Icon name="sparkle" size={16} color="var(--primary)" />
                  <h3 style={{ margin: 0 }}>Bản 2 (Trong trường) → Bản 3 (Công khai)</h3>
                </div>
                <p className="small">+ Bổ sung lưu ý an toàn sân vườn cho hoạt động Quan sát vòng đời bướm.</p>
                <p className="small">+ Chuẩn hóa 4 bước vẽ con bướm cho nhóm 4–5 tuổi (Mẫu giáo).</p>
              </div>
            )}
          </div>

          {/* 4 Required Checklist Items (Start unchecked; Approve disabled until all 4 pass) */}
          <div className="card col" style={{ gap: 12 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 8 }}>
                <IconBadge name="check" tone={allChecked ? "mint" : "accent"} size={36} />
                <div>
                  <h2 style={{ margin: 0 }}>Danh mục kiểm tra bắt buộc</h2>
                  <p className="tiny muted">Xác nhận đủ 4 mục để mở nút Duyệt công khai</p>
                </div>
              </div>
              <span className={`pill ${allChecked ? "ok" : "warn"}`}>{checkedCount}/4 mục</span>
            </div>

            <div className="col" style={{ gap: 8 }}>
              {checklistLabels.map((label, idx) => (
                <label
                  key={idx}
                  className="row"
                  style={{
                    padding: "11px 14px",
                    borderRadius: 12,
                    border: checks[idx] ? "1.5px solid var(--mint-700)" : "1px solid var(--line)",
                    background: checks[idx] ? "var(--mint-50)" : "#FFFFFF",
                    cursor: "pointer",
                    fontWeight: 600,
                    gap: 10,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checks[idx]}
                    onChange={() => toggleCheck(idx)}
                    style={{ width: 18, height: 18 }}
                  />
                  <span style={{ flex: 1 }}>{label}</span>
                  {checks[idx] && <Icon name="check" size={16} color="var(--mint-700)" />}
                </label>
              ))}
            </div>

            <div className="field" style={{ marginTop: 4 }}>
              <label htmlFor="m01-feedback">Phản hồi cho giáo viên</label>
              <textarea
                id="m01-feedback"
                className="input"
                rows={2}
                placeholder="Ghi chú hoặc nội dung cần Cô Thảo chỉnh sửa..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
              />
            </div>

            <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
              <button
                type="button"
                className="btn secondary"
                onClick={() => {
                  setStatus("Yêu cầu chỉnh sửa");
                  showToast("Đã gửi yêu cầu chỉnh sửa cho Cô Thảo (Vòng đời bướm · Bản 3).", "warn");
                }}
              >
                <Icon name="message" size={16} color="var(--ink-2)" /> Yêu cầu chỉnh sửa
              </button>
              <button
                type="button"
                className="btn"
                disabled={!allChecked}
                onClick={() => {
                  setStatus("Đã duyệt công khai");
                  showToast("Đã duyệt công khai giáo án Vòng đời bướm · Bản 3.", "ok");
                }}
              >
                <Icon name="check" size={16} color="#FFF" /> Duyệt công khai
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* UI03 Specimen 1 Modal */}
      {decisionDialogOpen && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15,23,42,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
        >
          <div className="card col" style={{ width: 520, padding: 24, gap: 14 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row" style={{ gap: 10 }}>
                <IconBadge name="check" tone="primary" size={38} />
                <h2 style={{ margin: 0 }}>Quản lý trường · Duyệt công khai</h2>
              </div>
              <span className="pill">Vòng đời bướm · Bản 3</span>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <span className="pill">Hiện tại: Trong trường</span>
              <Icon name="arrow-right" size={14} color="var(--ink-3)" />
              <span className="pill warn">Yêu cầu: Công khai</span>
            </div>
            <div className="col" style={{ gap: 8 }}>
              {checklistLabels.map((lbl, idx) => (
                <label key={idx} className="row small" style={{ fontWeight: 600, gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={checks[idx]}
                    onChange={() => toggleCheck(idx)}
                  />
                  <span>{lbl}</span>
                </label>
              ))}
            </div>
            <div className="row" style={{ justifyContent: "flex-end", gap: 10, marginTop: 6 }}>
              <button
                type="button"
                className="btn ghost"
                onClick={() => setDecisionDialogOpen(false)}
              >
                Đóng
              </button>
              <button
                type="button"
                className="btn secondary"
                onClick={() => {
                  setStatus("Yêu cầu chỉnh sửa");
                  setDecisionDialogOpen(false);
                  showToast("Đã gửi yêu cầu chỉnh sửa cho Cô Thảo.", "warn");
                }}
              >
                Yêu cầu chỉnh sửa
              </button>
              <button
                type="button"
                className="btn"
                disabled={!allChecked}
                onClick={() => {
                  setStatus("Đã duyệt công khai");
                  setDecisionDialogOpen(false);
                  showToast("Đã duyệt công khai Vòng đời bướm · Bản 3.", "ok");
                }}
              >
                <Icon name="check" size={16} color="#FFF" /> Duyệt công khai
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* M02 — School Manager Organization Management (m02-organization-management + Sidebar Sections + UI08) */
export function M02OrganizationManagementPage({
  showToast,
}: {
  showToast: (text: string, kind?: "ok" | "info" | "warn" | "err") => void;
}) {
  const location = useLocation();
  const activeSection = new URLSearchParams(location.search).get("section") || "overview";

  const [classes, setClasses] = useState([
    {
      id: "cls-1",
      name: "Lớp Mầm 2",
      level: "Mẫu giáo (4–5 tuổi)",
      teacher: "Cô Thảo",
      childrenCount: 24,
      parentGroup: "Nhóm phụ huynh Lớp Mầm 2",
      status: "Đang hoạt động",
    },
    {
      id: "cls-2",
      name: "Lớp Lá 1",
      level: "Mẫu giáo lớn (5–6 tuổi)",
      teacher: "Cô Mai",
      childrenCount: 22,
      parentGroup: "Nhóm phụ huynh Lớp Lá 1",
      status: "Đang hoạt động",
    },
  ]);

  const [schoolGrants, setSchoolGrants] = useState([
    {
      id: "sg-1",
      recipient: "Nhóm phụ huynh Lớp Mầm 2",
      scope: "Giáo án: Vòng đời bướm · Bản 3",
      expiresAt: "30/11/2026",
      status: "Đang hiệu lực" as "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi",
    },
    {
      id: "sg-2",
      recipient: "Nhóm phụ huynh Lớp Lá 1",
      scope: "Giáo án: Cây xanh quanh lớp · Bản 1",
      expiresAt: "15/11/2026",
      status: "Đang chờ" as "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi",
    },
    {
      id: "sg-3",
      recipient: "Nhóm phụ huynh Lớp Chồi 1",
      scope: "Giáo án: Vòng đời bướm · Bản 2",
      expiresAt: "15/10/2026",
      status: "Đã thu hồi" as "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi",
    },
  ]);

  const [usedSlots, setUsedSlots] = useState(8);
  const totalSlots = 10;

  return (
    <div className="col" style={{ gap: 20 }}>
      {/* Hero Banner */}
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
            <h1 style={{ color: "#FFFFFF", margin: 0 }}>Quản lý trường</h1>
            <div style={{ fontSize: 13, opacity: 0.85 }}>
              Trường Mầm non Ánh Dương · Giáo viên, lớp học & hạn mức
            </div>
          </div>
        </div>
        <div className="row" style={{ gap: 10 }}>
          <button
            type="button"
            className="btn secondary small"
            style={{ background: "rgba(255,255,255,0.16)", borderColor: "rgba(255,255,255,0.3)", color: "#FFF" }}
            onClick={() =>
              showToast("Đang hiển thị chi tiết 86 lượt tạo video còn lại của trường (số liệu minh họa).", "info")
            }
          >
            <Icon name="video" size={15} color="#FFF" /> Xem quota
          </button>
          <button
            type="button"
            style={{
              background: usedSlots >= totalSlots ? "rgba(255,255,255,0.4)" : "#FFFFFF",
              color: "var(--primary)",
              border: "none",
              borderRadius: 12,
              padding: "9px 18px",
              fontWeight: 800,
              fontSize: 14,
              cursor: usedSlots >= totalSlots ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
            disabled={usedSlots >= totalSlots}
            onClick={() => {
              if (usedSlots >= totalSlots) return;
              const nextNum = classes.length + 1;
              setClasses((prev) => [
                ...prev,
                {
                  id: `cls-${Date.now()}`,
                  name: `Lớp Chồi ${nextNum}`,
                  level: "Mẫu giáo (4–5 tuổi)",
                  teacher: "Cô Lan",
                  childrenCount: 20,
                  parentGroup: `Nhóm phụ huynh Lớp Chồi ${nextNum}`,
                  status: "Đang hoạt động",
                },
              ]);
              setUsedSlots((s) => s + 1);
              showToast("Đã thêm lớp mới trong hạn mức slot của trường.", "ok");
            }}
          >
            <Icon name="plus" size={15} color="var(--primary)" /> Thêm lớp
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 14,
        }}
      >
        <div
          className="card col"
          style={{
            gap: 8,
            borderColor: activeSection === "classes" ? "var(--primary)" : "var(--line)",
          }}
        >
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="book" tone="primary" size={40} />
            <div>
              <div className="tiny muted">Sức chứa lớp học</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "var(--primary)" }}>
                {usedSlots}/{totalSlots} lớp
              </div>
            </div>
          </div>
          <div style={{ height: 6, borderRadius: 999, background: "var(--primary-50)", overflow: "hidden" }}>
            <div
              style={{
                width: `${(usedSlots / totalSlots) * 100}%`,
                height: "100%",
                background: "var(--primary)",
                borderRadius: 999,
              }}
            />
          </div>
          <span className="tiny muted">Còn {totalSlots - usedSlots} slot khả dụng</span>
        </div>

        <div
          className="card col"
          style={{
            gap: 8,
            borderColor: activeSection === "quota" ? "var(--primary)" : "var(--line)",
          }}
        >
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="video" tone="mint" size={40} />
            <div>
              <div className="tiny muted">Quota video trường</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "var(--mint-700)" }}>
                86 lượt còn
              </div>
            </div>
          </div>
          <span className="tiny muted">Dùng cho tạo video mẫu theo buổi học</span>
        </div>

        <div
          className="card col"
          style={{
            gap: 8,
            borderColor: activeSection === "teachers" ? "var(--primary)" : "var(--line)",
          }}
        >
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="users" tone="accent" size={40} />
            <div>
              <div className="tiny muted">Giáo viên</div>
              <div style={{ fontWeight: 800 }}>8 thành viên</div>
            </div>
          </div>
          <button
            type="button"
            className="btn secondary small"
            style={{ alignSelf: "flex-start" }}
            onClick={() =>
              showToast("Đã gửi email mời giáo viên xác minh tài khoản vào Trường Mầm non Ánh Dương.", "ok")
            }
          >
            <Icon name="plus" size={14} color="var(--primary)" /> Mời giáo viên
          </button>
        </div>

        <div
          className="card col"
          style={{
            gap: 8,
            borderColor: activeSection === "teachers" ? "var(--primary)" : "var(--line)",
          }}
        >
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="share" tone="primary" size={40} />
            <div>
              <div className="tiny muted">Nhóm phụ huynh</div>
              <div style={{ fontWeight: 800 }}>4 nhóm trường</div>
            </div>
          </div>
          <button
            type="button"
            className="btn secondary small"
            style={{ alignSelf: "flex-start" }}
            onClick={() =>
              showToast("Nhóm phụ huynh dùng để cấp quyền bài học theo lớp, không sở hữu tài khoản phụ huynh.", "info")
            }
          >
            <Icon name="settings" size={14} color="var(--primary)" /> Quản lý nhóm
          </button>
        </div>
      </div>

      {/* Classes Table */}
      <div
        className="card col"
        style={{
          gap: 12,
          borderColor: activeSection === "classes" ? "var(--primary)" : "var(--line)",
        }}
      >
        <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="book" tone="primary" size={38} />
            <div>
              <h2 style={{ margin: 0 }}>Danh sách lớp học & phân công</h2>
              <div className="tiny muted">Không truy cập media riêng tư của trẻ</div>
            </div>
          </div>
          <span className="pill ok"><Icon name="lock" size={12} /> Tách biệt dữ liệu trẻ</span>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Tên lớp</th>
              <th>Khối / Độ tuổi</th>
              <th>Giáo viên</th>
              <th>Sĩ số</th>
              <th>Nhóm phụ huynh</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {classes.map((c) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 700 }}>{c.name}</td>
                <td>{c.level}</td>
                <td>{c.teacher}</td>
                <td>{c.childrenCount} trẻ</td>
                <td>{c.parentGroup}</td>
                <td>
                  <span className="pill ok" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    <Icon name="check" size={12} /> {c.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* UI08 Lesson Access Grants Table for the School */}
      <div
        className="card col"
        style={{
          gap: 12,
          borderColor:
            activeSection === "teachers" || activeSection === "settings"
              ? "var(--primary)"
              : "var(--line)",
        }}
      >
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 10 }}>
            <IconBadge name="share" tone="mint" size={38} />
            <div>
              <h2 style={{ margin: 0 }}>Chia sẻ giáo án theo nhóm phụ huynh (Bảng UI08)</h2>
              <p className="tiny muted">Nhóm phụ huynh nhận quyền bài học của trường</p>
            </div>
          </div>
          <span className="pill">Trường Mầm non Ánh Dương</span>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Người nhận</th>
              <th>Phạm vi chia sẻ</th>
              <th>Hết hạn</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {schoolGrants.map((g) => (
              <tr key={g.id}>
                <td style={{ fontWeight: 700 }}>{g.recipient}</td>
                <td>{g.scope}</td>
                <td>{g.expiresAt}</td>
                <td>
                  <span
                    className={`pill ${
                      g.status === "Đang hiệu lực"
                        ? "ok"
                        : g.status === "Đang chờ"
                        ? "warn"
                        : "off"
                    }`}
                    style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                  >
                    <Icon
                      name={g.status === "Đang hiệu lực" ? "check" : g.status === "Đang chờ" ? "clock" : "close"}
                      size={12}
                    />
                    {g.status}
                  </span>
                </td>
                <td>
                  {g.status === "Đang hiệu lực" ? (
                    <button
                      type="button"
                      className="btn danger small"
                      onClick={() => {
                        setSchoolGrants((prev) =>
                          prev.map((row) =>
                            row.id === g.id ? { ...row, status: "Đã thu hồi" } : row
                          )
                        );
                        showToast("Đã thu hồi quyền chia sẻ bài học của nhóm.", "info");
                      }}
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
