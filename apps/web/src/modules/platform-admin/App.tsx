import "./styles/tokens.css";
import "./styles/mg-manage.css";
import "./styles/admin-rebuild.css";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { WebAppShell, PLATFORM_ADMIN_NAVIGATION } from "../../shared/WebAppShell";
import { usePortalSession } from "../../shared/PortalSessionContext";
import { RoleMismatchPage } from "../../shared/RoleMismatchPage";
import { A01ContentModerationPage, A02PlatformOperationsPage } from "./pages/AdminScreens";
import { UsersPage } from "./pages/UsersPage";

export function PlatformAdminApp() {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentRole, isAuthenticated, toast, logout } = usePortalSession();
  if (isAuthenticated && currentRole !== "ADMIN") return <RoleMismatchPage roleLabel="Quản trị nền tảng" onLogout={logout} />;
  if (!isAuthenticated) return <Navigate to="/login?role=admin" replace />;
  if (location.pathname === "/platform" || location.pathname === "/platform/") return <Navigate to="/platform/a02-platform-operations" replace />;
  const page = location.pathname === "/platform/accounts"
    ? <UsersPage />
    : location.pathname === "/platform/a01-content-moderation"
    ? <A01ContentModerationPage />
    : location.pathname === "/platform/a02-platform-operations"
      ? <A02PlatformOperationsPage />
      : <Navigate to="/platform/a02-platform-operations" replace />;

  return (
    <WebAppShell
      roleLabel="Platform Admin"
      roleSubtitle="Vận hành nền tảng · nội dung theo quyền"
      navigation={PLATFORM_ADMIN_NAVIGATION}
      loginHref="/login?role=admin"
      modeLabel="Phiên đã xác minh"
      toast={toast}
      onLogout={() => { logout(); navigate("/login?role=admin"); }}
    >
      {page}
    </WebAppShell>
  );
}

export default PlatformAdminApp;
