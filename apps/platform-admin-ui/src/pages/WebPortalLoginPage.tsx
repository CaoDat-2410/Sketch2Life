import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTeacher, WebPortalRole } from "../context/TeacherContext";
import { Logo } from "../components/Logo";
import { Icon, IconName } from "../components/Icon";

const ROLE_ACCOUNTS: Record<
  WebPortalRole,
  {
    title: string;
    email: string;
    icon: IconName;
    avatarTone: string;
    badgeTone: string;
    targetRoute: string;
    desc: string;
  }
> = {
  TEACHER: {
    title: "Giáo viên",
    email: "colan@anhduong.edu.vn",
    icon: "palette",
    avatarTone: "is-sky",
    badgeTone: "",
    targetRoute: "/t01-lesson-workspace",
    desc: "Quản lý lớp, giáo án, AI Assisted và tạo video mẫu",
  },
  MANAGER: {
    title: "Quản lý trường",
    email: "hieutruong@anhduong.edu.vn",
    icon: "users",
    avatarTone: "is-mint",
    badgeTone: "is-mint",
    targetRoute: "/m02-organization-management",
    desc: "Quản lý slot lớp, phân công giáo viên, quota và duyệt giáo án công khai",
  },
  ADMIN: {
    title: "Quản trị nền tảng",
    email: "admin@sketch2life.vn",
    icon: "lock",
    avatarTone: "is-amber",
    badgeTone: "is-amber",
    targetRoute: "/a02-platform-operations",
    desc: "Vận hành hệ thống, danh mục hoạt động chuẩn và kiểm duyệt nội dung",
  },
};

const CLASS_VISUALS: { icon: IconName; tone: "" | "is-amber" | "is-mint"; alias: string }[] = [
  { icon: "sun", tone: "is-amber", alias: "Lớp Mặt Trời" },
  { icon: "sparkle", tone: "", alias: "Lớp Cầu Vồng" },
  { icon: "star", tone: "is-mint", alias: "Lớp Ngôi Sao" },
];

function detectRoleFromEmail(email: string, fallback: WebPortalRole): WebPortalRole {
  const lower = email.trim().toLowerCase();
  if (lower.includes("admin") || lower.includes("quantri")) return "ADMIN";
  if (lower.includes("quanly") || lower.includes("hieutruong") || lower.includes("manager")) return "MANAGER";
  if (lower.includes("gv") || lower.includes("co") || lower.includes("teacher")) return "TEACHER";
  return fallback;
}

export function WebPortalLoginPage() {
  const navigate = useNavigate();
  const { loginAsRole, assignedClasses, activeClassId, setActiveClassId, showToast } = useTeacher();

  const [step, setStep] = useState<"LOGIN" | "SELECT_CLASS">("LOGIN");
  const [selectedRole, setSelectedRole] = useState<WebPortalRole>("TEACHER");
  const [email, setEmail] = useState(ROLE_ACCOUNTS.TEACHER.email);
  const [password, setPassword] = useState("••••••••");
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [organization, setOrganization] = useState("Trường Mầm non Ánh Dương");
  const [pickedClassId, setPickedClassId] = useState(activeClassId || assignedClasses[0]?.id || "");
  const [isLoading, setIsLoading] = useState(false);

  const handleQuickFill = (role: WebPortalRole) => {
    setSelectedRole(role);
    setEmail(ROLE_ACCOUNTS[role].email);
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const resolvedRole = detectRoleFromEmail(email, selectedRole);
    setSelectedRole(resolvedRole);
    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      if (resolvedRole === "TEACHER") {
        setStep("SELECT_CLASS");
      } else {
        loginAsRole(resolvedRole, email);
        navigate(ROLE_ACCOUNTS[resolvedRole].targetRoute);
      }
    }, 300);
  };

  const handleEnterClass = (targetClassId?: string) => {
    const finalClassId = targetClassId || pickedClassId || assignedClasses[0]?.id;
    loginAsRole("TEACHER", email);
    if (finalClassId) setActiveClassId(finalClassId);
    navigate("/t01-lesson-workspace");
  };

  const resolvedRole = detectRoleFromEmail(email, selectedRole);

  return (
    <div className="tw-hero-bg">
      <div className="tw-grid-2" style={{ maxWidth: 980, width: "100%", gap: 28, alignItems: "stretch" }}>
        {/* Cột trái: Thương hiệu & Chọn nhanh tài khoản mẫu */}
        <div
          className="tw-card is-sky"
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            gap: 20,
            padding: 34,
          }}
        >
          <div className="tw-row tw-between">
            <Logo height={38} />
            <span className="tw-chip">Cổng Web thống nhất</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="tw-row" style={{ gap: 14 }}>
              <span className="tw-avatar tw-float" style={{ width: 68, height: 68 }} aria-hidden="true">
                <Icon name="palette" size={30} />
              </span>
              <span className="tw-avatar is-mint" style={{ width: 58, height: 58 }} aria-hidden="true">
                <Icon name="sparkle" size={26} />
              </span>
              <span className="tw-avatar is-sky" style={{ width: 58, height: 58 }} aria-hidden="true">
                <Icon name="video" size={26} />
              </span>
            </div>
            <h1 className="tw-title" style={{ fontSize: 30, lineHeight: 1.2 }}>
              Khơi nguồn câu chuyện
              <br />
              từ nét vẽ tuổi thơ
            </h1>
            <p className="tw-sub" style={{ fontSize: 14.5, maxWidth: "46ch" }}>
              Một cổng đăng nhập duy nhất dành cho Giáo viên, Quản lý trường và Quản trị viên nền tảng.
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>
              Chọn nhanh tài khoản mẫu để trải nghiệm
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(Object.keys(ROLE_ACCOUNTS) as WebPortalRole[]).map((r) => {
                const acc = ROLE_ACCOUNTS[r];
                const active = selectedRole === r && step === "LOGIN";
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => {
                      handleQuickFill(r);
                      setStep("LOGIN");
                    }}
                    className={"tw-item is-lift tw-row tw-between" + (active ? " is-selected" : "")}
                    style={{
                      padding: "11px 14px",
                      borderRadius: 18,
                      textAlign: "left",
                      fontFamily: "inherit",
                    }}
                  >
                    <div className="tw-row" style={{ gap: 10 }}>
                      <span className={`tw-avatar is-sm ${acc.avatarTone}`} style={{ width: 38, height: 38 }} aria-hidden="true">
                        <Icon name={acc.icon} size={18} />
                      </span>
                      <div>
                        <div className="tw-strong" style={{ fontSize: 14 }}>{acc.title}</div>
                        <div className="tw-meta" style={{ fontSize: 12.5 }}>{acc.email}</div>
                      </div>
                    </div>
                    <span className={"tw-chip " + acc.badgeTone}>
                      {active ? "Đang chọn" : "Điền nhanh"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Cột phải: Bước 1 (Đăng nhập) hoặc Bước 2 (Chọn tổ chức & lớp học) */}
        {step === "LOGIN" ? (
          <form
            onSubmit={handleLoginSubmit}
            className="tw-card"
            style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 16, padding: 32 }}
          >
            <div className="tw-row tw-between">
              <div>
                <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>Đăng nhập cổng Web</h2>
                <p className="tw-sub" style={{ fontSize: 13.5, marginTop: 4 }}>
                  Hệ thống tự động nhận diện quyền Giáo viên, Quản lý trường hoặc Admin.
                </p>
                <div className="tw-row tw-wrap" style={{ marginTop: 8, gap: 8 }}>
                  <span className="tw-chip">Bước 1 / 2 · Xác thực tài khoản</span>
                </div>
              </div>
              <span className={`tw-avatar is-sm ${ROLE_ACCOUNTS[resolvedRole].avatarTone}`} aria-hidden="true">
                <Icon name={ROLE_ACCOUNTS[resolvedRole].icon} size={20} />
              </span>
            </div>

            <label className="tw-label">
              Email tài khoản
              <input
                className="tw-input"
                type="email"
                placeholder="ten@truong.edu.vn"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setSelectedRole(detectRoleFromEmail(e.target.value, selectedRole));
                }}
                required
              />
            </label>

            <label className="tw-label">
              Mật khẩu
              <div style={{ position: "relative" }}>
                <input
                  className="tw-input"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  style={{
                    position: "absolute",
                    right: 12,
                    top: 10,
                    border: 0,
                    background: "transparent",
                    cursor: "pointer",
                    color: "var(--tw-sub-ink)",
                  }}
                >
                  <Icon name={showPassword ? "eye-off" : "eye"} size={18} />
                </button>
              </div>
            </label>

            <div className="tw-row tw-between" style={{ fontSize: 13.5 }}>
              <label className="tw-row" style={{ gap: 8, cursor: "pointer", fontWeight: 600 }}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Ghi nhớ đăng nhập</span>
              </label>
              <button
                type="button"
                onClick={() => showToast("Đã gửi liên kết đặt lại mật khẩu tới email của bạn.", "info")}
                style={{
                  border: 0,
                  background: "none",
                  color: "var(--color-accent)",
                  fontWeight: 700,
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}
              >
                Quên mật khẩu?
              </button>
            </div>

            <div className="tw-item is-sky tw-row tw-between" style={{ padding: "11px 14px", borderRadius: 16 }}>
              <span style={{ fontSize: 13.5 }}>
                Vai trò nhận diện: <strong>{ROLE_ACCOUNTS[resolvedRole].title}</strong>
              </span>
              <span className="tw-chip is-mint">Firebase Auth</span>
            </div>

            <button
              type="submit"
              className="tw-btn"
              disabled={isLoading}
              style={{ width: "100%", justifyContent: "center", marginTop: 4 }}
            >
              {isLoading ? "Đang xác thực..." : "Đăng nhập"}
            </button>
          </form>
        ) : (
          <div
            className="tw-card"
            style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 16, padding: 32 }}
          >
            <div>
              <div className="tw-row tw-between tw-wrap">
                <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>Chào mừng cô giáo!</h2>
                <button
                  type="button"
                  className="tw-btn is-ghost is-sm"
                  onClick={() => setStep("LOGIN")}
                >
                  Đổi tài khoản
                </button>
              </div>
              <p className="tw-sub" style={{ fontSize: 13.5, marginTop: 4 }}>
                Chọn trường và lớp phụ trách để mở không gian dạy học hôm nay.
              </p>
              <div className="tw-row tw-wrap" style={{ marginTop: 8 }}>
                <span className="tw-chip is-mint">Bước 2 / 2 · Chọn tổ chức &amp; lớp học</span>
              </div>
            </div>

            <label className="tw-label">
              Tổ chức / Trường mầm non
              <select
                className="tw-input"
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
              >
                <option value="Trường Mầm non Ánh Dương">Trường Mầm non Ánh Dương</option>
                <option value="Trường Mầm non Sao Mai">Trường Mầm non Sao Mai</option>
              </select>
            </label>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <h3 style={{ fontSize: 14.5, fontWeight: 700, margin: 0 }}>Lớp học được phân công</h3>
              {assignedClasses.map((cls, idx) => {
                const vis = CLASS_VISUALS[idx % CLASS_VISUALS.length];
                const selected = pickedClassId === cls.id;
                return (
                  <button
                    key={cls.id}
                    type="button"
                    onClick={() => setPickedClassId(cls.id)}
                    onDoubleClick={() => handleEnterClass(cls.id)}
                    className={"tw-item is-lift tw-row tw-between" + (selected ? " is-selected" : "")}
                    style={{
                      padding: "12px 16px",
                      borderRadius: 18,
                      textAlign: "left",
                      fontFamily: "inherit",
                    }}
                  >
                    <div className="tw-row" style={{ gap: 12 }}>
                      <span className={`tw-ico ${vis.tone}`} style={{ width: 42, height: 42, borderRadius: 14 }} aria-hidden="true">
                        <Icon name={vis.icon} size={20} />
                      </span>
                      <div>
                        <div className="tw-strong" style={{ fontSize: 15 }}>
                          {cls.className} <span className="tw-meta" style={{ fontWeight: 600 }}>({vis.alias})</span>
                        </div>
                        <div className="tw-meta" style={{ fontSize: 12.5 }}>
                          {cls.studentCount} học sinh · {cls.ageRangeLabel}
                        </div>
                      </div>
                    </div>
                    <span className={"tw-chip " + (selected ? "is-mint" : "is-gray")}>
                      {selected ? "Đã chọn" : "Chọn lớp"}
                    </span>
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              className="tw-btn"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={() => handleEnterClass(pickedClassId)}
            >
              Vào bảng điều khiển lớp học <Icon name="arrow-right" size={18} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
