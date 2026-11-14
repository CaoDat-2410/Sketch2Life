import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BrandMark } from './BrandMark';
import { hasRoleFlow, RoleFlowPage } from './roleFlows';

export type Role = 'teacher' | 'manager' | 'admin';
type IconKey = 'grid' | 'book' | 'class' | 'spark' | 'video' | 'file' | 'users' | 'check' | 'chart' | 'shield' | 'bell' | 'settings' | 'search' | 'plus' | 'arrow' | 'chevron' | 'menu' | 'close' | 'clock' | 'filter' | 'download' | 'more' | 'eye' | 'send' | 'message' | 'layer' | 'link' | 'alert' | 'edit';
type NavItem = { id: string; label: string; icon: IconKey; group?: string };
type RecordItem = { id: string; title: string; subtitle: string; meta: string; status: string; tone: 'green' | 'amber' | 'blue' | 'gray' | 'red' };
type TeacherLessonSummaryPreview = { id: string; title: string; visibility: 'private' | 'shared' | 'public'; reviewState: 'draft' | 'pending' | 'approved' | 'needs_changes' };
type TeacherAssignmentPreview = { classId: string; teacherId: string; active: boolean };
type TeacherDashboardPreview = { lessons: TeacherLessonSummaryPreview[]; assignments: TeacherAssignmentPreview[]; nextSession: { className: string; time: string; lesson: string; activity: string }; feedback: { subject: string; note: string; time: string }[] };
type Config = { displayName: string; name: string; scope: string; greeting: string; heading: string; description: string; heroTag: string; heroAction: string; heroTarget: string; nav: NavItem[]; metrics: { value: string; label: string; note: string }[] };

const paths: Record<IconKey, React.ReactNode> = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
  book: <><path d="M12 20c-2.3-1.5-5.3-2-9-1V4c3.7-1 6.7-.5 9 1 2.3-1.5 5.3-2 9-1v15c-3.7-1-6.7-.5-9 1Z"/><path d="M12 5v15"/></>,
  class: <><rect x="3" y="4" width="18" height="15" rx="2"/><path d="M7 9h10M7 13h6M8 22h8"/></>,
  spark: <path d="m12 2 2.2 7.8L22 12l-7.8 2.2L12 22l-2.2-7.8L2 12l7.8-2.2L12 2Z"/>,
  video: <><rect x="3" y="5" width="14" height="14" rx="3"/><path d="m17 10 4-3v10l-4-3"/></>,
  file: <><path d="M5 2h9l5 5v15H5z"/><path d="M14 2v5h5M8 12h8M8 16h8"/></>,
  users: <><circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6m1 4a5 5 0 0 1 3 5v1"/></>,
  check: <path d="m4 12 5 5L20 6"/>, chart: <><path d="M4 20V4M4 20h17M8 16l4-5 4 2 5-7"/></>,
  shield: <><path d="M12 2 4 5v6c0 5 3.4 8.8 8 11 4.6-2.2 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 8-3 9h18c0-1-3-2-3-9ZM10 21h4"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M12 2v2m0 16v2M4 12H2m20 0h-2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></>,
  search: <><circle cx="10.8" cy="10.8" r="6.5"/><path d="m16 16 5 5"/></>, plus: <path d="M12 4v16M4 12h16"/>, arrow: <path d="M4 12h16m-7-7 7 7-7 7"/>, chevron: <path d="m9 5 7 7-7 7"/>,
  menu: <path d="M4 6h16M4 12h16M4 18h16"/>, close: <path d="M5 5 19 19M19 5 5 19"/>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/></>, filter: <path d="M3 5h18l-7 8v5l-4 2v-7L3 5Z"/>,
  download: <path d="M12 3v13m-5-5 5 5 5-5M4 20h16"/>, more: <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
  eye: <><path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.5"/></>,
  send: <path d="m3 11 18-8-8 18-2-8-8-2Zm8 2L21 3"/>, message: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-5.5A7.5 7.5 0 1 1 20 11.5Z"/><path d="M8 11h.01M12 11h.01M16 11h.01"/></>, layer: <><rect x="5" y="4" width="14" height="14" rx="2"/><path d="M8 21h11a2 2 0 0 0 2-2V8"/></>,
  link: <><path d="M9 15 15 9M8 7H6a4 4 0 0 0 0 8h2m8-8h2a4 4 0 0 1 0 8h-2"/></>,
  alert: <><path d="m12 2 10 18H2L12 2Z"/><path d="M12 9v4m0 4h.01"/></>, edit: <><path d="M4 20h4L20 8l-4-4L4 16v4ZM13 7l4 4"/></>,
};
function Icon({ name, size = 19 }: { name: IconKey; size?: number }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>; }

const config: Record<Role, Config> = {
  teacher: { displayName: 'Cô Mai', name: 'Giáo viên', scope: 'Không gian dạy học', greeting: 'Chào cô Mai,', heading: 'Mỗi nét vẽ là một bài học mới.', description: 'Giáo án, lớp học và câu chuyện mẫu trong cùng một nơi.', heroTag: 'BUỔI DẠY HÔM NAY', heroAction: 'Chuẩn bị bài giảng', heroTarget: 'lessons', nav: [
    { id: 'home', label: 'Tổng quan', icon: 'grid' },
    { id: 'classes', label: 'Lớp học & học sinh', icon: 'class', group: 'GIẢNG DẠY' },
    { id: 'lessons', label: 'Giáo án', icon: 'book' },
    { id: 'session', label: 'Buổi dạy', icon: 'video' },
    { id: 'history', label: 'Lịch sử buổi dạy', icon: 'clock' },
    { id: 'feedback', label: 'Phản hồi gia đình', icon: 'message', group: 'GIA ĐÌNH & HỆ THỐNG' },
    { id: 'quota', label: 'Lượt tạo của trường', icon: 'chart' },
    { id: 'settings', label: 'Cài đặt & thông báo', icon: 'settings' },
  ], metrics: [{ value: '03', label: 'Giáo án đang soạn', note: 'Bản nháp của cô' }, { value: '01', label: 'Lớp phụ trách', note: 'Theo phân công' }, { value: '01', label: 'Việc cần xem lại', note: 'Trước buổi học' }] },
  manager: { displayName: 'Thầy Minh', name: 'Quản lý trường', scope: 'Điều hành nhà trường', greeting: 'Chào thầy Minh,', heading: 'Nhìn rõ nhịp học của cả trường.', description: 'Lớp học, phân công và phê duyệt được sắp xếp theo ưu tiên.', heroTag: 'TỔNG QUAN NHÀ TRƯỜNG', heroAction: 'Xem lớp học', heroTarget: 'classes', nav: [
    { id: 'home', label: 'Tổng quan', icon: 'grid' },
    { id: 'classes', label: 'Lớp học & sức chứa', icon: 'class', group: 'NHÀ TRƯỜNG & NHÂN SỰ' },
    { id: 'teachers', label: 'Giáo viên & phân công', icon: 'users' },
    { id: 'groups', label: 'Gia đình & Roster', icon: 'layer' },
    { id: 'review', label: 'Duyệt công khai', icon: 'book', group: 'GIÁO ÁN & VẬN HÀNH' },
    { id: 'feedback', label: 'Phản hồi giáo án', icon: 'message' },
    { id: 'billing', label: 'Gói dịch vụ & Quota', icon: 'file' },
    { id: 'settings', label: 'Cài đặt & thông báo', icon: 'settings' },
  ], metrics: [{ value: '04', label: 'Lớp học', note: 'Đang hoạt động' }, { value: '03', label: 'Giáo viên', note: 'Đang phân công' }, { value: '02', label: 'Cần xem xét', note: 'Giáo án công khai' }] },
  admin: { displayName: 'Quản trị viên', name: 'Quản trị nền tảng', scope: 'Vận hành Sketch2Life', greeting: 'Không gian quản trị', heading: 'Nền tảng rõ ràng, an toàn.', description: 'Duyệt nội dung và theo dõi tổ chức trong đúng phạm vi quyền.', heroTag: 'TỔNG QUAN HỆ THỐNG', heroAction: 'Xem hàng chờ duyệt', heroTarget: 'moderation', nav: [
    { id: 'home', label: 'Tổng quan', icon: 'grid' },
    { id: 'organizations', label: 'Tổ chức', icon: 'class', group: 'TỔ CHỨC & NỘI DUNG' },
    { id: 'accounts', label: 'Tài khoản & vai trò', icon: 'users' },
    { id: 'moderation', label: 'Kiểm duyệt thư viện', icon: 'shield' },
    { id: 'catalog', label: 'Danh mục hoạt động', icon: 'layer' },
    { id: 'billing-ops', label: 'Đối soát thanh toán', icon: 'check', group: 'VẬN HÀNH & HỆ THỐNG' },
    { id: 'health', label: 'Giám sát AI & hệ thống', icon: 'chart' },
    { id: 'feedback', label: 'Hỗ trợ & phản hồi', icon: 'message' },
    { id: 'settings', label: 'Cài đặt & thông báo', icon: 'settings' },
  ], metrics: [{ value: '02', label: 'Chờ duyệt', note: 'Cần xem xét' }, { value: '04', label: 'Tổ chức', note: 'Đang quản lý' }, { value: '—', label: 'Tác vụ AI', note: 'Hàng đợi xử lý' }] },
};

type HubTab = { routeId: string; label: string };
type HubSpec = { label: string; tabs: HubTab[] };

const workspaceHubs: Record<Role, Record<string, HubSpec>> = {
  teacher: {
    classes: {
      label: 'Không gian lớp học',
      tabs: [
        { routeId: 'classes', label: 'Lớp được phân công' },
        { routeId: 'children', label: 'Hồ sơ trẻ trong lớp' },
        { routeId: 'teacher-scope', label: 'Phạm vi tổ chức' },
      ],
    },
    lessons: {
      label: 'Không gian giáo án',
      tabs: [
        { routeId: 'lessons', label: 'Thư viện & soạn mới' },
        { routeId: 'import', label: 'Nhập từ tài liệu' },
        { routeId: 'sharing', label: 'Chia sẻ giáo án' },
      ],
    },
    session: {
      label: 'Không gian buổi dạy',
      tabs: [
        { routeId: 'session', label: 'Không gian buổi dạy' },
        { routeId: 'occurrences', label: 'Chuẩn bị Plan' },
        { routeId: 'deck', label: 'Sketch Deck' },
        { routeId: 'sample', label: 'Video mẫu' },
        { routeId: 'presentation', label: 'Trình chiếu' },
        { routeId: 'run-control', label: 'Kết thúc run' },
      ],
    },
    settings: {
      label: 'Cài đặt & thông báo',
      tabs: [
        { routeId: 'settings', label: 'Tài khoản & Web Push' },
        { routeId: 'inbox', label: 'Hộp thư thông báo' },
      ],
    },
  },
  manager: {
    classes: {
      label: 'Quản lý lớp học',
      tabs: [
        { routeId: 'classes', label: 'Danh sách lớp học' },
        { routeId: 'class-lifecycle', label: 'Vòng đời lớp' },
        { routeId: 'capacity', label: 'Sức chứa (Capacity)' },
      ],
    },
    teachers: {
      label: 'Giáo viên & phân công',
      tabs: [
        { routeId: 'teachers', label: 'Giáo viên & lời mời' },
        { routeId: 'assignment', label: 'Phân công theo lớp' },
        { routeId: 'transfers', label: 'Đổi người phụ trách' },
      ],
    },
    groups: {
      label: 'Gia đình & Roster',
      tabs: [
        { routeId: 'groups', label: 'Nhóm gia đình & lời mời' },
        { routeId: 'roster', label: 'Roster & chuyển lớp' },
      ],
    },
    billing: {
      label: 'Gói dịch vụ & Quota',
      tabs: [
        { routeId: 'billing', label: 'Gói & hóa đơn' },
        { routeId: 'quota', label: 'Quota video trường' },
      ],
    },
    settings: {
      label: 'Cài đặt & thông báo',
      tabs: [
        { routeId: 'settings', label: 'Thiết lập cổng trường' },
        { routeId: 'notifications', label: 'Thông báo tổ chức' },
      ],
    },
  },
  admin: {
    health: {
      label: 'Giám sát AI & hệ thống',
      tabs: [
        { routeId: 'health', label: 'Sức khỏe nền tảng' },
        { routeId: 'jobs', label: 'Tác vụ AI (Queue)' },
        { routeId: 'audit', label: 'Nhật ký vận hành' },
      ],
    },
    settings: {
      label: 'Cài đặt & thông báo',
      tabs: [
        { routeId: 'settings', label: 'Thiết lập cổng quản trị' },
        { routeId: 'notifications', label: 'Thông báo vận hành' },
      ],
    },
  },
};

function resolveRoute(role: Role, rawId: string): { page: string; routeId: string } {
  const hubs = workspaceHubs[role] ?? {};
  for (const [hubPage, hub] of Object.entries(hubs)) {
    if (hub.tabs.some((tab) => tab.routeId === rawId)) return { page: hubPage, routeId: rawId };
  }
  const validNavIds = config[role].nav.map((item) => item.id);
  if (validNavIds.includes(rawId)) return { page: rawId, routeId: rawId };
  return { page: 'home', routeId: 'home' };
}

const collections: Record<string, RecordItem[]> = {
  lessons: [
    { id: 'garden', title: 'Khám phá khu vườn', subtitle: 'Thiên nhiên · 3 hoạt động', meta: 'Phiên bản 1.4', status: 'Bản nháp', tone: 'amber' },
    { id: 'sky', title: 'Bầu trời kỳ diệu', subtitle: 'Quan sát · 2 hoạt động', meta: 'Phiên bản 2.0', status: 'Đã chia sẻ', tone: 'green' },
    { id: 'seed', title: 'Hành trình của hạt mầm', subtitle: 'Cây xanh · 2 hoạt động', meta: 'Phiên bản 1.0', status: 'Chờ duyệt', tone: 'blue' },
  ],
  classes: [
    { id: 'la1', title: 'Lớp Lá 1', subtitle: 'Cô Mai phụ trách', meta: 'Nhóm 5–6 tuổi', status: 'Đang học', tone: 'green' },
    { id: 'choi2', title: 'Lớp Chồi 2', subtitle: 'Cô Lan phụ trách', meta: 'Nhóm 4–5 tuổi', status: 'Đang học', tone: 'green' },
    { id: 'mam1', title: 'Lớp Mầm 1', subtitle: 'Chưa phân công', meta: 'Nhóm 3–4 tuổi', status: 'Cần phân công', tone: 'amber' },
    { id: 'la2', title: 'Lớp Lá 2', subtitle: 'Cô Hà phụ trách', meta: 'Nhóm 5–6 tuổi', status: 'Đang học', tone: 'green' },
  ],
  teachers: [
    { id: 'mai', title: 'Cô Nguyễn Mai', subtitle: 'Lớp Lá 1', meta: 'Giáo viên phụ trách', status: 'Đang phân công', tone: 'green' },
    { id: 'lan', title: 'Cô Trần Lan', subtitle: 'Lớp Chồi 2', meta: 'Giáo viên phụ trách', status: 'Đang phân công', tone: 'green' },
    { id: 'ha', title: 'Cô Phạm Hà', subtitle: 'Lớp Lá 2', meta: 'Giáo viên phụ trách', status: 'Đang phân công', tone: 'green' },
  ],
  review: [
    { id: 'seed', title: 'Hành trình của hạt mầm', subtitle: 'Cô Mai · Chủ đề cây xanh', meta: 'Phiên bản 1.0', status: 'Chờ xem xét', tone: 'amber' },
    { id: 'cloud', title: 'Những đám mây kể chuyện', subtitle: 'Cô Lan · Chủ đề bầu trời', meta: 'Phiên bản 1.2', status: 'Cần bổ sung', tone: 'blue' },
  ],
  moderation: [
    { id: 'outdoor', title: 'Dạo bước tìm màu sắc', subtitle: 'Hoạt động ngoài trời · bản mới', meta: 'Chờ kiểm tra nội dung', status: 'Chờ duyệt', tone: 'amber' },
    { id: 'lesson', title: 'Khu vườn nhỏ của bé', subtitle: 'Giáo án công khai · bản mới', meta: 'Chờ kiểm tra quyền', status: 'Chờ duyệt', tone: 'amber' },
  ],
  catalog: [
    { id: 'colors', title: 'Tìm màu trong vườn', subtitle: 'Ngoài trời · quan sát', meta: 'Phiên bản v1', status: 'Đã phát hành', tone: 'green' },
    { id: 'clouds', title: 'Nhìn mây kể chuyện', subtitle: 'Ngoài trời · tưởng tượng', meta: 'Phiên bản v1', status: 'Đã phát hành', tone: 'green' },
    { id: 'walk', title: 'Dạo bước tìm màu sắc', subtitle: 'Ngoài trời · quan sát', meta: 'Phiên bản v2', status: 'Chờ duyệt', tone: 'amber' },
  ],
  organizations: [
    { id: 'sun', title: 'Trường Mầm non Ánh Nắng', subtitle: 'Hà Nội', meta: 'Đang vận hành', status: 'Hoạt động', tone: 'green' },
    { id: 'leaf', title: 'Trường Mầm non Lá Xanh', subtitle: 'Đà Nẵng', meta: 'Đang vận hành', status: 'Hoạt động', tone: 'green' },
    { id: 'river', title: 'Trường Mầm non Dòng Suối', subtitle: 'Huế', meta: 'Đang thiết lập', status: 'Chờ thiết lập', tone: 'blue' },
  ],
  feedback: [
    { id: 'fb1', title: 'Khám phá khu vườn', subtitle: 'Phụ huynh Bé An · tới Cô Mai', meta: 'Góp ý về vật liệu', status: 'Chờ phản hồi', tone: 'amber' },
    { id: 'fb2', title: 'Bầu trời kỳ diệu', subtitle: 'Phụ huynh Bé Minh · tới Cô Lan', meta: 'Cảm ơn giáo viên', status: 'Đã phản hồi', tone: 'green' },
  ],
};

// Offline fixture shaped around the Teacher lesson-summary and assignment contracts.
// It is intentionally local demo data; no API request is made from this workspace.
const teacherDashboardPreview: TeacherDashboardPreview | null = {
  lessons: [
    { id: 'garden', title: 'Khám phá khu vườn', visibility: 'private', reviewState: 'draft' },
    { id: 'sky', title: 'Bầu trời kỳ diệu', visibility: 'shared', reviewState: 'approved' },
    { id: 'seed', title: 'Hành trình của hạt mầm', visibility: 'private', reviewState: 'pending' },
  ],
  assignments: [{ classId: 'la1', teacherId: 'mai', active: true }],
  nextSession: { className: 'Lớp Lá 1', time: '10:30 · hôm nay', lesson: 'Bầu trời kỳ diệu · v2.0 · đã duyệt', activity: 'Tìm hình trong mây' },
  feedback: [{ subject: 'Khám phá khu vườn · gia đình Bé An', note: 'Bé muốn quan sát thêm các loại lá ở sân trường.', time: '3 ngày trước' }, { subject: 'Bầu trời kỳ diệu · gia đình Bé Minh', note: 'Cô đã phản hồi về hoạt động vẽ mây.', time: 'Tuần trước' }],
};

function HeroArt({ role }: { role: Role }) {
  return <svg className="web-hero-art" viewBox="0 0 420 245" role="img" aria-label={role === 'teacher' ? 'Trang sách, giấy vẽ và những nét màu' : role === 'manager' ? 'Các lớp học được kết nối như những trang giấy' : 'Những lớp nội dung được kiểm tra và bảo vệ'}>
    <defs><linearGradient id={`paper-${role}`} x1="0" x2="1" y1="0" y2="1"><stop stopColor="#fffdf4"/><stop offset="1" stopColor="#eaf0e3"/></linearGradient><filter id={`shadow-${role}`}><feDropShadow dx="0" dy="12" stdDeviation="12" floodColor="#253e39" floodOpacity=".16"/></filter></defs>
    <circle cx="324" cy="118" r="98" fill="white" opacity=".16"/><circle cx="360" cy="38" r="25" fill="#f7d77d" opacity=".8"/>
    <g filter={`url(#shadow-${role})`} transform="translate(42 22) rotate(-8 150 110)"><rect x="24" y="34" width="245" height="170" rx="18" fill={`url(#paper-${role})`}/><path d="M53 75h112M53 93h88" stroke="#c2d4c4" strokeWidth="7" strokeLinecap="round"/><path d="M47 149q38-45 80-12t79-12" stroke="#7ba893" strokeWidth="12" fill="none" strokeLinecap="round"/><circle cx="206" cy="78" r="18" fill="#f3cc72"/></g>
    <g transform="translate(194 79) rotate(10 85 65)" filter={`url(#shadow-${role})`}><rect width="165" height="126" rx="17" fill="#fffdf5"/><rect x="16" y="16" width="133" height="94" rx="12" fill={role === 'teacher' ? '#e5efd7' : role === 'manager' ? '#dae9eb' : '#e6f0e8'}/>{role === 'teacher' ? <><path d="M30 83q38-38 70-10t37-17" fill="none" stroke="#6ea582" strokeWidth="9" strokeLinecap="round"/><circle cx="113" cy="40" r="14" fill="#f7cb70"/></> : role === 'manager' ? <><rect x="29" y="57" width="24" height="35" rx="5" fill="#93bcae"/><rect x="64" y="40" width="24" height="52" rx="5" fill="#5d9b8b"/><rect x="99" y="25" width="24" height="67" rx="5" fill="#36786d"/></> : <><circle cx="82" cy="61" r="34" fill="#cbe0cf"/><path d="m67 61 11 11 22-25" fill="none" stroke="#2e6b53" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/></>}</g>
    <path d="m40 46 3 8 8 3-8 3-3 8-3-8-8-3 8-3 3-8Zm338 128 2 6 6 2-6 2-2 6-2-6-6-2 6-2 2-6Z" fill="#f8d881"/>
  </svg>;
}

function Status({ item }: { item: RecordItem }) { return <span className={`web-status web-status--${item.tone}`}><i />{item.status}</span>; }
function PanelTitle({ eyebrow, title, action, onAction }: { eyebrow?: string; title: string; action?: string; onAction?: () => void }) { return <div className="web-panel-title"><div>{eyebrow && <span className="web-eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{action && <button className="web-text-action" onClick={onAction}>{action}<Icon name="arrow" size={16}/></button>}</div>; }

type DashMetric = { label: string; value: number | string; note: string; icon: IconKey; target: string };

function DashIntro({ role, title, description, action, onAction }: { role: Role; title: string; description: string; action: string; onAction: () => void }) {
  return <header className={`dash-intro dash-intro--${role}`}><div className="dash-intro-copy"><span className="dash-overline"><Icon name={role === 'teacher' ? 'book' : role === 'manager' ? 'class' : 'shield'} size={17}/>{config[role].scope.toLocaleUpperCase('vi')}</span><p>{config[role].greeting}</p><h1>{title}</h1><span className="dash-intro-description">{description}</span><button className="dashboard-primary" onClick={onAction}>{action}<Icon name="arrow" size={17}/></button></div><div className="dashboard-welcome-art dash-intro-art"><HeroArt role={role}/></div></header>;
}
function DashMetrics({ items, go }: { items: DashMetric[]; go: (id: string) => void }) {
  return <section className="dashboard-kpi-grid" aria-label="Chỉ số tổng quan">{items.map((metric, index) => <button className="dashboard-kpi" key={metric.label} onClick={() => go(metric.target)} style={{ animationDelay: `${index * 45}ms` }}><span className="dashboard-kpi-top"><span className="dashboard-kpi-icon"><Icon name={metric.icon} size={20}/></span><Icon name="arrow" size={15}/></span><span className="dashboard-kpi-label">{metric.label}</span><strong>{typeof metric.value === 'number' ? String(metric.value).padStart(2, '0') : metric.value}</strong><small>{metric.note}</small></button>)}</section>;
}
function DashBarList({ rows, total }: { rows: { label: string; value: number; tone: string }[]; total: number }) {
  return <div className="dashboard-bars">{rows.map((row) => <div className="dashboard-bar-row" key={row.label}><div><strong>{row.label}</strong><span>{row.value}</span></div><span className="dashboard-bar-track"><i className={`dashboard-bar-fill dashboard-bar-fill--${row.tone}`} style={{ width: `${total ? row.value / total * 100 : 0}%` }}/></span></div>)}</div>;
}
function DashRing({ value, total, label }: { value: number; total: number; label: string }) {
  const percent = total ? Math.round(value / total * 100) : 0;
  return <div className="dashboard-ring-body"><div className="dashboard-ring" role="img" aria-label={`${value} trên ${total} ${label}`} style={{ '--ring-angle': `${percent * 3.6}deg` } as React.CSSProperties}><span><strong>{percent}%</strong><small>Hoàn thành</small></span></div><div className="dashboard-ring-copy"><strong>{value}/{total}</strong><span>{label}</span></div></div>;
}
function DashSectionNote() { return <div className="dashboard-section-label"><span>TỔNG QUAN</span></div>; }

function TeacherDashboard({ go, openAction }: { go: (id: string) => void; openAction: (type: string) => void }) {
  if (!teacherDashboardPreview) return <div className="role-dashboard role-dashboard--teacher"><DashIntro role="teacher" title="Bảng điều khiển tạm thời chưa có dữ liệu." description="Chưa có dữ liệu tổng quan để hiển thị." action="Mở giáo án" onAction={() => go('lessons')}/><div className="web-panel dashboard-empty-state"><Icon name="alert" size={22}/><strong>Chưa có dữ liệu tổng quan</strong><p>Vui lòng thử lại sau hoặc mở danh sách giáo án.</p></div></div>;
  const lessonRows = teacherDashboardPreview.lessons;
  const activeAssignments = teacherDashboardPreview.assignments.filter((item) => item.active && item.teacherId === 'mai' && Boolean(item.classId));
  const assignedClasses = activeAssignments.map((assignment) => collections.classes.find((item) => item.id === assignment.classId)).filter((item): item is RecordItem => Boolean(item));
  const visibleLessons = lessonRows.filter((item) => item.visibility === 'shared' || item.visibility === 'public');
  const pendingReview = lessonRows.filter((item) => item.reviewState === 'pending' || item.reviewState === 'needs_changes');
  const lessonStatus = (lesson: TeacherLessonSummaryPreview): RecordItem => ({
    id: lesson.id,
    title: lesson.title,
    subtitle: `${lesson.visibility === 'public' ? 'Công khai' : lesson.visibility === 'shared' ? 'Đã chia sẻ' : 'Riêng tư'} · ${lesson.reviewState === 'approved' ? 'Đã duyệt' : lesson.reviewState === 'pending' ? 'Chờ duyệt' : lesson.reviewState === 'needs_changes' ? 'Cần bổ sung' : 'Bản nháp'}`,
    meta: '',
    status: lesson.reviewState === 'approved' ? 'Đã duyệt' : lesson.reviewState === 'pending' ? 'Chờ duyệt' : lesson.reviewState === 'needs_changes' ? 'Cần bổ sung' : 'Bản nháp',
    tone: lesson.reviewState === 'approved' ? 'green' : lesson.reviewState === 'pending' || lesson.reviewState === 'needs_changes' ? 'amber' : 'gray',
  });
  return <div className="role-dashboard role-dashboard--teacher"><DashIntro role="teacher" title="Giáo án và lớp được phân công." description="Tổng quan theo danh sách giáo án, trạng thái chia sẻ và các lớp cô đang phụ trách." action="Soạn giáo án" onAction={() => openAction('new-lesson')}/><DashSectionNote/><DashMetrics go={go} items={[{ label: 'Giáo án', value: lessonRows.length, note: 'Trong thư viện', icon: 'book', target: 'lessons' }, { label: 'Lớp phụ trách', value: assignedClasses.length, note: 'Phân công còn hiệu lực', icon: 'class', target: 'classes' }, { label: 'Đang chia sẻ', value: visibleLessons.length, note: 'Đã chia sẻ & công khai', icon: 'send', target: 'sharing' }, { label: 'Chờ xem xét', value: pendingReview.length, note: 'Chờ duyệt hoặc cần sửa', icon: 'clock', target: 'lessons' }]}/>
    <div className="teacher-next-session-grid"><section className="web-panel teacher-next-session"><div><span className="web-eyebrow">BUỔI DẠY TIẾP THEO</span><h2>{teacherDashboardPreview.nextSession.className}</h2><p>{teacherDashboardPreview.nextSession.time} · {teacherDashboardPreview.nextSession.lesson}</p><small>Hoạt động ghim: {teacherDashboardPreview.nextSession.activity}</small></div><button className="web-primary" onClick={() => go('session')}>Chuẩn bị buổi dạy <Icon name="arrow" size={16}/></button></section><section className="web-panel teacher-feedback-summary"><PanelTitle eyebrow="PHẢN HỒI GIÁO ÁN" title="Cập nhật từ gia đình" action="Mở hộp thư" onAction={() => go('feedback')}/>{teacherDashboardPreview.feedback.map((entry) => <button key={entry.subject} onClick={() => go('feedback')}><span className="dash-list-icon"><Icon name="message" size={17}/></span><span><strong>{entry.subject}</strong><small>{entry.note}</small></span><em>{entry.time}</em></button>)}</section></div>
    <div className="edu-primary-grid"><section className="web-panel edu-progress-panel"><PanelTitle eyebrow="DANH SÁCH GIÁO ÁN" title="Giáo án của cô" action="Xem danh sách" onAction={() => go('lessons')}/>{lessonRows.length ? <div className="edu-lesson-rows">{lessonRows.map((lesson) => { const status = lessonStatus(lesson); return <button key={lesson.id} onClick={() => go('lessons')}><span className="edu-lesson-number"><Icon name="book" size={17}/></span><span className="edu-lesson-copy"><strong>{lesson.title}</strong><small>{status.subtitle}</small></span><Status item={status}/><Icon name="chevron" size={17}/></button>; })}</div> : <div className="dashboard-empty-state"><strong>Chưa có giáo án</strong><p>Giáo án mới sẽ xuất hiện trong danh sách này.</p><button onClick={() => openAction('new-lesson')}>Soạn giáo án</button></div>}</section><section className="web-panel edu-topic-panel"><PanelTitle eyebrow="PHÂN CÔNG" title="Lớp của cô" action="Xem phân công" onAction={() => go('classes')}/>{assignedClasses.length ? <div className="dash-compact-list">{assignedClasses.map((item) => <button key={item.id} onClick={() => go('classes')}><span className="dash-list-icon"><Icon name="class" size={19}/></span><span><strong>{item.title}</strong><small>{item.meta} · Đang phân công</small></span><Icon name="arrow" size={15}/></button>)}</div> : <div className="dashboard-empty-state"><strong>Chưa có lớp được phân công</strong><p>Lớp sẽ hiện tại đây khi có assignment đang hiệu lực.</p></div>}</section></div>
    <div className="edu-final-grid"><section className="web-panel"><PanelTitle eyebrow="TRẠNG THÁI TỪ DANH SÁCH" title="Chia sẻ và xét duyệt"/><div className="teacher-api-status-list"><div><span><i className="is-shared"/>Đang hiển thị với gia đình</span><strong>{visibleLessons.length}</strong></div><div><span><i className="is-pending"/>Chờ xem xét / cần bổ sung</span><strong>{pendingReview.length}</strong></div><div><span><i className="is-draft"/>Bản nháp / riêng tư</span><strong>{lessonRows.filter((item) => item.visibility === 'private' && item.reviewState === 'draft').length}</strong></div></div></section><section className="web-panel"><PanelTitle eyebrow="LỐI TẮT" title="Tiếp tục công việc"/><div className="dash-compact-list"><button onClick={() => go('session')}><span className="dash-list-icon"><Icon name="class" size={19}/></span><span><strong>Bắt đầu buổi dạy</strong><small>Chọn lớp, giáo án và hoạt động</small></span><Icon name="arrow" size={15}/></button><button onClick={() => go('deck')}><span className="dash-list-icon"><Icon name="spark" size={19}/></span><span><strong>Hướng dẫn nét vẽ</strong><small>Tùy chọn theo plan đã duyệt</small></span><Icon name="arrow" size={15}/></button></div></section></div></div>;
}

function ManagerDashboard({ go, openAction }: { go: (id: string) => void; openAction: (type: string) => void }) {
  const classes = collections.classes;
  const teachers = collections.teachers;
  const review = collections.review;
  const assigned = classes.filter((item) => item.status === 'Đang học').length;
  const unassigned = classes.length - assigned;
  return <div className="role-dashboard role-dashboard--manager"><DashIntro role="manager" title="Nắm rõ nhịp học của cả trường." description="Lớp, giáo viên và việc cần duyệt được sắp theo ưu tiên." action="Xem lớp học" onAction={() => go('classes')}/><DashSectionNote/><DashMetrics go={go} items={[{ label: 'Lớp học', value: classes.length, note: 'Trong trường', icon: 'class', target: 'classes' }, { label: 'Giáo viên', value: teachers.length, note: 'Đang phân công', icon: 'users', target: 'teachers' }, { label: 'Đã phân công', value: assigned, note: 'Lớp có giáo viên', icon: 'check', target: 'classes' }, { label: 'Cần xem xét', value: review.length, note: 'Giáo án công khai', icon: 'clock', target: 'review' }]}/>
    <div className="project-primary-grid"><section className="web-panel project-classes-panel"><PanelTitle eyebrow="PHÂN CÔNG" title="Tiến độ lớp học" action="Xem lớp" onAction={() => go('classes')}/><div className="project-class-list">{classes.map((item) => <button key={item.id} onClick={() => go('classes')}><span className="project-class-mark"><Icon name="class" size={18}/></span><span className="project-class-name"><strong>{item.title}</strong><small>{item.subtitle}</small></span><span className={`project-class-track ${item.status === 'Đang học' ? 'is-assigned' : ''}`}><i/></span><span className="project-class-result">{item.status === 'Đang học' ? 'Đã có GV' : 'Cần GV'}</span></button>)}</div></section><section className="web-panel project-review-panel"><PanelTitle eyebrow="CÔNG KHAI" title="Duyệt giáo án" action="Xem hàng chờ" onAction={() => go('review')}/><div className="project-review-count"><strong>{review.length}</strong><span>giáo án cần theo dõi</span></div><div className="project-review-tiles"><span><strong>{review.filter((item) => item.status === 'Chờ xem xét').length}</strong><small>Chờ xem xét</small></span><span><strong>{review.filter((item) => item.status === 'Cần bổ sung').length}</strong><small>Cần bổ sung</small></span></div><div className="project-review-rule"><i/></div><p>Quyết định dựa trên phiên bản và quyền của trường.</p></section></div>
    <div className="project-secondary-grid"><section className="web-panel"><PanelTitle eyebrow="TỔNG QUAN" title="Lớp đã phân công"/><DashRing value={assigned} total={classes.length} label="lớp đã có giáo viên"/></section><section className="web-panel"><PanelTitle eyebrow="NHÂN SỰ" title="Giáo viên phụ trách" action="Xem phân công" onAction={() => go('teachers')}/><div className="project-teacher-list">{teachers.map((item) => <button key={item.id} onClick={() => go('teachers')}><span>{item.title.charAt(0)}</span><strong>{item.title}</strong><small>{item.subtitle}</small></button>)}</div></section></div>
    <div className="project-bottom-grid"><section className="web-panel"><PanelTitle eyebrow="ƯU TIÊN" title="Cần xử lý"/><div className="dash-compact-list"><button onClick={() => go('classes')}><span className="dash-list-icon"><Icon name="alert" size={19}/></span><span><strong>{collections.classes.find((item) => item.status === 'Cần phân công')?.title}</strong><small>Chưa phân công giáo viên</small></span><Icon name="arrow" size={15}/></button><button onClick={() => go('review')}><span className="dash-list-icon"><Icon name="book" size={19}/></span><span><strong>{review[0].title}</strong><small>Giáo án chờ xem xét</small></span><Icon name="arrow" size={15}/></button></div></section><section className="web-panel"><PanelTitle eyebrow="QUY TRÌNH" title="Mốc công việc"/><div className="project-steps"><span className="is-done">Tạo lớp</span><span className={unassigned ? 'is-current' : 'is-done'}>Phân công</span><span>Duyệt giáo án</span></div></section><section className="web-panel"><PanelTitle eyebrow="LỐI TẮT" title="Điều hành nhanh"/><div className="dash-compact-list"><button onClick={() => openAction('new-class')}><Icon name="plus" size={17}/><span><strong>Thêm lớp</strong></span><Icon name="arrow" size={15}/></button><button onClick={() => go('teachers')}><Icon name="users" size={17}/><span><strong>Phân công</strong></span><Icon name="arrow" size={15}/></button><button onClick={() => go('review')}><Icon name="check" size={17}/><span><strong>Duyệt giáo án</strong></span><Icon name="arrow" size={15}/></button></div></section></div></div>;
}

function AdminDashboard({ go }: { go: (id: string) => void }) {
  const catalog = collections.catalog;
  const organizations = collections.organizations;
  const moderation = collections.moderation;
  const published = catalog.filter((item) => item.status === 'Đã phát hành').length;
  const activeOrganizations = organizations.filter((item) => item.status === 'Hoạt động').length;
  const chart = [{ label: 'Danh mục', value: catalog.length, target: 'catalog' }, { label: 'Phát hành', value: published, target: 'catalog' }, { label: 'Chờ duyệt', value: moderation.length, target: 'moderation' }];
  return <div className="role-dashboard role-dashboard--admin"><DashIntro role="admin" title="Nền tảng trong tầm kiểm soát." description="Nội dung, tổ chức và hàng chờ duyệt trong một không gian." action="Xem hàng chờ" onAction={() => go('moderation')}/><DashSectionNote/><DashMetrics go={go} items={[{ label: 'Chờ duyệt', value: moderation.length, note: 'Nội dung công khai', icon: 'shield', target: 'moderation' }, { label: 'Hoạt động', value: catalog.length, note: 'Trong danh mục', icon: 'layer', target: 'catalog' }, { label: 'Đã phát hành', value: published, note: 'Sẵn sàng hiển thị', icon: 'check', target: 'catalog' }, { label: 'Tổ chức', value: organizations.length, note: 'Đang sử dụng', icon: 'class', target: 'organizations' }]}/>
    <div className="commerce-primary-grid"><section className="web-panel commerce-chart-panel"><PanelTitle eyebrow="NỘI DUNG" title="Khối lượng theo nhóm" action="Xem danh mục" onAction={() => go('catalog')}/><div className="commerce-columns" role="group" aria-label="Số lượng nội dung theo nhóm">{chart.map((item, index) => <button key={item.label} onClick={() => go(item.target)}><strong>{item.value}</strong><span className={`commerce-column commerce-column--${index}`} style={{ height: `${item.value / catalog.length * 100}%` }}/><small>{item.label}</small></button>)}</div></section><section className="web-panel commerce-donut-panel"><PanelTitle eyebrow="DANH MỤC" title="Trạng thái phát hành"/><DashRing value={published} total={catalog.length} label="hoạt động đã phát hành"/><div className="commerce-legend"><span><i/>Đã phát hành <strong>{published}</strong></span><span><i/>Chờ duyệt <strong>{catalog.length - published}</strong></span></div></section></div>
    <div className="commerce-middle-grid"><section className="web-panel"><PanelTitle eyebrow="DANH MỤC" title="Hoạt động gần đây" action="Xem tất cả" onAction={() => go('catalog')}/><div className="commerce-table"><div className="commerce-table-head"><span>HOẠT ĐỘNG</span><span>TRẠNG THÁI</span></div>{catalog.map((item) => <button key={item.id} onClick={() => go('catalog')}><span className="dash-list-icon"><Icon name="spark" size={18}/></span><span><strong>{item.title}</strong><small>{item.subtitle}</small></span><Status item={item}/></button>)}</div></section><section className="web-panel"><PanelTitle eyebrow="TỔ CHỨC" title="Đơn vị sử dụng" action="Xem tất cả" onAction={() => go('organizations')}/><div className="commerce-org-summary"><strong>{activeOrganizations}/{organizations.length}</strong><span>đang hoạt động</span></div><div className="dash-compact-list">{organizations.map((item) => <button key={item.id} onClick={() => go('organizations')}><span className="dash-list-icon"><Icon name="class" size={18}/></span><span><strong>{item.title}</strong><small>{item.status}</small></span></button>)}</div></section></div>
    <div className="commerce-bottom-grid"><section className="web-panel"><PanelTitle eyebrow="KIỂM DUYỆT" title="Hàng chờ nội dung" action="Xem tất cả" onAction={() => go('moderation')}/><div className="commerce-table"><div className="commerce-table-head"><span>NỘI DUNG</span><span>TRẠNG THÁI</span></div>{moderation.map((item) => <button key={item.id} onClick={() => go('moderation')}><span className="dash-list-icon"><Icon name="shield" size={18}/></span><span><strong>{item.title}</strong><small>{item.subtitle}</small></span><Status item={item}/></button>)}</div></section><section className="web-panel"><PanelTitle eyebrow="HỆ THỐNG" title="Ảnh chụp vận hành"/><div className="commerce-snapshot"><button onClick={() => go('moderation')}><Icon name="shield" size={20}/><strong>{moderation.length}</strong><span>Chờ duyệt</span></button><button onClick={() => go('organizations')}><Icon name="class" size={20}/><strong>{organizations.length}</strong><span>Tổ chức</span></button><button onClick={() => go('jobs')}><Icon name="spark" size={20}/><strong>—</strong><span>Tác vụ AI</span></button></div></section></div></div>;
}

function Dashboard({ role, go, openAction }: { role: Role; go: (id: string) => void; openAction: (type: string) => void }) {
  return role === 'teacher' ? <TeacherDashboard go={go} openAction={openAction}/> : role === 'manager' ? <ManagerDashboard go={go} openAction={openAction}/> : <AdminDashboard go={go}/>;
}

function CollectionPage({ role, page, items, search, setSearch, filter, setFilter, select, openAction, go }: { role: Role; page: string; items: RecordItem[]; search: string; setSearch: (v: string) => void; filter: string; setFilter: (v: string) => void; select: (id: string) => void; openAction: (type: string) => void; go: (id: string) => void }) {
  const labels: Record<string, [string, string, string]> = {
    lessons: ['Giáo án', 'Tạo, theo dõi và chia sẻ những bài học của lớp.', 'Soạn giáo án'], classes: ['Lớp học', 'Danh sách lớp trong phạm vi phân công.', 'Thêm lớp'], teachers: ['Giáo viên & phân công', 'Mỗi lớp có một giáo viên phụ trách hiện tại.', 'Xem phân công'], review: ['Duyệt giáo án', 'Xem phiên bản và quyết định trong quyền nhà trường.', 'Xem hướng dẫn'], moderation: ['Duyệt nội dung', 'Kiểm tra nội dung theo quyền Content Admin.', 'Xem chính sách'], catalog: ['Danh mục hoạt động', 'Chỉ nội dung đã duyệt và phát hành mới tới người dùng.', 'Tạo bản nháp'], organizations: ['Tổ chức', 'Theo dõi đơn vị sử dụng nền tảng.', 'Thêm tổ chức'], feedback: ['Phản hồi giáo án', 'Trao đổi trong đúng giáo án và tổ chức.', 'Xem phạm vi'], sharing: ['Chia sẻ giáo án', 'Cấp quyền cho đúng phụ huynh hoặc nhóm.', 'Tạo lời mời']
  };
  const [title, description, action] = labels[page] ?? [page, '', 'Tạo mới'];
  const filtered = items.filter((item) => (filter === 'all' || item.status === filter) && `${item.title} ${item.subtitle}`.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi')));
  const statuses = [...new Set(items.map((item) => item.status))];
  const createActionByPage: Record<string, string> = { lessons: 'new-lesson', classes: 'new-class', organizations: 'new-organization', catalog: 'new-activity' };
  const nextPageByPage: Record<string, string> = { teachers: 'assignment', review: 'review', moderation: 'moderation', feedback: 'feedback', sharing: 'sharing' };
  const createAction = createActionByPage[page];
  const nextPage = nextPageByPage[page];
  const showPrimaryAction = Boolean(createAction || nextPage);
  const handlePrimaryAction = () => { if (createAction) openAction(createAction); else if (nextPage) go(nextPage); };
  return <><header className="web-page-head"><div><span className="web-eyebrow">{config[role].scope.toLocaleUpperCase('vi')}</span><h1>{title}</h1><p>{description}</p></div>{(showPrimaryAction || (role === 'teacher' && page === 'lessons')) && <div className="web-head-actions">{role === 'teacher' && page === 'lessons' && <button type="button" className="web-subtle" onClick={() => go('import')}><Icon name="file" size={16}/>Nhập từ tài liệu</button>}{showPrimaryAction && <button className="web-primary" onClick={handlePrimaryAction}><Icon name={createAction ? 'plus' : 'eye'} size={17}/>{action}</button>}</div>}</header>
    <section className="web-panel web-table-panel"><div className="web-toolbar"><label className="web-search"><Icon name="search" size={18}/><span className="web-sr-only">Tìm kiếm {title.toLowerCase()}</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Tìm trong ${title.toLowerCase()}...`}/></label><div className="web-filter" role="group" aria-label="Lọc theo trạng thái"><button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>Tất cả</button>{statuses.map((status) => <button key={status} className={filter === status ? 'active' : ''} onClick={() => setFilter(status)}>{status}</button>)}</div></div><div className="web-list-heading"><span>NỘI DUNG</span><span>PHIÊN BẢN / PHẠM VI</span><span>TRẠNG THÁI</span><span className="web-sr-only">Mở chi tiết</span></div><div className="web-record-list">{filtered.map((item) => <button key={item.id} onClick={() => select(item.id)} className="web-record"><span className="web-record-main"><span className="web-record-avatar"><Icon name={page === 'classes' || page === 'organizations' ? 'class' : page === 'teachers' ? 'users' : page === 'moderation' || page === 'catalog' ? 'shield' : 'book'} size={20}/></span><span><strong>{item.title}</strong><small>{item.subtitle}</small></span></span><span className="web-record-meta">{item.meta}</span><Status item={item}/><Icon name="chevron" size={18}/></button>)}{!filtered.length && <div className="web-empty"><Icon name="search" size={22}/><strong>Không có kết quả phù hợp</strong><p>Thử từ khóa hoặc trạng thái khác.</p><button onClick={() => { setSearch(''); setFilter('all'); }}>Xóa bộ lọc</button></div>}</div><div className="web-list-foot"><span>Hiển thị {filtered.length} mục</span></div></section></>;
}

function useDialogFocus(close: () => void) {
  const dialogRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    const focusables = () => Array.from(dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href]') ?? []);
    (dialog?.querySelector<HTMLElement>('input:not(:disabled)') ?? focusables()[0] ?? dialog)?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); close(); return; }
      if (event.key !== 'Tab') return;
      const elements = focusables();
      if (!elements.length) { event.preventDefault(); dialog?.focus(); return; }
      const first = elements[0], last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('keydown', onKey); previousFocus?.focus(); };
  }, [close]);
  return dialogRef;
}

type DetailNextFlow = { page: string; label: string; description: string };

function detailNextFlow(role: Role, page: string, item: RecordItem): DetailNextFlow | null {
  if (role === 'teacher' && page === 'lessons' && (item.status === 'Đã duyệt' || item.status === 'Đã chia sẻ' || item.subtitle.includes('Đã duyệt'))) return { page: 'occurrences', label: 'Chuẩn bị buổi dạy', description: `Mở luồng chọn lớp, giáo án và phiên bản đã duyệt cho “${item.title}”.` };
  if (role === 'teacher' && page === 'classes') return { page: 'session', label: 'Mở không gian buổi dạy', description: 'Chọn hoạt động, trình chiếu gợi ý nét vẽ và quản lý video mẫu cho lớp.' };
  if (role === 'manager' && page === 'classes') return { page: 'class-lifecycle', label: 'Quản lý lớp học', description: 'Quản lý phân công, sức chứa và trạng thái hoạt động của lớp.' };
  if (role === 'manager' && page === 'teachers') return { page: 'assignment', label: 'Quản lý phân công', description: `Mở màn hình phân công lớp cho giáo viên “${item.title}”.` };
  if (role === 'admin' && page === 'organizations') return { page: 'accounts', label: 'Xem tài khoản và quyền', description: `Mở trang quản lý tài khoản thuộc phạm vi tổ chức “${item.title}”.` };
  return null;
}

function detailOnlyNote(role: Role, page: string, item: RecordItem): string {
  if (role === 'teacher' && page === 'lessons' && item.status === 'Bản nháp') return 'Giáo án đang là bản nháp. Hoàn thiện và gửi rà soát trước khi dùng phiên bản này để chuẩn bị buổi dạy.';
  if (role === 'teacher' && page === 'lessons' && item.status.includes('Chờ')) return 'Giáo án đang chờ rà soát. Theo dõi trạng thái trong thư viện; chỉ phiên bản đã duyệt mới dùng cho buổi dạy.';
  const listName = role === 'teacher' ? (page === 'classes' ? 'danh sách lớp được phân công' : 'thư viện giáo án') : role === 'manager' ? (page === 'teachers' ? 'danh sách giáo viên' : 'danh sách lớp của trường') : 'danh sách tổ chức';
  return `Thông tin chi tiết của ${item.title} trong ${listName}. Đóng cửa sổ để quay lại danh sách.`;
}

function DetailPanel({ item, page, role, close, go, onEdit }: { item: RecordItem; page: string; role: Role; close: () => void; go: (id: string) => void; onEdit: (item: RecordItem) => void }) {
  const dialogRef = useDialogFocus(close);
  const next = detailNextFlow(role, page, item);
  const canEditDraft = role === 'teacher' && page === 'lessons' && item.status === 'Bản nháp';
  const detailEyebrow = page === 'lessons' ? 'GIÁO ÁN' : page === 'classes' ? 'LỚP HỌC' : page === 'teachers' ? 'GIÁO VIÊN' : page === 'organizations' ? 'TỔ CHỨC' : page.toLocaleUpperCase('vi');
  return <div className="web-modal-overlay web-detail-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><section ref={dialogRef} tabIndex={-1} className="web-modal web-detail-modal" role="dialog" aria-modal="true" aria-labelledby="web-detail-title"><button className="web-icon-button web-modal-close" onClick={close} aria-label="Đóng chi tiết"><Icon name="close"/></button><span className="web-eyebrow">CHI TIẾT {detailEyebrow}</span><h2 id="web-detail-title">{item.title}</h2><p>{item.subtitle}</p><Status item={item}/><div className="web-detail-art"><Icon name={page === 'classes' ? 'class' : page === 'organizations' ? 'chart' : 'book'} size={37}/><span/><span/></div><dl><div><dt>Phạm vi</dt><dd>{item.meta}</dd></div><div><dt>Trạng thái</dt><dd>{item.status}</dd></div></dl>{canEditDraft ? <><div className="web-detail-next"><strong>Tiếp tục giáo án này</strong><p>Mở lại các bước mục tiêu, nội dung và chuẩn bị để hoàn thiện bản nháp trước khi gửi quản lý rà soát.</p></div><button className="web-primary" onClick={() => { close(); onEdit(item); }}>Chỉnh sửa bản nháp<Icon name="arrow" size={16}/></button></> : next ? <><div className="web-detail-next"><strong>Bước tiếp theo</strong><p>{next.description}</p></div><button className="web-primary" onClick={() => { close(); go(next.page); }}>{next.label}<Icon name="arrow" size={16}/></button></> : <p className="web-detail-next">{detailOnlyNote(role, page, item)}</p>}<button className="web-subtle" onClick={close}>Quay lại danh sách</button></section></div>;
}

type PreviewLessonStatus = 'Bản nháp' | 'Chờ rà soát';
type PreviewCreate = (name: string, subtitle?: string, meta?: string, status?: PreviewLessonStatus, editId?: string) => void;

function LessonAuthoringDialog({ close, confirm, initial }: { close: () => void; confirm: PreviewCreate; initial?: RecordItem }) {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState(() => initial ? { title: initial.title, topic: initial.subtitle.split(' · ')[0] ?? 'Thiên nhiên', age: '4–5 tuổi', objective: 'Nhận biết hình dạng và màu sắc trong tự nhiên.', drawing: '1. Phác hình lớn. 2. Thêm chi tiết. 3. Tô màu theo ý thích.', knowledge: 'Quan sát một vài đặc điểm của chủ đề.', activities: 'Quan sát cùng người lớn và kể điều con tò mò.', materials: 'Giấy, bút màu và vật liệu an toàn.', safety: 'Người lớn chuẩn bị vật liệu; không cho vật nhỏ vào miệng.', direction: 'Giọng kể nhẹ nhàng, khuyến khích trẻ tự tưởng tượng.' } : { title: '', topic: '', age: '', objective: '', drawing: '', knowledge: '', activities: '', materials: '', safety: '', direction: '' });
  const dialogRef = useDialogFocus(close);
  const update = (field: keyof typeof draft, value: string) => setDraft((current) => ({ ...current, [field]: value }));
  const fields = step === 0 ? <div className="lesson-authoring-grid"><label>Tên giáo án<input value={draft.title} maxLength={100} required autoFocus placeholder="Ví dụ: Khu vườn của em" onChange={(event) => update('title', event.target.value)}/></label><label>Chủ đề<input value={draft.topic} maxLength={80} required placeholder="Thiên nhiên" onChange={(event) => update('topic', event.target.value)}/></label><label>Nhóm tuổi<select value={draft.age} required onChange={(event) => update('age', event.target.value)}><option value="">Chọn nhóm tuổi</option><option>3–4 tuổi</option><option>4–5 tuổi</option><option>5–6 tuổi</option></select></label><label className="lesson-authoring-wide">Mục tiêu học tập<textarea value={draft.objective} maxLength={600} required rows={3} placeholder="Trẻ sẽ quan sát, gọi tên hoặc thử làm điều gì?" onChange={(event) => update('objective', event.target.value)}/></label></div> : step === 1 ? <div className="lesson-authoring-grid"><label>Hướng dẫn nét vẽ<textarea value={draft.drawing} maxLength={800} required rows={4} placeholder="Các bước ngắn, rõ, phù hợp với trẻ…" onChange={(event) => update('drawing', event.target.value)}/></label><label>Kiến thức chủ đề<textarea value={draft.knowledge} maxLength={800} rows={4} placeholder="Thông tin nền cần đưa vào bài học…" onChange={(event) => update('knowledge', event.target.value)}/></label><label className="lesson-authoring-wide">Hoạt động và hướng dẫn<textarea value={draft.activities} maxLength={1000} required rows={4} placeholder="Tên hoạt động, cách tổ chức và câu hỏi gợi mở…" onChange={(event) => update('activities', event.target.value)}/></label></div> : <div className="lesson-authoring-grid"><label>Vật liệu cần chuẩn bị<textarea value={draft.materials} maxLength={600} required rows={3} placeholder="Liệt kê vật liệu và cách chuẩn bị…" onChange={(event) => update('materials', event.target.value)}/></label><label>Lưu ý an toàn<textarea value={draft.safety} maxLength={600} required rows={3} placeholder="Nêu rủi ro và cách giảm thiểu…" onChange={(event) => update('safety', event.target.value)}/></label><label className="lesson-authoring-wide">Định hướng lời kể / kịch bản<textarea value={draft.direction} maxLength={600} rows={3} placeholder="Giọng kể và ý cần giữ trong câu chuyện…" onChange={(event) => update('direction', event.target.value)}/></label></div>;
  return <div className="web-modal-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><section ref={dialogRef} tabIndex={-1} className="web-modal web-modal--wide" role="dialog" aria-modal="true" aria-labelledby="lesson-authoring-title"><button className="web-icon-button web-modal-close" onClick={close} aria-label="Đóng"><Icon name="close"/></button><span className="web-eyebrow">GIÁO ÁN · {initial ? 'CHỈNH SỬA' : 'SOẠN MỚI'}</span><h2 id="lesson-authoring-title">{initial ? 'Chỉnh sửa giáo án' : 'Soạn giáo án mới'}</h2><div className="lesson-authoring-progress" aria-label={`Bước ${step + 1} trên 3`}>{['Mục tiêu','Nội dung','Chuẩn bị'].map((label, index) => <span key={label} className={index === step ? 'is-current' : index < step ? 'is-done' : ''}><i>{index < step ? '✓' : index + 1}</i>{label}</span>)}</div><form onSubmit={(event) => { event.preventDefault(); if (step < 2) setStep((current) => current + 1); else { const submitter = (event.nativeEvent as SubmitEvent).submitter; const status: PreviewLessonStatus = submitter instanceof HTMLButtonElement && submitter.value === 'review' ? 'Chờ rà soát' : 'Bản nháp'; confirm(draft.title.trim(), `${draft.topic} · ${draft.age} · ${draft.objective.trim()}`, status === 'Chờ rà soát' ? 'Chờ rà soát' : 'Bản nháp', status, initial?.id); } }}><div className="lesson-authoring-fields">{fields}</div><div className="web-modal-actions lesson-authoring-actions">{step > 0 && <button type="button" className="web-subtle" onClick={() => setStep((current) => current - 1)}>Quay lại</button>}{step < 2 ? <button type="submit" className="web-primary">Tiếp tục<Icon name="arrow" size={15}/></button> : <div className="lesson-authoring-submit-group"><button type="submit" name="lesson-intent" value="draft" className="web-subtle">{initial ? 'Lưu thay đổi' : 'Lưu bản nháp'}</button><button type="submit" name="lesson-intent" value="review" className="web-primary">Gửi quản lý rà soát<Icon name="arrow" size={15}/></button></div>}</div></form></section></div>;
}

function ActionDialog({ type, close, confirm }: { type: string; close: () => void; confirm: PreviewCreate }) {
  const creations = {
    'new-class': { title: 'Thêm lớp học', label: 'Tên lớp' },
    'new-organization': { title: 'Thêm tổ chức', label: 'Tên tổ chức' },
    'new-activity': { title: 'Tạo hoạt động nháp', label: 'Tên hoạt động' },
  } as const;
  const creation = creations[type as keyof typeof creations];
  const [name, setName] = useState('');
  const dialogRef = useDialogFocus(close);
  if (!creation) return null;
  return <div className="web-modal-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><section ref={dialogRef} tabIndex={-1} className="web-modal" role="dialog" aria-modal="true" aria-labelledby="web-modal-title"><button className="web-icon-button web-modal-close" onClick={close} aria-label="Đóng"><Icon name="close"/></button><span className="web-modal-icon"><Icon name="plus" size={25}/></span><h2 id="web-modal-title">{creation.title}</h2><form onSubmit={(event) => { event.preventDefault(); if (name.trim()) confirm(name.trim()); }}><p>Nhập thông tin để thêm mục mới vào danh sách.</p><label htmlFor="web-create-name">{creation.label}</label><input id="web-create-name" value={name} maxLength={100} onChange={(event) => setName(event.target.value)} placeholder="Nhập tên rõ ràng..." required/><div className="web-modal-actions"><button type="button" className="web-subtle" onClick={close}>Hủy</button><button type="submit" className="web-primary" disabled={!name.trim()}>Thêm bản nháp</button></div></form></section></div>;
}

type PushPreviewScenario = 'supported' | 'denied' | 'unsupported' | 'invalid-endpoint';

function TeacherPushEnrollment() {
  const [scenario, setScenario] = useState<PushPreviewScenario>('supported');
  const [enabled, setEnabled] = useState(false);
  const [notice, setNotice] = useState('');
  const copy: Record<PushPreviewScenario, {title: string; body: string; action: string}> = {
    supported: {title: enabled ? 'Đã bật thông báo đẩy' : 'Có thể bật thông báo', body: 'Nhận thông báo đẩy ngay trên trình duyệt khi giáo án hoặc buổi dạy có cập nhật.', action: enabled ? 'Tắt thông báo' : 'Bật thông báo'},
    denied: {title: 'Quyền thông báo bị từ chối', body: 'Bạn có thể bật lại quyền thông báo trong cài đặt trình duyệt. Hộp thư trong ứng dụng vẫn hoạt động bình thường.', action: 'Xem hướng dẫn cài đặt'},
    unsupported: {title: 'Trình duyệt chưa hỗ trợ Web Push', body: 'Bạn vẫn có thể xem đầy đủ thông báo trong hộp thư trên ứng dụng.', action: ''},
    'invalid-endpoint': {title: 'Kết nối thông báo cần làm mới', body: 'Đăng ký thông báo cũ không còn hợp lệ. Hãy bật lại để tiếp tục nhận thông báo đẩy.', action: 'Làm mới kết nối'},
  };
  const selected = copy[scenario];
  const changeScenario = (next: PushPreviewScenario): void => {
    setScenario(next);
    setEnabled(false);
    setNotice('');
  };
  const runAction = (): void => {
    if (scenario === 'supported') {
      setEnabled((current) => !current);
      setNotice(enabled ? 'Đã tắt thông báo đẩy trên thiết bị này.' : 'Đã bật thông báo đẩy trên trình duyệt.');
      return;
    }
    if (scenario === 'denied') setNotice('Vui lòng mở Cài đặt trình duyệt > Quyền riêng tư để bật lại thông báo.');
    if (scenario === 'invalid-endpoint') setNotice('Đã thu hồi kết nối cũ. Bạn có thể bật lại thông báo.');
  };
  return <section className="web-panel push-enrollment-panel" aria-labelledby="teacher-push-title"><div className="push-panel-heading"><div><span className="web-eyebrow">WEB PUSH</span><h2 id="teacher-push-title">Thông báo trên trình duyệt</h2></div><span className="web-status web-status--blue">{enabled ? 'Đang bật' : 'Sẵn sàng'}</span></div><label className="push-scenario-label">Tình huống thiết bị<select value={scenario} onChange={(event) => changeScenario(event.target.value as PushPreviewScenario)}><option value="supported">Trình duyệt hỗ trợ</option><option value="denied">Quyền bị từ chối</option><option value="unsupported">Không hỗ trợ Web Push</option><option value="invalid-endpoint">Endpoint lỗi</option></select></label><article className={`push-state-card push-state-card--${scenario}`} role="status" aria-live="polite"><strong>{selected.title}</strong><p>{selected.body}</p>{selected.action ? <button type="button" className="web-subtle" onClick={runAction}>{selected.action}</button> : null}{notice ? <small>{notice}</small> : null}</article><div className="push-inbox-note"><Icon name="bell" size={18}/><span><strong>Hộp thư vẫn khả dụng</strong><small>Inbox là nguồn thông báo chuẩn; push chỉ là kênh bổ sung.</small></span></div></section>;
}

function FeaturePage({ role, page, go }: { role: Role; page: string; go: (id: string) => void }) {
  const [localFile, setLocalFile] = useState('');
  const content: Record<string, { eyebrow: string; title: string; description: string; icon: IconKey; steps: { title: string; body: string }[]; action: string; target: string }> = {
    import: { eyebrow: 'BÀI GIẢNG TRÊN LỚP', title: 'Tài liệu thành giáo án rõ ràng.', description: 'Tải PDF, DOCX hoặc PPTX rồi kiểm tra phần trích xuất trước khi dùng cho buổi dạy.', icon: 'file', steps: [{ title: 'Tải tài liệu', body: 'Giữ bản gốc và kiểm tra định dạng.' }, { title: 'Xem phần trích xuất', body: 'Sửa nội dung trước khi tạo phiên bản mới.' }, { title: 'Gắn vào giáo án', body: 'Pin đúng bản đã duyệt cho buổi dạy.' }], action: 'Xem giáo án', target: 'lessons' },
    deck: { eyebrow: 'GỢI Ý NÉT VẼ', title: 'Một hướng dẫn cho cả buổi học.', description: 'Sketch Deck được tạo từ plan đã duyệt của occurrence, không lấy hồ sơ hoặc tranh trẻ làm đầu vào.', icon: 'spark', steps: [{ title: 'Plan được duyệt', body: 'Xem toàn bộ hoạt động và chủ đề.' }, { title: 'Bật hướng dẫn', body: 'AI tạo 3–5 bước nét vẽ cho từng hoạt động.' }, { title: 'Kiểm tra trước khi chiếu', body: 'Chỉ dùng kết quả hợp lệ, an toàn và đúng phiên bản.' }], action: 'Xem giáo án', target: 'lessons' },
    sample: { eyebrow: 'VIDEO MẪU CHO LỚP', title: 'Từ một bức tranh đến câu chuyện.', description: 'Một occurrence chỉ có một video mẫu phát được, gắn với đúng một trẻ được hệ thống chọn và người lớn xác nhận.', icon: 'video', steps: [{ title: 'Xác nhận trẻ và tranh', body: 'Quyền, sự đồng ý và chủ thể được kiểm tra.' }, { title: 'Duyệt kịch bản', body: 'Người lớn duyệt revision cuối trước khi tạo video.' }, { title: 'Chiếu sau kiểm tra', body: 'Video chỉ mở khi kiểm tra kỹ thuật và an toàn đạt.' }], action: 'Xem lớp học', target: 'classes' },
    sharing: { eyebrow: 'CHIA SẺ GIÁO ÁN', title: 'Bài học đi đúng gia đình.', description: 'Giáo viên chia sẻ đúng lesson version và người nhận; lời mời chưa được chấp nhận không cấp quyền đọc.', icon: 'send', steps: [{ title: 'Chọn giáo án', body: 'Xác nhận phiên bản muốn chia sẻ.' }, { title: 'Chọn người nhận', body: 'Dùng tài khoản hoặc nhóm đã xác minh.' }, { title: 'Theo dõi lời mời', body: 'Chỉ sau khi nhận, phụ huynh mới thấy nội dung.' }], action: 'Chọn giáo án', target: 'lessons' },
    quota: { eyebrow: 'LƯỢT TẠO & GÓI', title: 'Quản lý ngân sách sáng tạo.', description: 'Lượt tạo video của giáo viên thuộc quota trường. Giá và quyền mua bổ sung phải do Billing và chủ dự án xác nhận.', icon: 'chart', steps: [{ title: 'Số dư theo tổ chức', body: 'Số liệu sẽ có khi hệ thống vận hành thật.' }, { title: 'Mỗi yêu cầu được nhận', body: 'Ghi một usage receipt; không tự hoàn lượt.' }, { title: 'Mua bổ sung', body: 'Chỉ mở khi quyền và chính sách đã được duyệt.' }], action: 'Xem lớp học', target: 'classes' },
    jobs: { eyebrow: 'VẬN HÀNH AI', title: 'Theo dõi công việc, giữ riêng tư.', description: 'Quản trị chỉ thấy trạng thái và dữ liệu vận hành được cấp quyền; không mở tranh hoặc video trẻ.', icon: 'spark', steps: [{ title: 'Hàng đợi', body: 'Trạng thái sẽ có khi tác vụ được vận hành thật.' }, { title: 'Lỗi có thể khôi phục', body: 'Hiện mã và hành động vận hành phù hợp.' }, { title: 'Kiểm tra an toàn', body: 'Không phát media chưa đạt hoặc kết quả stale.' }], action: 'Xem nội dung chờ duyệt', target: 'moderation' },
    audit: { eyebrow: 'NHẬT KÝ VẬN HÀNH', title: 'Mọi quyết định có dấu vết.', description: 'Nhật ký cần phân quyền, thời điểm, actor và phiên bản liên quan; không đưa dữ liệu trẻ vào danh sách quản trị.', icon: 'file', steps: [{ title: 'Lọc sự kiện', body: 'Theo tổ chức, actor và loại thao tác.' }, { title: 'Xem quyết định', body: 'Đọc lý do và phiên bản dữ liệu.' }, { title: 'Bảo vệ log', body: 'Không hiển thị token, media hoặc thông tin nhạy cảm.' }], action: 'Xem tổ chức', target: 'organizations' },
  };
  const item = content[page];
  if (page === 'settings') return <><header className="web-page-head"><div><span className="web-eyebrow">{config[role].scope.toLocaleUpperCase('vi')}</span><h1>Cài đặt</h1><p>Tùy chọn cổng web và phạm vi tài khoản.</p></div></header><div className="web-feature-grid"><section className="web-panel"><PanelTitle eyebrow="TÀI KHOẢN" title="Vai trò hiện tại"/><div className="web-setting-row"><span><Icon name="users"/></span><div><strong>{config[role].name}</strong><small>Quyền truy cập phụ thuộc vào tài khoản được cấp.</small></div></div><div className="web-setting-row"><span><Icon name="shield"/></span><div><strong>Quyền dữ liệu</strong><small>Chỉ hiển thị nội dung thuộc phạm vi được cấp.</small></div><span className="web-setting-value">Theo quyền tài khoản</span></div></section><section className="web-panel"><PanelTitle eyebrow="GIAO DIỆN" title="Trải nghiệm sử dụng"/><div className="web-setting-row"><span><Icon name="spark"/></span><div><strong>Chuyển động nhẹ</strong><small>Hiệu ứng tuân theo thiết lập giảm chuyển động của hệ thống.</small></div><span className="web-setting-value">Đang bật</span></div><div className="web-setting-row"><span><Icon name="bell"/></span><div><strong>Thông báo</strong><small>Theo dõi cập nhật trực tiếp trong hộp thư thông báo trên web.</small></div><span className="web-setting-value">Đang bật</span></div></section>{role === 'teacher' ? <TeacherPushEnrollment/> : null}</div></>;
  if (!item) return null;
  return <><header className="web-page-head"><div><span className="web-eyebrow">{item.eyebrow}</span><h1>{item.title}</h1><p>{item.description}</p></div></header><div className="web-feature-grid web-feature-grid--single"><section className="web-panel web-feature-main"><span className="web-feature-emblem"><Icon name={item.icon} size={30}/></span><h2>Luồng làm việc</h2><div className="web-step-list">{item.steps.map((step, index) => <div className="web-step" key={step.title}><span>{String(index + 1).padStart(2, '0')}</span><div><strong>{step.title}</strong><p>{step.body}</p></div></div>)}</div>{page === 'import' ? <div className="web-file-preview"><label htmlFor="web-lesson-file"><Icon name="file" size={22}/><strong>{localFile || 'Chọn PDF, DOCX hoặc PPTX'}</strong><small>{localFile ? 'Tệp đã sẵn sàng để trích xuất nội dung.' : 'Hỗ trợ PDF, DOCX hoặc PPTX (tối đa 25 MB).'}</small></label><input id="web-lesson-file" type="file" accept=".pdf,.docx,.pptx" onChange={(event) => setLocalFile(event.target.files?.[0]?.name ?? '')}/></div> : null}<button className="web-primary" onClick={() => go(item.target)}>{item.action}<Icon name="arrow" size={17}/></button></section></div></>;
}

export function Workspace({ role, onLogout }: { role: Role; onLogout?: () => void }) {
  const c = config[role];
  const sections = useMemo(() => {
    const grouped: { label: string; items: NavItem[] }[] = [];
    let currentLabel = 'TỔNG QUAN';
    for (const item of c.nav) {
      if (item.group) currentLabel = item.group;
      let section = grouped[grouped.length - 1];
      if (!section || section.label !== currentLabel) {
        section = { label: currentLabel, items: [] };
        grouped.push(section);
      }
      section.items.push(item);
    }
    return grouped;
  }, [c.nav]);
  const readRoute = () => resolveRoute(role, window.location.hash.slice(1));
  const [route, setRoute] = useState(readRoute);
  const page = route.page;
  const activeRouteId = route.routeId;
  const activeHub = workspaceHubs[role]?.[page];
  const activeHubTab = activeHub?.tabs.find((tab) => tab.routeId === activeRouteId);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [openRailGroup, setOpenRailGroup] = useState<string | null>(null);
  const [closedSections, setClosedSections] = useState<string[]>(() => sections.filter((section) => section.label !== 'TỔNG QUAN' && !section.items.some((item) => item.id === readRoute().page)).map((section) => section.label));
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState<string | null>(null);
  const [dialog, setDialog] = useState<string | null>(null);
  const [editingLesson, setEditingLesson] = useState<RecordItem | null>(null);
  const [noticeOpen, setNoticeOpen] = useState(false);
  const [toast, setToast] = useState('');
  const [additions, setAdditions] = useState<Record<string, RecordItem[]>>({});
  const [lessonOverrides, setLessonOverrides] = useState<Record<string, RecordItem>>({});
  useEffect(() => {
    setRoute(resolveRoute(role, window.location.hash.slice(1)));
    const change = () => setRoute(resolveRoute(role, window.location.hash.slice(1)));
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, [role]);
  useEffect(() => { const activeSection = sections.find((section) => section.items.some((item) => item.id === page)); if (activeSection) setClosedSections(sections.filter((section) => section.label !== 'TỔNG QUAN' && section.label !== activeSection.label).map((section) => section.label)); }, [page, sections]);
  useEffect(() => { const viewport = window.matchMedia('(max-width: 900px)'); const sync = () => { if (viewport.matches) { setNavCollapsed(false); setOpenRailGroup(null); } }; sync(); viewport.addEventListener('change', sync); return () => viewport.removeEventListener('change', sync); }, []);
  useEffect(() => { if (!toast) return; const id = window.setTimeout(() => setToast(''), 3500); return () => window.clearTimeout(id); }, [toast]);
  const go = (id: string) => {
    const resolved = resolveRoute(role, id);
    if (resolved.page === 'home' && id !== 'home') return;
    window.location.hash = resolved.routeId;
    setRoute(resolved);
    setSearch('');
    setFilter('all');
    setSelected(null);
    setMobileMenu(false);
    setOpenRailGroup(null);
    setNoticeOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const collectionKey = activeRouteId === 'sharing' ? 'lessons' : activeRouteId;
  const items = useMemo(() => [...(additions[collectionKey] ?? []), ...(collections[collectionKey] ?? [])].map((item) => lessonOverrides[item.id] ?? item), [collectionKey, additions, lessonOverrides]);
  const selectedItem = items.find((item) => item.id === selected) ?? null;
  const saveImportDraft = (draft: { title: string; subtitle: string; meta: string }) => {
    const newItem: RecordItem = {
      id: `preview-import-${Date.now()}`,
      title: draft.title,
      subtitle: draft.subtitle,
      meta: draft.meta,
      status: 'Bản nháp',
      tone: 'amber',
    };
    setAdditions((current) => ({ ...current, lessons: [newItem, ...(current.lessons ?? [])] }));
    setToast('Đã lưu bản nháp giáo án vào thư viện.');
    go('lessons');
  };
  const onCreate = (name: string, subtitle?: string, meta?: string, status: PreviewLessonStatus = 'Bản nháp', editId?: string) => {
    if (editId) {
      const current = [...(additions.lessons ?? []), ...collections.lessons].find((item) => item.id === editId);
      if (current) setLessonOverrides((overrides) => ({ ...overrides, [editId]: { ...current, title: name, subtitle: subtitle || current.subtitle, meta: meta || current.meta, status, tone: status === 'Chờ rà soát' ? 'blue' : 'amber' } }));
      setEditingLesson(null);
      setToast(status === 'Chờ rà soát' ? 'Đã gửi yêu cầu rà soát giáo án.' : 'Đã lưu thay đổi bản nháp.');
      go('lessons');
      return;
    }
    const key = dialog === 'new-lesson' ? 'lessons' : dialog === 'new-class' ? 'classes' : dialog === 'new-organization' ? 'organizations' : 'catalog';
    const newItem: RecordItem = { id: `preview-${Date.now()}`, title: name, subtitle: subtitle || 'Vừa tạo mới', meta: meta || 'Bản nháp', status, tone: status === 'Chờ rà soát' ? 'blue' : 'amber' };
    setAdditions((current) => ({ ...current, [key]: [newItem, ...(current[key] ?? [])] }));
    setDialog(null);
    setToast(status === 'Chờ rà soát' ? 'Đã gửi giáo án vào hàng chờ rà soát.' : 'Đã thêm bản nháp mới.');
    go(key);
  };
  return <div className={`web-app web-app--${role} ${navCollapsed ? 'web-app--nav-collapsed' : ''}`}><a className="web-skip" href="#main-content" onClick={(event) => { event.preventDefault(); window.requestAnimationFrame(() => document.getElementById("main-content")?.focus()); }}>Bỏ qua điều hướng</a><aside className={`web-sidebar ${mobileMenu ? 'is-open' : ''}`}><div className="web-brand"><BrandMark size={41}/><div className="web-brand-copy"><strong>Sketch<span>2</span>Life</strong><small>{c.scope}</small></div><button className="web-icon-button web-collapse-toggle" onClick={() => { setNavCollapsed((value) => !value); setOpenRailGroup(null); }} aria-label={navCollapsed ? 'Mở rộng menu' : 'Thu gọn menu'} aria-expanded={!navCollapsed} title={navCollapsed ? 'Mở rộng menu' : 'Thu gọn menu'}><Icon name="chevron" size={17}/></button><button className="web-icon-button web-mobile-close" onClick={() => setMobileMenu(false)} aria-label="Đóng menu"><Icon name="close"/></button></div><div className="web-role-card" title={c.name}><span><Icon name={role === 'teacher' ? 'book' : role === 'manager' ? 'class' : 'shield'} size={20}/></span><div><strong>{c.name}</strong><small>{c.scope}</small></div></div><nav className="web-nav" aria-label={`Điều hướng ${c.name}`}>{sections.map((section) => <section className={["web-nav-section", section.label === "TỔNG QUAN" ? "web-nav-section--overview" : "", openRailGroup === section.label ? "is-rail-open" : "", section.items.some((item) => item.id === page) ? "has-active-page" : ""].filter(Boolean).join(" ")} key={section.label}><button type="button" className="web-nav-group" title={section.label} onClick={() => { if (section.label === 'TỔNG QUAN') return; if (navCollapsed) { setOpenRailGroup((current) => current === section.label ? null : section.label); return; } setClosedSections((current) => current.includes(section.label) ? current.filter((label) => label !== section.label) : [...current, section.label]); }} aria-expanded={section.label === 'TỔNG QUAN' || (navCollapsed ? openRailGroup === section.label : !closedSections.includes(section.label))} aria-controls={`nav-section-${role}-${section.label.replace(/[^a-z0-9]+/gi, '-')}`}><Icon name={section.items[0]?.icon ?? 'grid'} size={18}/><span>{section.label}</span><Icon name="chevron" size={14}/></button><div id={`nav-section-${role}-${section.label.replace(/[^a-z0-9]+/gi, '-')}`} className={`web-nav-section-items ${(section.label !== 'TỔNG QUAN' && (navCollapsed ? openRailGroup !== section.label : closedSections.includes(section.label))) ? 'is-collapsed' : ''}`}>{section.items.map((item) => <button key={item.id} title={navCollapsed ? item.label : undefined} className={page === item.id ? 'active' : ''} onClick={() => go(item.id)} aria-current={page === item.id ? 'page' : undefined}><Icon name={item.icon} size={19}/><span>{item.label}</span>{page === item.id && <i/>}</button>)}</div></section>)}</nav><div className="web-sidebar-footer"><div className="web-sidebar-user" title={`${c.displayName} · ${c.name}`}><span className="web-sidebar-user-avatar" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="3.2" fill="currentColor"/><path d="M5 20c.5-3.6 2.8-5.6 7-5.6s6.5 2 7 5.6" fill="currentColor"/></svg></span><span className="web-sidebar-user-copy"><strong>{c.displayName}</strong><small>{c.name}</small></span></div>{onLogout && (navCollapsed ? <button className="web-logout web-logout--compact" onClick={onLogout} aria-label="Đăng xuất và đổi tài khoản" title="Đăng xuất"><Icon name="arrow" size={18}/></button> : <button className="web-logout" onClick={onLogout} aria-label="Đăng xuất và đổi tài khoản">Đăng xuất</button>)}</div></aside>{navCollapsed && openRailGroup && <button className="web-rail-dismiss" onClick={() => setOpenRailGroup(null)} aria-label="Đóng nhóm menu"/>}{mobileMenu && <button className="web-mobile-scrim" onClick={() => setMobileMenu(false)} aria-label="Đóng menu"/>}
    <div className="web-main-frame"><header className="web-topbar"><button className="web-icon-button web-menu-toggle" onClick={() => setMobileMenu(true)} aria-label="Mở menu"><Icon name="menu"/></button><div className="web-breadcrumb"><span>Sketch2Life</span><Icon name="chevron" size={15}/><strong>{c.nav.find((item) => item.id === page)?.label ?? 'Tổng quan'}</strong>{activeHubTab && activeHubTab.routeId !== page ? <><Icon name="chevron" size={14}/><small>{activeHubTab.label}</small></> : null}</div><div className="web-top-actions"><button className="web-icon-button" onClick={() => setNoticeOpen((value) => !value)} aria-label="Mở thông báo" aria-expanded={noticeOpen}><Icon name="bell" size={20}/></button></div>{noticeOpen && <div className="web-popover"><strong>Thông báo</strong><p>Chưa có thông báo mới.</p><div className="web-popover-actions"><button type="button" className="web-primary-inline" onClick={() => go(role === 'teacher' ? 'inbox' : 'notifications')}>Mở hộp thư thông báo</button><button type="button" onClick={() => setNoticeOpen(false)}>Đóng</button></div></div>}</header>
      <main id="main-content" tabIndex={-1} className="web-content">{page !== 'home' && activeHub ? <nav className="web-hub-bar" aria-label={activeHub.label}><div className="web-hub-tabs" role="tablist" aria-label={activeHub.label}>{activeHub.tabs.map((tab) => { const selectedTab = activeRouteId === tab.routeId; return <button key={tab.routeId} type="button" role="tab" aria-selected={selectedTab} className={`web-hub-tab${selectedTab ? ' is-active' : ''}`} onClick={() => go(tab.routeId)}><span>{tab.label}</span></button>; })}</div></nav> : null}{activeRouteId === 'home' ? <Dashboard role={role} go={go} openAction={setDialog}/> : hasRoleFlow(role, activeRouteId) ? <RoleFlowPage role={role} page={activeRouteId} onNavigate={go} onSaveImportDraft={saveImportDraft}/> : ['lessons','classes','teachers','review','moderation','catalog','organizations','feedback','sharing'].includes(activeRouteId) ? <CollectionPage role={role} page={activeRouteId} items={role === 'teacher' && activeRouteId === 'classes' ? items.filter((item) => item.subtitle.includes('Cô Mai')) : items} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} select={setSelected} openAction={setDialog} go={go}/> : <FeaturePage role={role} page={activeRouteId} go={go}/>}<footer className="web-footer"><span>Sketch2Life · {c.name}</span><span>Không gian làm việc cho nhà trường</span></footer></main></div>
    {selectedItem && <DetailPanel item={selectedItem} page={activeRouteId} role={role} close={() => setSelected(null)} go={go} onEdit={setEditingLesson}/ >}{editingLesson && <LessonAuthoringDialog key={editingLesson.id} initial={editingLesson} close={() => setEditingLesson(null)} confirm={onCreate}/ >}{dialog === 'new-lesson' ? <LessonAuthoringDialog close={() => setDialog(null)} confirm={onCreate}/> : dialog && <ActionDialog type={dialog} close={() => setDialog(null)} confirm={onCreate}/ >}{toast && <div className="web-toast" role="status"><Icon name="check" size={17}/>{toast}</div>}
  </div>;
}

