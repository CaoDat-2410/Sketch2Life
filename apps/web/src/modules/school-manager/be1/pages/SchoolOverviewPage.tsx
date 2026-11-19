import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, School, Users } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import {
  managerBusinessService,
  type Be1Organization,
} from "../services/managerBusinessService";

const SUMMARY_CARDS = [
  {
    title: "Lớp học",
    description: "Đọc các lớp trong organization đã được BE1 xác minh.",
    href: "/school/classes",
    action: "Mở lớp học",
    icon: School,
    state: "BE1",
  },
  {
    title: "Duyệt học liệu",
    description: "Rà soát yêu cầu công khai theo version hiện hành.",
    href: "/school/review-content",
    action: "Mở yêu cầu",
    icon: BookOpen,
    state: "API review",
  },
  {
    title: "Roster & consent",
    description: "Đọc roster tối thiểu và trạng thái consent theo lớp.",
    href: "/school/teachers",
    action: "Xem theo lớp",
    icon: Users,
    state: "BE1",
  },
  {
    title: "Nhóm phụ huynh",
    description: "Xem và tạo nhóm trong phạm vi organization của trường.",
    href: "/school/parent-groups",
    action: "Mở nhóm",
    icon: Users,
    state: "Lesson Library",
  },
];

export function SchoolOverviewPage() {
  const [organization, setOrganization] = useState<Be1Organization | null>(null);
  const [organizationError, setOrganizationError] = useState("");
  const [organizationLoading, setOrganizationLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    managerBusinessService.organization(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setOrganization(result);
          setOrganizationError("");
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setOrganization(null);
          setOrganizationError(
            cause instanceof Error ? cause.message : "Không tải được organization từ BE1.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setOrganizationLoading(false);
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="s2l-page manager-business-page">
      <PageHeading
        eyebrow="School Manager"
        title="Tổng quan nhà trường"
        description="Dữ liệu và thao tác chỉ mở trong organization được BE1 xác minh."
      />

      <section className="manager-business-card" aria-labelledby="school-organization-title">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Phạm vi hiện tại</p>
            <h2 id="school-organization-title">Organization nhà trường</h2>
          </div>
          <span className="manager-business-chip">GET · BE1</span>
        </div>
        {organizationLoading ? (
          <p className="manager-business-state" role="status">Đang tải thông tin organization…</p>
        ) : organizationError ? (
          <p className="manager-business-alert" role="alert">{organizationError}</p>
        ) : organization ? (
          <dl className="manager-business-organization">
            <div>
              <dt>Tên trường</dt>
              <dd>{organization.display_name}</dd>
            </div>
            <div>
              <dt>Mã organization</dt>
              <dd className="manager-business-code">{organization.organization_id}</dd>
            </div>
          </dl>
        ) : (
          <p className="manager-business-state">BE1 chưa trả thông tin organization.</p>
        )}
      </section>

      <section className="manager-business-grid" aria-label="Nghiệp vụ đang khả dụng">
        {SUMMARY_CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <article className="manager-business-card manager-business-summary" key={card.href}>
              <div className="manager-business-card-heading">
                <span className="manager-business-icon"><Icon size={19} aria-hidden="true" /></span>
                <span className="manager-business-chip">{card.state}</span>
              </div>
              <h2>{card.title}</h2>
              <p>{card.description}</p>
              <Link to={card.href}>{card.action}<ArrowRight size={16} aria-hidden="true" /></Link>
            </article>
          );
        })}
      </section>

      <section className="manager-business-card manager-business-limitation">
        <div>
          <p className="manager-business-eyebrow">Backend còn thiếu contract</p>
          <h2>Sức chứa và phân công giáo viên</h2>
          <p>
            Tạo lớp đang tạm khóa vì API hiện chưa kiểm tra capacity theo FR-T-03.
            Phân công Teacher lần đầu đã có ở màn Roster &amp; consent; đổi Teacher của lớp chưa được hỗ trợ.
          </p>
        </div>
        <span className="manager-business-chip is-pending">Chờ API</span>
      </section>
    </div>
  );
}
