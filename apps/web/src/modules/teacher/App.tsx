import "./styles/tokens.css";
import "./styles/teacher-paper-crayon.css";
import "./styles/teacher-rebuild.css";
import "./styles/teacher-cozy.css";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { WebAppShell, TEACHER_NAVIGATION } from "../../shared/navigation/WebAppShell";
import { usePortalSession } from "../../shared/auth/PortalSessionContext";
import { RoleMismatchPage } from "../../shared/auth/RoleMismatchPage";
import { TeacherApiLessonPage } from "./pages/TeacherApiLessonPage";
import { TeacherApiImportPage } from "./pages/TeacherApiImportPage";
import { T05ClassDetailPage, TeacherApiClassesPage } from "./pages/T05ClassesScreen";
import { TeacherWorkbenchPage } from "./pages/TeacherWorkbenchPage";
import { TeacherUnavailablePage } from "./pages/TeacherUnavailablePage";
import { TeacherPresentationPage } from "./pages/TeacherPresentationPage";
import { TeacherAiLessonWorkflowPage } from "./pages/TeacherAiLessonWorkflowPage";
import { TeacherSampleRunPage } from "./pages/TeacherSampleRunPage";
import { TeacherProjectionPage } from "./pages/TeacherProjectionPage";
import { TeacherOccurrencePage } from "./pages/TeacherOccurrencePage";
import { AccountSettingsPage } from "../../shared/settings/AccountSettingsPage";
import { InboxPage } from "../../shared/notifications/InboxPage";

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
  if (pathname === "/teacher/t04-session-sketch-deck") return <TeacherOccurrencePage />;
  if (pathname === "/teacher/t06-sample-story-run") return <TeacherSampleRunPage />;
  if (pathname === "/teacher/t07-video-presentation-confirmation") return <TeacherProjectionPage />;
  if (pathname === "/teacher/t08-settings") return <AccountSettingsPage role="Teacher" />;
  if (pathname === "/teacher/t09-history") return <TeacherUnavailablePage title="Lịch sử" summary="Occurrence, StoryRun và trạng thái xử lý thuộc phạm vi của giáo viên." srsStep="Chưa có endpoint lịch sử/đối soát để hiển thị dữ liệu có nguồn gốc từ backend." missing={["API phân trang lịch sử occurrence/StoryRun theo assignment.", "API trạng thái job và reconciliation để phân biệt hoàn tất, chờ xử lý và lỗi."]} nextTo={ROLE_HOME} nextLabel="Về tổng quan" />;
  if (pathname === "/teacher/t10-inbox") return <InboxPage />;
  if (pathname === "/teacher/t11-profile") return <TeacherUnavailablePage title="Hồ sơ cá nhân" summary="Thông tin tài khoản lấy từ phiên đã xác thực." srsStep="Không dùng tên giáo viên hoặc trường minh họa làm dữ liệu sản phẩm." missing={["API đọc hồ sơ Teacher theo Firebase identity.", "API cập nhật hồ sơ và audit phù hợp quyền tài khoản."]} nextTo="/teacher/t08-settings" nextLabel="Xem cài đặt" />;
  if (pathname === "/teacher/t12-activities") return <TeacherUnavailablePage title="Hoạt động" summary="Hoạt động được xem trong giáo án hoặc checklist occurrence tương ứng." srsStep="Lesson API hỗ trợ activity content; Activity Catalog versioning và checklist occurrence chưa có trong FE contract." missing={["API danh mục hoạt động có revision, visibility và scope rõ ràng.", "API gắn checklist hoạt động với occurrence và lưu trạng thái thực hiện."]} nextTo="/teacher/t02-lesson-authoring" nextLabel="Mở giáo án" />;
  return <Navigate to={ROLE_HOME} replace />;
}

export function TeacherPortalApp() {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentRole, isAuthenticated, toast, logout } = usePortalSession();
  if (isAuthenticated && currentRole !== ROLE) return <RoleMismatchPage roleLabel="Giáo viên" onLogout={logout} />;
  if (!isAuthenticated) return <Navigate to="/login?role=teacher" replace state={{ from: location }} />;
  if (location.pathname === "/teacher" || location.pathname === "/teacher/") return <Navigate to={ROLE_HOME} replace />;

  return (
    <WebAppShell
      portal="teacher"
      roleLabel="Giáo viên"
      roleSubtitle="Lớp được phân công · học liệu · buổi dạy"
      navigation={TEACHER_NAVIGATION}
      loginHref="/login?role=teacher"
      modeLabel="Phiên đã xác minh"
      toast={toast}
      onLogout={() => { logout(); navigate("/login?role=teacher"); }}
    >
      {renderTeacherPage(location.pathname)}
    </WebAppShell>
  );
}

export default TeacherPortalApp;
