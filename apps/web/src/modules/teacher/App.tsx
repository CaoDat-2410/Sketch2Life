import "./styles/teacher-shared-carryover.css";
import "./styles/tokens.css";
import "./styles/teacher-paper-crayon.css";
import "./styles/teacher-rebuild.css";
import "./styles/teacher-cozy.css";
import "./styles/teacher-polish.css";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { WebAppShell, TEACHER_NAVIGATION } from "../../shared/navigation/WebAppShell";
import { usePortalSession } from "../../shared/auth/PortalSessionContext";
import { RoleMismatchPage } from "../../shared/auth/RoleMismatchPage";
import { TeacherApiLessonPage } from "./pages/TeacherApiLessonPage";
import { TeacherApiImportPage } from "./pages/TeacherApiImportPage";
import { T05ClassDetailPage, TeacherApiClassesPage } from "./pages/T05ClassesScreen";
import { TeacherWorkbenchPage } from "./pages/TeacherWorkbenchPage";
import { TeacherPresentationPage } from "./pages/TeacherPresentationPage";
import { TeacherHistoryPage } from "./pages/TeacherHistoryPage";
import { TeacherProfilePage } from "./pages/TeacherProfilePage";
import { TeacherActivitiesPage } from "./pages/TeacherActivitiesPage";
import { TeacherAiLessonWorkflowPage } from "./pages/TeacherAiLessonWorkflowPage";
import { TeacherSampleRunPage } from "./pages/TeacherSampleRunPage";
import { TeacherProjectionPage } from "./pages/TeacherProjectionPage";
import { TeacherFeedbackPage } from "./pages/TeacherFeedbackPage";
import { TeacherOccurrencePage } from "./pages/TeacherOccurrencePage";
import { TeacherSvgCatalogPage } from "./pages/TeacherSvgCatalogPage";
import { InboxPage } from "../../shared/notifications/InboxPage";
import { clearAiWorkflowSession } from "./services/aiWorkflowSession";
import { clearSvgDraftRequests } from "./services/svgDraftRequests";
import { getAiTaskAggregateStatus, useAiTaskAggregateStatus } from "./services/aiTaskStatus";
import { useEffect } from "react";

const ROLE_HOME = "/teacher/t01-lesson-workspace";
const ROLE = "TEACHER" as const;

function renderTeacherPage(pathname: string) {
  if (pathname === ROLE_HOME) return <TeacherWorkbenchPage />;
  if (pathname === "/teacher/t05-classes-and-children") return <TeacherApiClassesPage />;
  const classPrefix = "/teacher/t05-classes-and-children/";
  if (pathname.startsWith(classPrefix)) {
    const classId = decodeURIComponent(pathname.slice(classPrefix.length));
    if (classId && !classId.includes("/")) return <T05ClassDetailPage classId={classId} />;
  }
  if (pathname === "/teacher/t02-lesson-authoring") return <TeacherApiLessonPage />;
  if (pathname === "/teacher/t03-document-import-review") return <TeacherApiImportPage />;
  if (pathname === "/teacher/t02-presentation") return <TeacherPresentationPage />;
  if (pathname === "/teacher/t13-ai-lesson-workflow") return <TeacherAiLessonWorkflowPage />;
  if (pathname === "/teacher/svg-catalog") return <TeacherSvgCatalogPage />;
  if (pathname === "/teacher/t04-session-sketch-deck") return <TeacherOccurrencePage />;
  if (pathname === "/teacher/t06-sample-story-run") return <TeacherSampleRunPage />;
  if (pathname === "/teacher/t07-video-presentation-confirmation") return <TeacherProjectionPage />;
  if (pathname === "/teacher/t14-feedback") return <TeacherFeedbackPage />;
  if (pathname === "/teacher/t08-settings") return <Navigate to="/teacher/t11-profile" replace />;
  if (pathname === "/teacher/t09-history") return <TeacherHistoryPage />;
  if (pathname === "/teacher/t10-inbox") return <InboxPage />;
  if (pathname === "/teacher/t11-profile") return <TeacherProfilePage />;
  if (pathname === "/teacher/t12-activities") return <TeacherActivitiesPage />;
  return <Navigate to={ROLE_HOME} replace />;
}

export function TeacherPortalApp() {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentRole, isAuthenticated, toast, logout } = usePortalSession();
  const navAiStatus = useAiTaskAggregateStatus();
  const hasPendingAiTask = navAiStatus === "pending";
  useEffect(() => {
    if (!hasPendingAiTask) return;
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      if (getAiTaskAggregateStatus() !== "pending") return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [hasPendingAiTask]);
  const logoutAndClearAiState = () => {
    clearAiWorkflowSession();
    clearSvgDraftRequests();
    logout();
  };
  if (isAuthenticated && currentRole !== ROLE) return <RoleMismatchPage roleLabel="Giáo viên" onLogout={logoutAndClearAiState} />;
  if (!isAuthenticated) return <Navigate to="/login?role=teacher" replace state={{ from: location }} />;
  if (location.pathname === "/teacher" || location.pathname === "/teacher/") return <Navigate to={ROLE_HOME} replace />;

  return (
    <WebAppShell
      portal="teacher"
      roleLabel="Giáo viên"
      roleSubtitle="Lớp được phân công · học liệu · buổi dạy"
      navigation={TEACHER_NAVIGATION}
      navStatus={{ "/teacher/t13-ai-lesson-workflow": navAiStatus }}
      loginHref="/login?role=teacher"
      modeLabel="Phiên đã xác minh"
      toast={toast}
      onLogout={() => { logoutAndClearAiState(); navigate("/login?role=teacher"); }}
    >
      {renderTeacherPage(location.pathname)}
    </WebAppShell>
  );
}

export default TeacherPortalApp;
