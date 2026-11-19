import "./styles/tokens.css";
import "./styles/teacher-paper-crayon.css";
import "./styles/teacher-rebuild.css";
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
  if (pathname === "/teacher/t04-session-sketch-deck") return <TeacherUnavailablePage title="Buổi dạy" summary="Chuẩn bị kế hoạch và hướng dẫn trong occurrence gắn với đúng lớp và phiên bản giáo án." srsStep="SRS §5.2 yêu cầu occurrence, mục tiêu học, hoạt động, checklist và trạng thái của từng bước." missing={["API tạo/đọc occurrence và gắn lớp với phiên bản giáo án.", "API lưu mục tiêu, hướng dẫn, checklist và trạng thái từng bước.", "API Sketch Deck và trạng thái sinh lại nội dung theo plan revision."]} nextTo="/teacher/t02-lesson-authoring" nextLabel="Mở giáo án" />;
  if (pathname === "/teacher/t06-sample-story-run") return <TeacherUnavailablePage title="Video mẫu cho buổi học" summary="Luồng một trẻ, một tác phẩm và một lần chạy trong một occurrence." srsStep="Theo SRS §5.2, server chọn đúng một trẻ đủ điều kiện theo policy; giáo viên rà soát ngữ cảnh và xác nhận trước khi gửi tác phẩm." missing={["API server chọn trẻ đủ điều kiện theo lớp/consent và giải quyết Q-01; không cho giáo viên tự chọn hoặc dùng roster mẫu.", "API xác nhận bản chép lời, ngữ cảnh và revision trước khi tạo StoryRun.", "API quota, job/reconciliation, trạng thái an toàn, playback token và vòng đời run."]} nextTo="/teacher/t04-session-sketch-deck" nextLabel="Xem buổi dạy" />;
  if (pathname === "/teacher/t07-video-presentation-confirmation") return <TeacherUnavailablePage title="Trình chiếu trên lớp" summary="Chỉ phát nội dung đã sẵn sàng an toàn và gắn với đúng occurrence." srsStep="SRS yêu cầu giáo viên xác nhận trước khi chiếu; backend phải xác minh trạng thái và cấp playback token ngắn hạn." missing={["API xác minh trạng thái nội dung và cấp playback token có thời hạn.", "API ghi nhận xác nhận chiếu theo lớp, occurrence và revision.", "API hoàn tất/hủy/xóa và đối soát trạng thái sau lỗi."]} nextTo="/teacher/t06-sample-story-run" nextLabel="Xem trạng thái video mẫu" />;
  if (pathname === "/teacher/t08-settings") return <TeacherUnavailablePage title="Cài đặt Giáo viên" summary="Thiết lập hồ sơ và xác thực theo tài khoản đã đăng nhập." srsStep="Trang chưa gửi thay đổi hồ sơ hoặc xác thực vì chưa có Teacher profile/settings contract." missing={["API đọc và cập nhật hồ sơ Teacher theo phạm vi tài khoản.", "Contract cài đặt ngôn ngữ, thông báo và xác thực theo SRS."]} nextTo={ROLE_HOME} nextLabel="Về tổng quan" />;
  if (pathname === "/teacher/t09-history") return <TeacherUnavailablePage title="Lịch sử" summary="Occurrence, StoryRun và trạng thái xử lý thuộc phạm vi của giáo viên." srsStep="Chưa có endpoint lịch sử/đối soát để hiển thị dữ liệu có nguồn gốc từ backend." missing={["API phân trang lịch sử occurrence/StoryRun theo assignment.", "API trạng thái job và reconciliation để phân biệt hoàn tất, chờ xử lý và lỗi."]} nextTo={ROLE_HOME} nextLabel="Về tổng quan" />;
  if (pathname === "/teacher/t10-inbox") return <TeacherUnavailablePage title="Hộp thư" summary="Thông báo cần được tải từ inbox có trạng thái phía server." srsStep="Hộp thư không hiển thị số chưa đọc giả; chờ contract đồng bộ read state." missing={["API inbox phân trang theo tài khoản và scope.", "API đánh dấu đã đọc và đồng bộ unread state.", "API feedback thread/reply nếu được hỗ trợ trong scope."]} nextTo={ROLE_HOME} nextLabel="Về tổng quan" />;
  if (pathname === "/teacher/t11-profile") return <TeacherUnavailablePage title="Hồ sơ cá nhân" summary="Thông tin tài khoản lấy từ phiên đã xác thực." srsStep="Không dùng tên giáo viên hoặc trường minh họa làm dữ liệu sản phẩm." missing={["API đọc hồ sơ Teacher theo Firebase identity.", "API cập nhật hồ sơ và audit phù hợp quyền tài khoản."]} nextTo="/teacher/t08-settings" nextLabel="Xem cài đặt" />;
  if (pathname === "/teacher/t12-activities") return <TeacherUnavailablePage title="Hoạt động" summary="Hoạt động được xem trong giáo án hoặc checklist occurrence tương ứng." srsStep="Lesson API hỗ trợ activity content; Activity Catalog versioning và checklist occurrence chưa có trong FE contract." missing={["API danh mục hoạt động có revision, visibility và scope rõ ràng.", "API gắn checklist hoạt động với occurrence và lưu trạng thái thực hiện."]} nextTo="/teacher/t02-lesson-authoring" nextLabel="Mở giáo án" />;
  return <Navigate to={ROLE_HOME} replace />;
}

export function TeacherPortalApp() {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentRole, isAuthenticated, toast, logout } = usePortalSession();
  if (isAuthenticated && currentRole !== ROLE) return <RoleMismatchPage roleLabel="Giáo viên" onLogout={logout} />;
  if (!isAuthenticated) return <Navigate to="/login?role=teacher" replace />;
  if (location.pathname === "/teacher" || location.pathname === "/teacher/") return <Navigate to={ROLE_HOME} replace />;

  return (
    <WebAppShell
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
