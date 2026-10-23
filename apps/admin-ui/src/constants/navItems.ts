import { ADMIN_ROUTES } from '../types/routes';

export interface NavItemConfig {
  label: string;
  path: string;
  iconName: string;
  badge?: string;
}

export const NAV_ITEMS: NavItemConfig[] = [
  { label: 'Dashboard', path: ADMIN_ROUTES.DASHBOARD, iconName: 'LayoutDashboard' },
  { label: 'Người dùng', path: ADMIN_ROUTES.USERS, iconName: 'Users' },
  { label: 'Lớp học', path: ADMIN_ROUTES.CLASSES, iconName: 'GraduationCap' },
  { label: 'Nội dung', path: ADMIN_ROUTES.CONTENT, iconName: 'BookOpen' },
  { label: 'Chính sách AI', path: ADMIN_ROUTES.AI_POLICY, iconName: 'ShieldAlert' },
  { label: 'Yêu cầu dữ liệu', path: ADMIN_ROUTES.DATA_REQUESTS, iconName: 'FileText' },
  { label: 'Nhật ký hệ thống', path: ADMIN_ROUTES.LOGS, iconName: 'ListOrdered' },
  { label: 'Giám sát', path: ADMIN_ROUTES.MONITORING, iconName: 'Activity' },
  { label: 'Báo cáo', path: ADMIN_ROUTES.REPORTS, iconName: 'BarChart3' },
  { label: 'Cài đặt', path: ADMIN_ROUTES.SETTINGS, iconName: 'Settings' },
];
