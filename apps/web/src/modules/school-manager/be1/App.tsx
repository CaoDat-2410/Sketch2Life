import type { ReactNode } from "react";
import "../styles/tokens.css";
import "../styles/mg-manage.css";
import "../styles/manager-rebuild.css";
import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { WebAppShell, SCHOOL_MANAGER_NAVIGATION } from "../../../shared/WebAppShell";
import { FeatureAvailability, PageHeading } from "../../../shared/FeatureAvailability";
import { usePortalSession } from "../../../shared/PortalSessionContext";
import { M01PublicationReviewPage } from "../pages/ManagerScreens";
import { SchoolOverviewPage } from "./pages/SchoolOverviewPage";
import { ClassesPage } from "./pages/ClassesPage";
import { authService } from "./services/authService";
import { classService } from "./services/classService";

function AdminAccessGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<"loading" | "signed-out" | "authorized" | "forbidden" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => authService.observe((user) => {
    if (!user) {
      setState("signed-out");
      return;
    }
    classService.currentAssignments().then((result) => {
      const isOrgAdmin = result.assignments.some((item) => item.role === "school_admin" && item.class_id === null);
      setState(isOrgAdmin ? "authorized" : "forbidden");
    }).catch((cause: unknown) => {
      setMessage(cause instanceof Error ? cause.message : "Không xác minh được quyền quản trị BE1.");
      setState("error");
    });
  }), []);

  if (state === "loading") return <main className="s2l-main"><div className="s2l-data-card" role="status">Đang xác minh quyền school_admin qua BE1…</div></main>;
  if (state === "signed-out") return <Navigate to="/login?role=manager" replace />;
  if (state === "forbidden" || state === "error") return <AccessError message={message || "Tài khoản này chưa có phân công school_admin cấp trường trong BE1."} />;
  return <>{children}</>;
}

function AccessError({ message }: { message: string }) {
  const navigate = useNavigate();
  return (
    <main className="s2l-login-shell">
      <section className="s2l-data-card" style={{ width: "min(100%, 540px)" }}>
        <p className="s2l-page-eyebrow">School Manager · Xác minh quyền</p>
        <h1 style={{ margin: "0 0 10px", fontSize: 26 }}>Không thể mở cổng quản trị</h1>
        <p>{message}</p>
        <button type="button" className="s2l-button" onClick={() => void authService.logout().then(() => navigate("/login?role=manager", { replace: true }))}>Đăng xuất</button>
      </section>
    </main>
  );
}

function SchoolManagerFrame({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const { toast } = usePortalSession();
  return (
    <WebAppShell
      roleLabel="School Manager"
      roleSubtitle="Quản lý trường trong organization được xác minh"
      navigation={SCHOOL_MANAGER_NAVIGATION}
      loginHref="/login?role=manager"
      modeLabel="Phạm vi BE1 đã xác minh"
      toast={toast}
      onLogout={() => { void authService.logout(); navigate("/login?role=manager"); }}
    >
      {children}
    </WebAppShell>
  );
}

const UNAVAILABLE: Record<string, { title: string; requirement: string; dependencies: string[] }> = {
  teachers: {
    title: "Giáo viên & roster",
    requirement: "SRS yêu cầu quản lý giáo viên, phân công và roster theo organization; school_admin không được đọc story/media của trẻ.",
    dependencies: ["API phân công teacher có version và audit.", "API roster có consent state và scoped access.", "Contract archive/suspend và xử lý xung đột assignment."],
  },
  capacity: {
    title: "Sức chứa",
    requirement: "SRS yêu cầu xem giới hạn lớp và capacity hiện hành của trường.",
    dependencies: ["API capacity theo organization.", "Quy tắc tính lớp active, archived và suspended.", "API cập nhật capacity có audit và precondition."],
  },
  billing: {
    title: "Thanh toán",
    requirement: "School Manager cần xem invoice/payment state và lịch sử đối soát của trường.",
    dependencies: ["API invoice, payment attempt và provider event.", "Trạng thái chỉ xác nhận sau webhook đối soát.", "Không đưa child story/media vào billing views."],
  },
  quota: {
    title: "Hạn mức",
    requirement: "SRS yêu cầu quota theo organization và hiển thị usage/reconciliation có nguồn.",
    dependencies: ["API quota summary và grant history.", "Policy revision và audit trail.", "Trạng thái reconciliation từ backend."],
  },
  inbox: {
    title: "Hộp thư",
    requirement: "Thông báo cần scope theo organization và đồng bộ trạng thái đã đọc.",
    dependencies: ["API inbox phân trang.", "API read state và unread state.", "Không làm lộ notification ngoài phạm vi."],
  },
};

function SchoolUnavailablePage() {
  const { pathname } = window.location;
  const feature = pathname.split("/").filter(Boolean).at(-1) ?? "";
  const panel = UNAVAILABLE[feature] ?? { title: "Chức năng trường học", requirement: "Chưa có API contract hiện hành cho chức năng này.", dependencies: ["Versioned API, scoped authorization và audit trail."] };
  return (
    <div className="s2l-page">
      <PageHeading eyebrow="School Manager · Đang chờ API" title={panel.title} description="Giao diện chỉ bật khi dữ liệu và quyền được xác minh từ backend." />
      <FeatureAvailability title="Chưa khả dụng" summary="BE1 hiện đang nối danh sách và tạo lớp; các dịch vụ này chưa có contract trong adapter của School Manager." requirement={panel.requirement} dependencies={panel.dependencies} permissionNote="Mọi truy cập phải được backend xác minh lại theo organization hiện hành." backTo="/school" />
    </div>
  );
}

function SchoolReviewPage() {
  const { showToast } = usePortalSession();
  return <div className="s2l-review-wrap"><M01PublicationReviewPage showToast={showToast} /></div>;
}

export function SchoolManagerBe1App() {
  const location = useLocation();

  let page;
  if (location.pathname === "/school" || location.pathname === "/school/") page = <SchoolOverviewPage />;
  else if (location.pathname === "/school/classes") page = <ClassesPage />;
  else if (location.pathname === "/school/review-content") page = <SchoolReviewPage />;
  else if (/^\/school\/[^/]+$/.test(location.pathname)) page = <SchoolUnavailablePage />;
  else return <Navigate to="/school" replace />;

  return <AdminAccessGate><SchoolManagerFrame>{page}</SchoolManagerFrame></AdminAccessGate>;
}

export default SchoolManagerBe1App;
