import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { authService } from "../modules/school-manager/be1/services/authService";
import { signInAndResolveRole } from "../shared/api/backendApi";
import { usePortalSession } from "../shared/auth/PortalSessionContext";
import { WebPortalLoginPage, type WebPortalAppRole } from "../shared/auth/WebPortalLoginPage";

const ROLE_QUERY: Record<WebPortalAppRole, string> = {
  TEACHER: "teacher",
  MANAGER: "manager",
  ADMIN: "admin",
};

const ROLE_HOME: Record<WebPortalAppRole, string> = {
  TEACHER: "/teacher/t01-lesson-workspace",
  MANAGER: "/school",
  ADMIN: "/platform/a02-platform-operations",
};

const ROLE_PREFIX: Record<WebPortalAppRole, string> = {
  TEACHER: "/teacher",
  MANAGER: "/school",
  ADMIN: "/platform",
};

type LoginRedirectState = {
  from?: { pathname?: string; search?: string; hash?: string };
};

function destinationAfterLogin(role: WebPortalAppRole, from: LoginRedirectState["from"]) {
  const prefix = ROLE_PREFIX[role];
  const path = from?.pathname;
  if (!path || (path !== prefix && !path.startsWith(`${prefix}/`))) return ROLE_HOME[role];
  return `${path}${from?.search ?? ""}${from?.hash ?? ""}`;
}

function roleFromQuery(value: string | null): WebPortalAppRole {
  if (value === "manager") return "MANAGER";
  if (value === "admin") return "ADMIN";
  return "TEACHER";
}

export function PortalEntryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { loginAsRole } = usePortalSession();
  const portalRole = roleFromQuery(searchParams.get("role"));

  const selectRole = (role: WebPortalAppRole) => {
    setSearchParams({ role: ROLE_QUERY[role] }, { replace: true, state: location.state });
  };

  const authenticate = async (role: WebPortalAppRole, email: string, password: string) => {
    const accountRole = role === "TEACHER"
      ? "teacher"
      : role === "MANAGER"
        ? "school_manager"
        : "platform_admin";
    await signInAndResolveRole(accountRole, email, password);
    loginAsRole(role);
    const redirectState = location.state as LoginRedirectState | null;
    navigate(destinationAfterLogin(role, redirectState?.from), { replace: true });
  };

  return (
    <WebPortalLoginPage
      portalRole={portalRole}
      onRoleChange={selectRole}
      onAuthenticate={authenticate}
      onResetPassword={(email) => authService.resetPassword(email)}
    />
  );
}
