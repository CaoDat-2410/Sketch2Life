import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, GraduationCap, School, Users } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import {
  managerBusinessService,
  type Be1Organization,
} from "../services/managerBusinessService";

const SUMMARY_CARDS = [
  {
    title: "Lớp học",
    description: "Xem và quản lý các lớp học trong phạm vi nhà trường.",
    href: "/school/classes",
    action: "Mở lớp học",
    icon: School,
    state: "Quản lý lớp",
  },
  {
    title: "Duyệt học liệu",
    description: "Rà soát yêu cầu công khai học liệu theo phiên bản hiện hành.",
    href: "/school/review-content",
    action: "Mở yêu cầu",
    icon: BookOpen,
    state: "Phê duyệt",
  },
  {
    title: "Danh sách lớp & đồng ý",
    description: "Theo dõi sĩ số học sinh và trạng thái xác nhận của phụ huynh theo lớp.",
    href: "/school/teachers",
    action: "Xem theo lớp",
    icon: Users,
    state: "Sĩ số & Xác nhận",
  },
  {
    title: "Nhóm phụ huynh",
    description: "Tạo nhóm và quản lý lời mời phụ huynh trong trường.",
    href: "/school/parent-groups",
    action: "Mở nhóm",
    icon: Users,
    state: "Phụ huynh",
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
            cause instanceof Error ? cause.message : "Không tải được thông tin trường học.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setOrganizationLoading(false);
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="s2l-page manager-business-page manager-overview">
      <PageHeading
        eyebrow="Quản lý trường"
        title="Tổng quan nhà trường"
        description="Dữ liệu và thao tác chỉ mở trong phạm vi nhà trường đã được xác minh."
      />

      <section className="manager-business-card manager-overview-school" aria-labelledby="school-organization-title">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Phạm vi hiện tại</p>
            <h2 id="school-organization-title">Thông tin trường học</h2>
          </div>
          <span className="manager-business-chip">Đã xác minh</span>
        </div>
        {organizationLoading ? (
          <p className="manager-business-state" role="status">Đang tải thông tin nhà trường…</p>
        ) : organizationError ? (
          <p className="manager-business-alert" role="alert">{organizationError}</p>
        ) : organization ? (
          <dl className="manager-business-organization">
            <div>
              <dt>Tên trường</dt>
              <dd>{organization.display_name}</dd>
            </div>
          </dl>
        ) : (
          <p className="manager-business-state">Chưa có thông tin trường học.</p>
        )}
      </section>

      <section className="manager-business-grid" aria-label="Nghiệp vụ đang khả dụng">
        {SUMMARY_CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <article className="manager-business-card manager-business-summary" key={card.href}>
              <span className="manager-business-icon"><Icon size={19} aria-hidden="true" /></span>
              <div className="manager-business-card-heading">
                <h2>{card.title}</h2>
                <span className="manager-business-chip">{card.state}</span>
              </div>
              <p>{card.description}</p>
              <Link to={card.href}>{card.action}<ArrowRight size={16} aria-hidden="true" /></Link>
            </article>
          );
        })}
      </section>

      <section className="manager-business-card manager-business-limitation">
        <span className="manager-business-icon"><GraduationCap size={19} aria-hidden="true" /></span>
        <div>
          <p className="manager-business-eyebrow">Phạm vi vận hành</p>
          <h2>Sức chứa và phân công giáo viên</h2>
        </div>
          <p>
            Tạo lớp, mời giáo viên, phân công, đổi và gỡ giáo viên phụ trách theo lớp.
          </p>
        <span className="manager-business-chip">Sẵn sàng</span>
      </section>
    </div>
  );
}
