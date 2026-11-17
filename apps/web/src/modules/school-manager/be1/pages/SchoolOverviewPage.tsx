import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, CircleHelp, School, Users } from "lucide-react";
import { FeatureAvailability, PageHeading } from "../../../../shared/FeatureAvailability";

const SUMMARY_CARDS = [
  {
    title: "Lớp học",
    description: "Đọc danh sách và tạo lớp qua BE1 trong organization đã xác minh.",
    href: "/school/classes",
    action: "Mở lớp học",
    icon: School,
    state: "BE1",
  },
  {
    title: "Duyệt học liệu",
    description: "Rà soát yêu cầu công khai trong phạm vi trường theo version hiện hành.",
    href: "/school/review-content",
    action: "Mở yêu cầu",
    icon: BookOpen,
    state: "API review",
  },
];

export function SchoolOverviewPage() {
  return (
    <div className="s2l-page">
      <PageHeading
        eyebrow="School Manager"
        title="Tổng quan nhà trường"
        description="Quản lý lớp và nội dung công khai trong organization được BE1 xác minh."
      />

      <section className="s2l-summary-grid" aria-label="Khu vực khả dụng">
        {SUMMARY_CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <article className="s2l-summary-card" key={card.href}>
              <div className="s2l-summary-card-top"><span className="s2l-summary-icon"><Icon size={20} aria-hidden="true" /></span><span className="s2l-status-tag is-available">{card.state}</span></div>
              <h2>{card.title}</h2>
              <p>{card.description}</p>
              <Link to={card.href}>{card.action}<ArrowRight size={16} aria-hidden="true" /></Link>
            </article>
          );
        })}
      </section>

      <section className="s2l-summary-grid s2l-summary-grid-secondary" aria-label="Khu vực đang chờ API">
        <article className="s2l-summary-card is-muted">
          <div className="s2l-summary-card-top"><span className="s2l-summary-icon"><Users size={20} aria-hidden="true" /></span><span className="s2l-status-tag">Chưa khả dụng</span></div>
          <h2>Phân công và roster</h2>
          <p>BE1 adapter hiện không cung cấp phân công giáo viên hoặc quản trị roster từ màn này.</p>
          <Link to="/school/teachers">Xem trạng thái<ArrowRight size={16} aria-hidden="true" /></Link>
        </article>
        <article className="s2l-summary-card is-muted">
          <div className="s2l-summary-card-top"><span className="s2l-summary-icon"><CircleHelp size={20} aria-hidden="true" /></span><span className="s2l-status-tag">Chưa khả dụng</span></div>
          <h2>Sức chứa và dịch vụ trường</h2>
          <p>Chưa có API tổng hợp capacity, billing, quota và inbox trong School Manager.</p>
          <Link to="/school/capacity">Xem trạng thái<ArrowRight size={16} aria-hidden="true" /></Link>
        </article>
      </section>

      <FeatureAvailability
        title="Quyền theo phạm vi trường"
        summary="Mỗi request được xác minh lại bằng tài khoản và assignment hiện hành ở backend."
        requirement="School Manager chỉ đọc roster trong organization của mình; không xem story hoặc media của trẻ."
        dependencies={["API và scope cho phân công giáo viên, roster, capacity, billing và quota.", "Màn hình không cấp quyền bằng cách đổi route hoặc chọn organization ở phía client."]}
        permissionNote="School Manager không có quyền đọc child media/story theo mặc định."
      />
    </div>
  );
}