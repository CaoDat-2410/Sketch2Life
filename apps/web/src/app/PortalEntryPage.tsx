import { useNavigate, useSearchParams } from "react-router-dom";
import { authService } from "../modules/school-manager/be1/services/authService";
import { signInAndResolveRole } from "../shared/backendApi";
import { usePortalSession } from "../shared/PortalSessionContext";
import { WebPortalLoginPage, type WebPortalAppRole } from "../shared/WebPortalLoginPage";

const ROLE_QUERY: Record<WebPortalAppRole, string> = {
  TEACHER: "teacher",
  MANAGER: "manager",
  ADMIN: "admin",
};

function roleFromQuery(value: string | null): WebPortalAppRole {
  if (value === "manager") return "MANAGER";
  if (value === "admin") return "ADMIN";
  return "TEACHER";
}

export function PortalEntryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { loginAsRole } = usePortalSession();
  const portalRole = roleFromQuery(searchParams.get("role"));

  const selectRole = (role: WebPortalAppRole) => {
    setSearchParams({ role: ROLE_QUERY[role] });
  };

  const authenticate = async (role: WebPortalAppRole, email: string, password: string) => {
    const accountRole = role === "TEACHER"
      ? "teacher"
      : role === "MANAGER"
        ? "school_manager"
        : "platform_admin";
    await signInAndResolveRole(accountRole, email, password);
    loginAsRole(role);
    navigate(
      role === "TEACHER"
        ? "/teacher/t01-lesson-workspace"
        : role === "MANAGER"
          ? "/school"
          : "/platform/a02-platform-operations",
      { replace: true },
    );
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
