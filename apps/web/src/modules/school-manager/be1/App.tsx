import type { ReactNode } from "react";
import "../styles/tokens.css";
import "../styles/mg-manage.css";
import "../styles/manager-rebuild.css";
import "../styles/manager-business.css";
import "../../../shared/styles/tailwind-utilities.css";
import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { WebAppShell, SCHOOL_MANAGER_NAVIGATION } from "../../../shared/navigation/WebAppShell";
import { FeatureAvailability, PageHeading } from "../../../shared/components/FeatureAvailability";
import { usePortalSession } from "../../../shared/auth/PortalSessionContext";
import { M01PublicationReviewPage } from "../pages/ManagerScreens";
import { SchoolOverviewPage } from "./pages/SchoolOverviewPage";
import { ClassesPage } from "./pages/ClassesPage";
import { RosterConsentPage } from "./pages/RosterConsentPage";
import { DataRequestsPage } from "./pages/DataRequestsPage";
import { ParentGroupsPage } from "./pages/ParentGroupsPage";
import { TeacherAssignmentsPage } from "./pages/TeacherAssignmentsPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import { SchoolBillingPage, SchoolQuotaPage } from "./pages/QuotaBillingPages";
import { CapacityPage } from "./pages/CapacityPage";
import { authService } from "./services/authService";
import { AdminBe1Error } from "./services/be1Client";
import { classService } from "./services/classService";
import { InboxPage } from "../../../shared/notifications/InboxPage";
import { SchoolAccountPage } from "./pages/SchoolAccountPage";

function AdminAccessGate({ children }: { children: ReactNode }) {
  const location = useLocation();
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
      if (cause instanceof AdminBe1Error && cause.status === 404) {
        setState("forbidden");
        return;
      }
      setMessage(cause instanceof Error ? cause.message : "Không xác minh được quyền quản trị nhà trường.");
      setState("error");
    });
  }), []);

  if (state === "loading") return <main className="s2l-main"><div className="s2l-data-card" role="status">Đang xác minh quyền quản lý nhà trường…</div></main>;
  if (state === "signed-out") return <Navigate to="/login?role=manager" replace state={{ from: location }} />;
  if (state === "forbidden" || state === "error") return <AccessError message={message || "Tài khoản này chưa được phân công quản lý nhà trường."} />;
  return <>{children}</>;
}

function AccessError({ message }: { message: string }) {
  const navigate = useNavigate();
  return (
    <main className="s2l-login-shell">
      <section className="s2l-data-card" style={{ width: "min(100%, 540px)" }}>
        <p className="s2l-page-eyebrow">Quản lý trường · Xác minh quyền</p>
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
      portal="manager"
      roleLabel="Quản lý trường"
      roleSubtitle="Quản lý trong phạm vi trường được xác minh"
      navigation={SCHOOL_MANAGER_NAVIGATION}
      loginHref="/login?role=manager"
      modeLabel="Phiên đã xác minh"
      toast={toast}
      onLogout={() => { void authService.logout(); navigate("/login?role=manager"); }}
    >
      {children}
    </WebAppShell>
  );
}

const UNAVAILABLE: Record<string, { title: string; requirement: string; dependencies: string[] }> = {
  billing: {
    title: "Thanh toán",
    requirement: "Nhà trường cần xem hóa đơn, trạng thái thanh toán và lịch sử đối soát.",
    dependencies: ["Chưa có dữ liệu hóa đơn, lần thanh toán và sự kiện thanh toán.", "Chỉ xác nhận trạng thái sau khi hệ thống đối soát.", "Không đưa câu chuyện hoặc hình ảnh của trẻ vào phần thanh toán."],
  },
  quota: {
    title: "Hạn mức",
    requirement: "Cần có hạn mức theo từng trường và hiển thị mức sử dụng, đối soát có nguồn.",
    dependencies: ["Chưa có bảng tổng hợp hạn mức và lịch sử cấp hạn mức.", "Cần theo dõi thay đổi chính sách và nhật ký kiểm tra.", "Cần trạng thái đối soát từ hệ thống."],
  },
};

function SchoolUnavailablePage() {
  const { pathname } = window.location;
  const feature = pathname.split("/").filter(Boolean).at(-1) ?? "";
  const panel = UNAVAILABLE[feature] ?? { title: "Chức năng trường học", requirement: "Chức năng này đang chờ dữ liệu phù hợp.", dependencies: ["Cần có dữ liệu theo phiên bản, quyền theo phạm vi trường và nhật ký kiểm tra."] };
  return (
    <div className="s2l-page">
      <PageHeading eyebrow="Quản lý trường · Đang chờ hoàn thiện" title={panel.title} description="Giao diện chỉ bật khi hệ thống xác minh được dữ liệu và quyền." />
      <FeatureAvailability title="Chưa khả dụng" summary="Hiện chỉ các thao tác có dữ liệu và phạm vi quyền đã được xác minh mới hoạt động. Chức năng khác sẽ mở khi hệ thống hỗ trợ." requirement={panel.requirement} dependencies={panel.dependencies} permissionNote="Mọi truy cập đều được hệ thống kiểm tra lại theo trường hiện tại." backTo="/school" />
    </div>
  );
}

function SchoolReviewPage() {
  const { showToast } = usePortalSession();
  return <div className="s2l-review-wrap"><M01PublicationReviewPage showToast={showToast} /></div>;
}

export function SchoolManagerBe1App() {
  const location = useLocation();

  if (location.pathname === "/school/settings") return <Navigate to="/school/account" replace />;

  let page;
  if (location.pathname === "/school" || location.pathname === "/school/") page = <SchoolOverviewPage />;
  else if (location.pathname === "/school/classes") page = <ClassesPage />;
  else if (location.pathname === "/school/teachers") page = <RosterConsentPage />;
  else if (location.pathname === "/school/data-requests") page = <DataRequestsPage />;
  else if (location.pathname === "/school/teacher-assignments") page = <TeacherAssignmentsPage />;
  else if (location.pathname === "/school/feedback") page = <FeedbackPage />;
  else if (location.pathname === "/school/teacher-groups") return <Navigate to="/school" replace />;
  else if (location.pathname === "/school/parent-groups") page = <ParentGroupsPage />;
  else if (location.pathname === "/school/capacity") page = <CapacityPage />;
  else if (location.pathname === "/school/quota") page = <SchoolQuotaPage />;
  else if (location.pathname === "/school/billing") page = <SchoolBillingPage />;
  else if (location.pathname === "/school/review-content") page = <SchoolReviewPage />;
  else if (location.pathname === "/school/inbox") page = <InboxPage />;
  else if (location.pathname === "/school/account") page = <SchoolAccountPage />;
  else if (/^\/school\/[^/]+$/.test(location.pathname)) page = <SchoolUnavailablePage />;
  else return <Navigate to="/school" replace />;

  return <AdminAccessGate><SchoolManagerFrame>{page}</SchoolManagerFrame></AdminAccessGate>;
}

export default SchoolManagerBe1App;
