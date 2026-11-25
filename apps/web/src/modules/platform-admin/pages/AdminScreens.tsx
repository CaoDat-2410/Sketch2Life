import { useLocation } from "react-router-dom";
import {
  OverviewPage,
  OrganizationsPage,
  OperationsPage,
  LifecyclePage,
  AuditPage,
  PermissionsPage,
  InboxPage,
  SettingsPage,
  FeedbackPage,
} from "./AdminDirectoryPages";
import { LessonsPage, CatalogPage } from "./AdminContentPages";
import { BillingPage, QuotaPage, CapacityPage } from "./AdminBillingPages";
import { AdminSvgCatalogPage } from "./AdminSvgCatalogPage";
import { Empty } from '../components/AdminUI'

export function A01ContentModerationPage() {
  return <LessonsPage />;
}
export function A02PlatformOperationsPage() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const panel = params.get("panel") ?? "overview";
  const pages = {
    overview: <OverviewPage />,
    orgs: <OrganizationsPage />,
    queues: <OperationsPage />,
    lifecycle: <LifecyclePage />,
    audit: <AuditPage />,
    permissions: <PermissionsPage />,
    inbox: <InboxPage />,
    settings: <SettingsPage />,
    feedback: <FeedbackPage key={params.get("org") ?? ""} initialOrganization={params.get("org") ?? ""} />,
    catalog: <CatalogPage />,
    billing: <BillingPage />,
    quota: <QuotaPage />,
    capacity: <CapacityPage />,
    svgcatalog: <AdminSvgCatalogPage />,
  };
  return (
    <div key={panel}>
      {pages[panel as keyof typeof pages] ?? (
        <Empty
          text="Không tìm thấy màn hình"
          detail="Chọn một mục trong thanh điều hướng để tiếp tục."
        />
      )}
    </div>
  );
}
