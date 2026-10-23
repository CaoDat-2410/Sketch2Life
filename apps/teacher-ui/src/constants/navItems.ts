import { TEACHER_ROUTES } from '../types/routes';

export const TEACHER_NAV_ITEMS = [
  { label: 'Trang chủ', path: TEACHER_ROUTES.HOME, icon: 'Home' },
  { label: 'Điều phối phiên học', path: TEACHER_ROUTES.SESSION_ORCHESTRATE, icon: 'PlayCircle' },
  { label: 'Không gian nhóm', path: TEACHER_ROUTES.GROUP_WORKSPACE, icon: 'Users' },
  { label: 'Duyệt gợi ý AI', path: TEACHER_ROUTES.AI_SUGGESTION_REVIEW, icon: 'Sparkles' },
  { label: 'Video học tập', path: TEACHER_ROUTES.VIDEO_KNOWLEDGE, icon: 'Video' },
  { label: 'Hoạt động thực tế', path: TEACHER_ROUTES.OFFLINE_ACTIVITIES, icon: 'Layers' },
  { label: 'Hồ sơ lớp học', path: TEACHER_ROUTES.CLASSES_PROFILES, icon: 'BookOpen' },
  { label: 'Bộ sưu tập tranh', path: TEACHER_ROUTES.CLASS_GALLERY, icon: 'Image' },
  { label: 'Nhật ký quan sát', path: TEACHER_ROUTES.OBSERVATION_FEEDBACK, icon: 'ClipboardCheck' },
];
