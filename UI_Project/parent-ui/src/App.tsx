import { ChangeEvent, FormEvent, createContext, useContext, useEffect, useId, useRef, useState } from 'react';

const SettingsContext = createContext<(() => void) | null>(null);

type Screen = 'home' | 'history' | 'profile' | 'child-detail' | 'group-invitations' | 'change-password' | 'privacy' | 'flow' | 'activities' | 'session-feedback' | 'library' | 'lesson-detail' | 'delivery-detail' | 'notifications' | 'sharing' | 'share-form' | 'quota' | 'feedback' | 'auth' | 'signup' | 'recovery' | 'child-form' | 'run-detail';
type Step = 'prepare' | 'guide' | 'capture' | 'idea' | 'review' | 'script' | 'generating' | 'ready';
type IconName = 'home' | 'clock' | 'user' | 'spark' | 'star' | 'expand' | 'arrow' | 'back' | 'camera' | 'upload' | 'book' | 'check' | 'lock' | 'play' | 'mic' | 'edit' | 'plus' | 'chevron' | 'settings' | 'close' | 'leaf' | 'trash' | 'bell' | 'search' | 'share' | 'download' | 'message' | 'calendar' | 'file' | 'logout' | 'refresh' | 'mail' | 'eye' | 'eyeOff';
type HistoryTab = 'stories' | 'lessons';
type HistoryStatus = 'all' | 'open' | 'completed';
type PreviewJobState = 'processing' | 'failed' | 'safety-blocked';

type Child = { id: string; name: string; ageMonths: number; tone: string; initial: string; gender: 'girl' | 'boy' | 'unspecified'; nickname?: string; supportNeeds?: string; photoUrl?: string; interests?: string; observations?: string; achievements?: string; externalExperiences?: string };
type ProfileContextField = 'interests' | 'observations' | 'achievements' | 'externalExperiences';
type StoryFeedback = { rating: number; tags: string[]; note: string };
type Story = { id: number; title: string; date: string; dateDaysAgo?: number; childId: string; child: string; color: string; subtitle: string; status?: 'active' | 'ready' | 'completed'; lessonId?: string | null; hidden?: boolean; sessionFeedback?: StoryFeedback };
type LessonDelivery = { id: string; lessonId: string; title: string; childId: string; child: string; date: string; school: string; teacher: string; teacherReply?: string; parentFeedback?: string };
type ShareGrant = { id: string; childId: string; recipient: string; organization: string; status: 'invited' | 'active'; date: string };
type VerifiedTeacher = { id: string; name: string; school: string };
type LessonInvitation = { id: string; lessonId: string; teacher: string; school: string; status: 'pending' | 'accepted' | 'declined' };
type GroupInvitation = { id: string; name: string; school: string; status: 'pending' | 'accepted' };
type AppNotice = { id: string; title: string; body: string; date: string; read: boolean; kind: 'story' | 'feedback' | 'run' };
type RunRecord = { id: string; childId: string; lessonId: string | null; step: Step; status: 'active' | 'ready'; rewriteCount: number; regenCount: number; scriptFollowing: 'lesson' | 'free' | null; needsRegeneration?: boolean };

const children: Child[] = [
  { id: 'an', name: 'Bé An', ageMonths: 60, tone: 'peach', initial: 'A', gender: 'girl' },
  { id: 'minh', name: 'Bé Minh', ageMonths: 84, tone: 'lavender', initial: 'M', gender: 'boy' },
];

const lessons = [
  { id: 'garden', title: 'Khám phá khu vườn', meta: '3 hoạt động · Chủ đề thiên nhiên', color: 'sage', visibility: 'Được chia sẻ với gia đình', ageTarget: '3–6 tuổi', version: 'v1.4', description: 'Cùng bé quan sát khu vườn và kể chuyện qua những điều con nhìn thấy.', activities: [{ title: 'Quan sát một bông hoa', materials: 'Một bông hoa hoặc cây nhỏ', instructions: 'Cùng bé nhìn màu sắc, cánh hoa và nơi cây đang mọc.', note: 'Để bé tự quan sát trước khi người lớn gợi ý.' }, { title: 'Vẽ khu vườn nhỏ', materials: 'Giấy và bút màu', instructions: 'Mời bé vẽ nơi chú bướm muốn ghé thăm.', note: 'Không cần vẽ đúng mẫu.' }, { title: 'Tìm màu trong vườn', materials: 'Không cần vật liệu', instructions: 'Cùng bé tìm ba màu con thấy quanh mình.', note: 'Luôn có người lớn đồng hành.' }] },
  { id: 'sky', title: 'Bầu trời kỳ diệu', meta: '2 hoạt động · Chủ đề khám phá', color: 'sky', visibility: 'Công khai', ageTarget: '4–7 tuổi', version: 'v2.0', description: 'Một giáo án khám phá bầu trời, mây và những hình dạng do bé tưởng tượng.', activities: [{ title: 'Nhìn mây kể chuyện', materials: 'Một khoảng trời thoáng', instructions: 'Cùng bé quan sát hình dạng mây và hỏi con thấy điều gì.', note: 'Chọn vị trí an toàn, có người lớn giám sát.' }, { title: 'Vẽ bầu trời hôm nay', materials: 'Giấy và bút màu', instructions: 'Mời bé vẽ bầu trời theo trí tưởng tượng.', note: 'Tôn trọng cách kể riêng của bé.' }] },
  { id: 'seed', title: 'Hành trình của hạt mầm', meta: '2 hoạt động · Chủ đề cây xanh', color: 'sage', visibility: 'Lời mời từ giáo viên', ageTarget: '4–7 tuổi', version: 'v1.0', description: 'Theo dõi hạt mầm lớn lên và kể lại hành trình bằng nét vẽ của bé.', activities: [{ title: 'Ươm một hạt mầm', materials: 'Hạt đậu, cốc và bông ẩm', instructions: 'Cùng bé đặt hạt lên bông ẩm và quan sát từng ngày.', note: 'Người lớn chuẩn bị vật liệu và giữ vệ sinh.' }, { title: 'Vẽ cây của con', materials: 'Giấy và bút màu', instructions: 'Mời bé vẽ cây khi lớn lên theo trí tưởng tượng.', note: 'Không cần giống mẫu.' }] },
];

const initialLessonInvitations: LessonInvitation[] = [{ id: 'lesson-invite-1', lessonId: 'seed', teacher: 'Cô Mai', school: 'Trường Mầm non Ánh Nắng', status: 'pending' }];
const initialGroupInvitations: GroupInvitation[] = [{ id: 'group-invite-1', name: 'Lớp Lá 1', school: 'Trường Mầm non Ánh Nắng', status: 'pending' }];
const quickSessionTags = ['Bé rất thích', 'Dễ thực hiện', 'Hình ảnh sinh động', 'Âm thanh rõ'];
const profileContextFields: { key: ProfileContextField; label: string }[] = [
  { key: 'interests', label: 'Sở thích' },
  { key: 'observations', label: 'Quan sát của ba mẹ' },
  { key: 'achievements', label: 'Điều bé đã làm được' },
  { key: 'externalExperiences', label: 'Trải nghiệm ngoài ứng dụng' },
];

const initialStories: Story[] = [
  { id: 1, title: 'Chú bướm tìm nắng', date: 'Hôm qua', childId: 'an', child: 'Bé An', color: 'sun', subtitle: 'Một chuyến đi qua khu vườn', status: 'completed', lessonId: 'garden' },
  { id: 2, title: 'Con thuyền giấy nhỏ', date: '6 tuần trước', dateDaysAgo: 42, childId: 'minh', child: 'Bé Minh', color: 'sea', subtitle: 'Hành trình trên dòng suối', status: 'completed', lessonId: null },
];

const initialLessonDeliveries: LessonDelivery[] = [
  { id: 'delivery-1', lessonId: 'garden', title: 'Khám phá khu vườn', childId: 'an', child: 'Bé An', date: '3 ngày trước', school: 'Trường Mầm non Ánh Nắng', teacher: 'Cô Mai', teacherReply: 'Cảm ơn gia đình đã chia sẻ. Buổi học tuần này bé rất hào hứng với chủ đề khu vườn.' },
  { id: 'delivery-2', lessonId: 'sky', title: 'Bầu trời kỳ diệu', childId: 'minh', child: 'Bé Minh', date: 'Tuần trước', school: 'Trường Mầm non Ánh Nắng', teacher: 'Cô Lan' },
];

const initialNotifications: AppNotice[] = [
  { id: 'notice-1', title: 'Mẫu: câu chuyện đã sẵn sàng', body: 'Nội dung và trạng thái chỉ minh họa cho giao diện; chưa có video thật.', date: 'Hôm qua', read: false, kind: 'story' },
  { id: 'notice-2', title: 'Cô Mai đã phản hồi giáo án', body: 'Có phản hồi mới trong giáo án “Khám phá khu vườn”.', date: '3 ngày trước', read: false, kind: 'feedback' },
  { id: 'notice-3', title: 'Lời nhắc câu chuyện', body: 'Một câu chuyện đang chờ ba mẹ xem lại.', date: 'Tuần trước', read: true, kind: 'run' },
];

const initialShareGrants: ShareGrant[] = [
  { id: 'grant-1', childId: 'an', recipient: 'Cô Mai', organization: 'Trường Mầm non Ánh Nắng', status: 'active', date: 'Đã chấp nhận' },
  { id: 'grant-2', childId: 'minh', recipient: 'Cô Lan', organization: 'Trường Mầm non Ánh Nắng', status: 'invited', date: 'Đang chờ lời mời' },
];
const verifiedTeacherPreview: VerifiedTeacher[] = [
  { id: 'teacher-mai-preview', name: 'Cô Mai', school: 'Trường Mầm non Ánh Nắng' },
  { id: 'teacher-lan-preview', name: 'Cô Lan', school: 'Trường Mầm non Ánh Nắng' },
];

const initialRun: RunRecord | null = null;

const steps: { key: Step; label: string }[] = [
  { key: 'prepare', label: 'Chuẩn bị' },
  { key: 'guide', label: 'Gợi ý vẽ' },
  { key: 'capture', label: 'Chụp tranh' },
  { key: 'idea', label: 'Ý tưởng & ghi âm' },
  { key: 'review', label: 'Chủ thể & hướng kể' },
  { key: 'script', label: 'Kịch bản & hoạt động' },
  { key: 'generating', label: 'Tạo video' },
  { key: 'ready', label: 'Hoàn tất' },
];

const iconPaths: Record<IconName, React.ReactNode> = {
  home: <><path d="m3 10 9-7 9 7" /><path d="M5 9v11h14V9M9 20v-6h6v6" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  user: <><circle cx="12" cy="8" r="3.5" /><path d="M4.5 20c.7-3.1 3.3-5 7.5-5s6.8 1.9 7.5 5" /></>,
  spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" /><path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z" /></>,
  star: <path d="m12 2.8 2.9 6.1 6.7.9-4.9 4.7 1.2 6.7-5.9-3.2-5.9 3.2 1.2-6.7-4.9-4.7 6.7-.9z" />,
  expand: <><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5" /><path d="m3 3 6 6m12-6-6 6M3 21l6-6m12 6-6-6" /></>,
  arrow: <><path d="M4 12h15" /><path d="m13 5 7 7-7 7" /></>,
  back: <><path d="m15 18-6-6 6-6" /></>,
  camera: <><path d="M4 7h3l1.5-2h7L17 7h3v12H4z" /><circle cx="12" cy="13" r="3.5" /></>,
  upload: <><path d="M12 15V4m0 0L8 8m4-4 4 4" /><path d="M5 14v5h14v-5" /></>,
  book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21z" /><path d="M4 5.5v13A2.5 2.5 0 0 1 6.5 16H20" /></>,
  check: <path d="m5 12 4.5 4.5L19 7" />,
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 1 1 8 0v3m-4 4v3" /></>,
  play: <path d="m9 6 10 6-10 6z" />,
  mic: <><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5 11v1a7 7 0 0 0 14 0v-1m-7 8v3m-4 0h8" /></>,
  edit: <><path d="m4 16.5-.8 4.3 4.3-.8L19 8.5 15.5 5z" /><path d="m13.5 7 3.5 3.5" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  chevron: <path d="m9 18 6-6-6-6" />,
  settings: <><circle cx="12" cy="12" r="3" /><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.6.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.6-.9l-1.7.6-1.4-2.4 1.4-1.1a7 7 0 0 1 0-1.9L6.1 12l1.4-2.4 1.7.6a8 8 0 0 1 1.6-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.6.9l1.7-.6 1.4 2.4-1.4 1.1a7 7 0 0 1-.1 1.9Z" /></>,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  leaf: <><path d="M20 4c-8 0-14 3-14 9a6 6 0 0 0 6 6c6 0 8-7 8-15Z" /><path d="M4 21c2-5 5-8 10-11" /></>,
  trash: <><path d="M4 7h16M10 11v6m4-6v6M6 7l1 14h10l1-14M9 7V4h6v3" /></>,
  bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></>,
  search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></>,
  share: <><circle cx="18" cy="5" r="2.5" /><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="19" r="2.5" /><path d="m8.2 10.8 7.5-4.4M8.2 13.2l7.5 4.4" /></>,
  download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4" /><path d="M5 17v4h14v-4" /></>,
  message: <><path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.8 8.8 0 0 1-3.7-.8L4 20l1.2-3.4A7 7 0 0 1 4 12c0-4.1 3.6-7.5 8-7.5s8 3.1 8 7Z" /><path d="M8 12h.01M12 12h.01M16 12h.01" /></>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18m-13 4h2m3 0h2m-7 3h2" /></>,
  file: <><path d="M6 3h8l5 5v13H6z" /><path d="M14 3v6h5m-9 4h5m-5 4h5" /></>,
  logout: <><path d="M10 17 15 12l-5-5m5 5H3" /><path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7" /></>,
  refresh: <><path d="M20 7v5h-5M4 17v-5h5" /><path d="M5.8 9a7 7 0 0 1 11.6-2L20 12M4 12l2.6 5a7 7 0 0 0 11.6-2" /></>,
  mail: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m4 7 8 6 8-6" /></>,
  eye: <><path d="M2.5 12S6 6.5 12 6.5 21.5 12 21.5 12 18 17.5 12 17.5 2.5 12 2.5 12Z" /><circle cx="12" cy="12" r="2.5" /></>,
  eyeOff: <><path d="m3 3 18 18M9.9 6.8c.7-.2 1.4-.3 2.1-.3 6 0 9.5 5.5 9.5 5.5a14 14 0 0 1-3.1 3.3M6.1 8.1A14 14 0 0 0 2.5 12s3.5 5.5 9.5 5.5c1.2 0 2.2-.2 3.2-.6M10.5 10.5a2.5 2.5 0 0 0 3 3" /></>,
};

function Icon({ name, size = 20, className = '' }: { name: IconName; size?: number; className?: string }) {
  return <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{iconPaths[name]}</svg>;
}

function StoryArt({ variant = 'hero' }: { variant?: 'hero' | 'thumb' | 'capture' }) {
  const isThumb = variant === 'thumb';
  const artId = useId().replace(/:/g, '');
  return (
    <svg className={`story-art story-art--${variant}`} viewBox="0 0 300 220" role="img" aria-label="Minh họa bức tranh trẻ em với khu vườn và chú bướm">
      <defs>
        <linearGradient id={`storybook-sky-${artId}`} x1="24" y1="18" x2="272" y2="210" gradientUnits="userSpaceOnUse">
          <stop stopColor={isThumb ? '#EAF1DD' : '#FFF4CC'} />
          <stop offset="1" stopColor={isThumb ? '#D5E4C9' : '#F8E5A9'} />
        </linearGradient>
        <radialGradient id={`storybook-sun-${artId}`} cx="0" cy="0" r="1" gradientTransform="matrix(38 34 -34 38 221 64)" gradientUnits="userSpaceOnUse">
          <stop stopColor="#FFE897" stopOpacity=".9" />
          <stop offset="1" stopColor="#FFE897" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`storybook-hill-${artId}`} x1="52" y1="125" x2="241" y2="215" gradientUnits="userSpaceOnUse">
          <stop stopColor="#BDD69D" />
          <stop offset="1" stopColor="#88B47D" />
        </linearGradient>
      </defs>
      <path d="M31 190c-18-22-17-57 1-82 13-18 35-28 59-24 16-35 56-51 92-36 24 10 39 30 42 53 27 3 47 25 47 52 0 29-23 52-53 52H66c-14 0-27-5-35-15Z" fill={`url(#storybook-sky-${artId})`} />
      <circle cx="222" cy="61" r="43" fill={`url(#storybook-sun-${artId})`} />
      <circle cx="222" cy="61" r="16" fill="#F6CB63" opacity=".82" />
      <path d="M43 162c24-32 54-45 91-35 24 7 42 22 64 20 19-2 32-15 50-15 17 0 30 8 40 22v57H49c-10-14-13-32-6-49Z" fill="#D7E5B7" opacity=".9" />
      <path d="M33 176c20-25 48-35 78-27 28 7 41 25 70 24 24-1 39-17 65-15 18 1 31 11 43 24v29H37c-9-9-11-22-4-35Z" fill={`url(#storybook-hill-${artId})`} />
      <path d="M37 202c32-15 62-18 94-9 28 8 43 9 66 0 25-9 48-7 82 3v15H37v-9Z" fill="#6F9B69" opacity=".55" />
      <path d="M83 178c7-19 14-33 27-46m70 44c-3-17-1-30 5-43" fill="none" stroke="#527C51" strokeWidth="4" strokeLinecap="round" />
      <path d="M103 144c-13-7-21-2-20 8 1 8 10 12 19 8 8 5 17 0 17-9 0-9-9-13-16-7Z" fill="#F5C66D" stroke="#A87945" strokeWidth="2" />
      <path d="M183 137c-9-8-17-6-18 2-1 7 6 11 14 9 7 4 14 0 13-7 0-7-5-10-9-4Z" fill="#F0A88E" stroke="#B97861" strokeWidth="2" />
      <path d="M153 90c-18-12-31-3-25 11 4 9 16 11 26 5 11 7 23 2 23-8 0-11-13-16-24-8Z" fill="#FFF0C1" stroke="#A47C44" strokeWidth="2" />
      <path d="M153 91v20m-7-24-4-8m18 8 5-8" fill="none" stroke="#806543" strokeWidth="2" strokeLinecap="round" />
      <circle cx="147" cy="98" r="1.5" fill="#544635" /><circle cx="160" cy="98" r="1.5" fill="#544635" />
      <path d="M150 104q4 4 8 0" fill="none" stroke="#544635" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M59 117c6-8 14-9 21-1m118-56c5-7 12-8 18-1m-22 96c1-12 8-18 17-18" fill="none" stroke="#B78C4A" strokeWidth="2.5" strokeLinecap="round" opacity=".8" />
      <path d="m68 68 3 7 7 1-6 4 1 7-5-5-7 2 4-6-3-6 6 3Z" fill="#E8BC5B" />
      <path d="m246 98 2.5 5 5.5 1-4 4 .8 5.5-4.8-2.8-5 2.8 1.1-5.4-4-4 5.5-.7Z" fill="#D89073" />
      <path d="M54 191c8-6 16-5 22 1m171-3c9-7 18-7 26-1" fill="none" stroke="#436B4D" strokeWidth="3" strokeLinecap="round" opacity=".72" />
    </svg>
  );
}

function SeaStoryArt() {
  return <svg className="story-art story-art--thumb" viewBox="0 0 300 220" role="img" aria-label="Minh họa con thuyền giấy nhỏ trên dòng suối">
    <defs><linearGradient id="sea-art-sky" x1="0" y1="0" x2="0" y2="220" gradientUnits="userSpaceOnUse"><stop stopColor="#BBDDE8"/><stop offset="1" stopColor="#E9F2E2"/></linearGradient></defs>
    <rect width="300" height="220" rx="28" fill="url(#sea-art-sky)"/>
    <circle cx="245" cy="45" r="19" fill="#F7D484"/>
    <path d="M0 132c45-38 83-43 120-21 49-35 89-29 124-4 18-13 37-16 56-7v120H0z" fill="#8DBD9C"/>
    <path d="M0 163c49-17 82-7 123 9 56-16 111-16 177-7v55H0z" fill="#4F977F"/>
    <path d="M0 187c45-13 82-12 125-4 55-17 107-13 175-3v40H0z" fill="#78B9C7"/>
    <path d="M87 167h116l-20 32H109z" fill="#F6E1B2" stroke="#B68D63" strokeWidth="3"/>
    <path d="M145 167V90l53 75z" fill="#FFFBEC" stroke="#B68D63" strokeWidth="3"/><path d="M144 167V106l-45 59z" fill="#F6EACD" stroke="#B68D63" strokeWidth="3"/>
    <path d="M50 203c19-8 34-8 51 0m110-2c14-6 29-7 45-2" fill="none" stroke="#E6F5E7" strokeWidth="4" strokeLinecap="round"/>
  </svg>;
}

function SkyLessonArt() {
  return <svg className="lesson-art" viewBox="0 0 160 130" role="img" aria-label="Mây, mặt trời và chiếc máy bay giấy trên bầu trời">
    <defs><linearGradient id="sky-lesson-bg" x1="0" y1="0" x2="160" y2="130" gradientUnits="userSpaceOnUse"><stop stopColor="#8DC7DC"/><stop offset="1" stopColor="#DBEEDA"/></linearGradient></defs>
    <rect width="160" height="130" rx="22" fill="url(#sky-lesson-bg)"/>
    <circle cx="120" cy="33" r="17" fill="#F6D47D"/>
    <path d="M5 57c6-9 18-11 25-5 5-13 25-15 33-3 12-5 25 2 26 13H5zm80 32c6-10 19-12 27-5 6-14 25-16 33-4 11-4 22 2 22 12H85z" fill="#FFFDF0" opacity=".89"/>
    <path d="m39 91 71-39-21 56-12-21z" fill="#FFFAE9" stroke="#518D89" strokeWidth="2" strokeLinejoin="round"/><path d="m39 91 38-4 33-35" fill="none" stroke="#8EBAAA" strokeWidth="2"/>
    <path d="M19 110c17-5 26-4 37 0m49 3c16-6 24-6 40-2" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity=".8"/>
  </svg>;
}

function WonderWorldArt() {
  const artId = useId().replace(/:/g, '');
  return <svg className="wonder-world-art" viewBox="0 0 390 420" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Cuốn truyện mở ra, bướm và khu vườn bước ra từ nét vẽ của bé">
    <defs>
      <linearGradient id={`world-sky-${artId}`} x1="195" y1="0" x2="195" y2="375" gradientUnits="userSpaceOnUse"><stop stopColor="#A9D9EB"/><stop offset=".55" stopColor="#D9EEF0"/><stop offset="1" stopColor="#F8E7B7"/></linearGradient>
      <linearGradient id={`world-hill-${artId}`} x1="70" y1="205" x2="315" y2="345" gradientUnits="userSpaceOnUse"><stop stopColor="#A2C890"/><stop offset="1" stopColor="#5C9768"/></linearGradient>
      <linearGradient id={`world-page-${artId}`} x1="110" y1="270" x2="330" y2="375" gradientUnits="userSpaceOnUse"><stop stopColor="#FFFCF0"/><stop offset="1" stopColor="#F4E7CA"/></linearGradient>
      <linearGradient id={`world-orange-${artId}`} x1="248" y1="181" x2="297" y2="232" gradientUnits="userSpaceOnUse"><stop stopColor="#FFD776"/><stop offset="1" stopColor="#E9916F"/></linearGradient>
      <filter id={`world-shadow-${artId}`} x="-30%" y="-50%" width="160%" height="220%"><feGaussianBlur stdDeviation="10"/></filter>
    </defs>
    <g className="world-cloud world-cloud--left" fill="#fff" opacity=".76"><path d="M-22 154c10-17 29-19 43-10 7-22 34-29 50-10 17-10 37-1 39 17 13 4 18 18 10 30H-22z"/></g>
    <g className="world-cloud world-cloud--right" fill="#fff" opacity=".7"><path d="M274 100c8-14 22-17 34-10 6-17 27-21 38-7 16-8 32 1 33 16 12 3 17 14 11 25H274z"/></g>
    <g className="world-sun"><circle cx="321" cy="155" r="44" fill="#F9D977" opacity=".25"/><circle cx="321" cy="155" r="28" fill="#F9D570"/><circle cx="315" cy="148" r="9" fill="#FFE9A5" opacity=".63"/></g>
    <path d="M0 286c63-48 109-56 160-31 48-46 96-49 144-16 32-18 58-21 86-12v193H0z" fill="#C7DFB3"/>
    <path d="M0 313c57-29 103-20 145 6 38-31 101-43 147-16 37-25 69-29 98-20v137H0z" fill={`url(#world-hill-${artId})`}/>
    <path d="M0 343c55-13 91-11 131 2 49-19 103-14 153 9 41-13 77-12 106-4v70H0z" fill="#487F5C" opacity=".52"/>
    <g fill="#427F5D"><path d="M9 300h7v54H9zM371 299h6v55h-6z"/><circle cx="11" cy="291" r="22"/><circle cx="37" cy="295" r="17"/><circle cx="367" cy="292" r="22"/><circle cx="390" cy="300" r="18"/></g>
    <g fill="#68A975"><circle cx="4" cy="278" r="19"/><circle cx="29" cy="282" r="18"/><circle cx="382" cy="278" r="23"/></g>
    <path d="M0 372c73-6 142-4 205 13 72-18 129-13 185-4v39H0z" fill="#A9BA85"/>
    <ellipse cx="198" cy="374" rx="175" ry="31" fill="#244D46" opacity=".18" filter={`url(#world-shadow-${artId})`}/>
    <path d="M20 340q84-51 169-7 86-44 181-1l-11 52q-88-15-170 28-81-41-158-30z" fill="#486F5D"/>
    <path d="M27 334q78-53 161-7 88-48 173-2l-6 53q-81-12-166 26-80-39-154-27z" fill="#E5CF9C"/>
    <path d="M31 325q74-42 156 2v68q-78-35-150-26z" fill={`url(#world-page-${artId})`} stroke="#EADDBB" strokeWidth="2"/>
    <path d="M187 327q83-47 169-10l-2 50q-84-7-167 28z" fill="#FFF9E6" stroke="#EADDBB" strokeWidth="2"/>
    <path d="M188 327v68" stroke="#B9A77E" strokeWidth="4" strokeLinecap="round"/>
    <path d="M45 360q69-2 132 26m24-1q67-30 140-25" stroke="#E2D4B5" strokeWidth="2" fill="none"/>
    <g className="world-paper-sketch" fill="none" stroke="#8A9B7F" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M79 348c6-16 21-19 30-7m2 15c7-14 20-15 29-5m98-14c10-16 22-18 33-8m8 20c8-14 22-13 30-1"/><path d="M121 317c-16-16-31-7-24 6 5 10 18 8 25 0 8 10 20 7 21-2 1-10-11-17-22-4Z"/></g>
    <g className="world-life">
      <path d="M119 338c-10-32-8-55 3-78" fill="none" stroke="#3F8055" strokeWidth="5" strokeLinecap="round"/>
      <path d="M119 313c-30-5-38-28-21-32 15 0 23 13 21 32Zm2-16c0-21 14-31 27-25 1 14-10 22-27 25Z" fill="#5CA570"/>
      <path d="M245 336c3-36 21-61 50-80" fill="none" stroke="#3F8055" strokeWidth="5" strokeLinecap="round"/>
      <path d="M263 298c-19-11-19-29-6-34 14 4 17 17 6 34Zm11-16c5-19 24-24 32-13-6 13-18 17-32 13Z" fill="#67A878"/>
      <g className="world-flower"><path d="M294 274c5-20 7-35 4-49" fill="none" stroke="#41815A" strokeWidth="4" strokeLinecap="round"/><circle cx="298" cy="218" r="11" fill="#F7B56E"/><circle cx="286" cy="220" r="11" fill="#F5C87B"/><circle cx="301" cy="204" r="11" fill="#F7B56E"/><circle cx="312" cy="216" r="11" fill="#F5C87B"/><circle cx="299" cy="217" r="8" fill="#A96245"/></g>
      <g className="world-flower world-flower--small"><path d="M84 344c0-24-3-39-11-50" fill="none" stroke="#46815B" strokeWidth="3"/><circle cx="71" cy="290" r="9" fill="#F7D48B"/><circle cx="62" cy="295" r="8" fill="#F3A990"/><circle cx="80" cy="297" r="8" fill="#F3A990"/><circle cx="71" cy="295" r="5" fill="#B76E4D"/></g>
      <g className="world-butterfly"><path d="M221 219c-18-24-38-24-41-7-2 14 12 23 30 19-11 13-4 26 9 23 11-3 14-15 8-28Z" fill={`url(#world-orange-${artId})`} stroke="#B87454" strokeWidth="2"/><path d="M229 218c16-25 38-26 42-11 3 14-9 24-28 24 12 12 7 25-6 24-11-1-15-12-10-28Z" fill="#F7CD78" stroke="#B87454" strokeWidth="2"/><path d="M225 215c-5 16-5 30 0 40" fill="none" stroke="#3F5750" strokeWidth="5" strokeLinecap="round"/><circle cx="225" cy="210" r="5" fill="#3F5750"/><path d="M222 206c-7-10-12-11-16-9m22 8c7-10 13-10 17-8" fill="none" stroke="#3F5750" strokeWidth="2" strokeLinecap="round"/><circle cx="196" cy="216" r="5" fill="#FFE8B1" opacity=".75"/><circle cx="255" cy="214" r="5" fill="#FFE8B1" opacity=".75"/></g>
      <path d="M190 271c9-8 16-12 24-11m-42 25c6-4 11-5 16-3" stroke="#FCF7DF" strokeWidth="3" strokeLinecap="round" strokeDasharray="2 8" fill="none"/>
      <g fill="#FFE2A2"><path d="m341 257 2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/><path d="m171 241 2 4 4 2-4 2-2 4-2-4-4-2 4-2z"/></g>
    </g>
    <g transform="rotate(-22 48 324)"><rect x="31" y="295" width="18" height="72" rx="6" fill="#E5886E" stroke="#A85C50" strokeWidth="2"/><path d="M31 301h18m-18 52h18" stroke="#F9DCC3" strokeWidth="3"/><path d="m31 367 9 16 9-16" fill="#EEC694"/><path d="m37 378 3 5 3-5" fill="#3F4C47"/></g>
  </svg>;
}

function StreamWorldArt() {
  const id = useId().replace(/:/g, '');
  return <svg className="wonder-world-art" viewBox="0 0 390 420" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Dòng suối xanh, chiếc thuyền giấy và cuốn truyện mở">
    <defs>
      <linearGradient id={`stream-sky-${id}`} x2="0" y2="1"><stop stopColor="#A9DCEC"/><stop offset="1" stopColor="#EAF3DE"/></linearGradient>
      <linearGradient id={`stream-water-${id}`} x2="1" y2="1"><stop stopColor="#B7E3D7"/><stop offset="1" stopColor="#5EA9B0"/></linearGradient>
      <filter id={`stream-shadow-${id}`} x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="8"/></filter>
    </defs>
    <rect width="390" height="420" fill={`url(#stream-sky-${id})`}/>
    <g className="scene-cloud scene-cloud--one" fill="#fff" opacity=".84"><path d="M-20 119q18-25 44-14 13-29 43-21 22 5 26 28 21-7 33 12 10 18-3 28H-20Z"/></g>
    <g className="scene-cloud scene-cloud--two" fill="#fff" opacity=".72"><path d="M257 77q11-18 30-11 10-23 32-15 14 5 18 21 24-8 38 8 9 11 4 22H257Z"/></g>
    <circle className="scene-sun" cx="319" cy="165" r="44" fill="#FFE6A4" opacity=".49"/><circle className="scene-sun" cx="319" cy="165" r="25" fill="#F9D378"/>
    <path d="M0 263q75-43 152-12 56-44 122-12 63-32 116-11v192H0Z" fill="#C9DFAF"/>
    <path d="M0 305q68-34 132-12 65-30 127-4 69-28 131-9v140H0Z" fill="#83B894"/>
    <path d="M0 343q70-31 141-11 80-22 142 7 62-25 107-8v89H0Z" fill="#4D9479"/>
    <g className="scene-life">
      <path d="M146 279q-33 33-14 56 20 19 70 2 48-17 91 8 19 14 63 12l34 63H58q55-50 88-141Z" fill={`url(#stream-water-${id})`}/>
      <path d="M146 279q-33 33-14 56 20 19 70 2 48-17 91 8 19 14 63 12" fill="none" stroke="#DDF3E9" strokeWidth="5" opacity=".68"/>
      <g className="scene-boat"><ellipse cx="215" cy="347" rx="68" ry="10" fill="#2A716F" opacity=".2"/><path d="M167 324h92l-15 24h-62z" fill="#FFF7DF" stroke="#B5906B" strokeWidth="3"/><path d="M208 323V207l45 116z" fill="#FFFDF1" stroke="#B5906B" strokeWidth="3"/><path d="M207 323V222l-32 101z" fill="#F2DFC2" stroke="#B5906B" strokeWidth="3"/><path d="M198 299q8 5 17 0" fill="none" stroke="#79B3A2" strokeWidth="2"/></g>
      <g fill="#F5D378"><circle cx="48" cy="286" r="8"/><circle cx="60" cy="295" r="7"/><circle cx="35" cy="298" r="7"/><circle cx="319" cy="305" r="8"/><circle cx="331" cy="316" r="7"/></g>
      <path d="M49 310v44m272-31v35M43 336q-14-10-17-25m28 12q13-8 18-24m247 35q-12-13-14-29m18 14q13-8 20-23" fill="none" stroke="#346F5A" strokeWidth="4" strokeLinecap="round"/>
      <path d="M128 364q20-8 39 0m76 16q24-9 44-1" fill="none" stroke="#EBFAEE" strokeWidth="4" strokeLinecap="round" opacity=".75"/>
    </g>
    <g className="scene-sketch" fill="none" stroke="#537F78" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M151 296q-22 43-2 46 20 5 52-9 50-17 85 9"/><path d="m167 324 91 1-16 24-59-1-16-24Zm41 0V207l45 116-45-101-32 101"/></g>
    <ellipse cx="199" cy="393" rx="145" ry="19" fill="#234D49" opacity=".16" filter={`url(#stream-shadow-${id})`}/>
  </svg>;
}

function SkyWorldArt() {
  const id = useId().replace(/:/g, '');
  return <svg className="wonder-world-art" viewBox="0 0 390 420" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Bầu trời xanh với mây, máy bay giấy và cuốn truyện mở">
    <defs><linearGradient id={`sky-world-${id}`} x2="0" y2="1"><stop stopColor="#92CEE8"/><stop offset=".7" stopColor="#E0F1EA"/><stop offset="1" stopColor="#FAE9BF"/></linearGradient><linearGradient id={`sky-hill-${id}`} x2="1" y2="1"><stop stopColor="#B7D49E"/><stop offset="1" stopColor="#6BA681"/></linearGradient></defs>
    <rect width="390" height="420" fill={`url(#sky-world-${id})`}/>
    <circle className="scene-sun" cx="318" cy="143" r="48" fill="#FFE6A6" opacity=".46"/><circle className="scene-sun" cx="318" cy="143" r="28" fill="#F9D274"/>
    <g className="scene-cloud scene-cloud--one" fill="#fff" opacity=".84"><path d="M-15 161q13-21 35-15 10-27 35-23 23 2 29 26 25-7 38 11 10 15 2 27H-15Z"/></g>
    <g className="scene-cloud scene-cloud--two" fill="#fff" opacity=".9"><path d="M243 81q12-18 32-13 12-26 38-20 19 4 22 25 20-6 33 10 10 12 5 24H243Z"/></g>
    <path d="M0 299q68-56 145-22 69-57 132-21 53-29 113-15v179H0Z" fill="#D9E7BF"/>
    <path d="M0 330q75-43 136-21 68-33 127-8 57-25 127-10v129H0Z" fill={`url(#sky-hill-${id})`}/>
    <path d="M0 368q64-23 142-5 64-16 117 6 70-18 131-5v56H0Z" fill="#4C8F70" opacity=".58"/>
    <g className="scene-life">
      <g className="scene-plane"><path d="m101 271 180-104-45 142-39-52-96 14Z" fill="#FFFDF0" stroke="#729D93" strokeWidth="3" strokeLinejoin="round"/><path d="m101 271 96-14 84-90-59 105" fill="none" stroke="#B6CDC0" strokeWidth="3" strokeLinejoin="round"/><path d="m197 257 20 40 19 12" fill="#E9D9B5" stroke="#729D93" strokeWidth="3"/></g>
      <path d="M47 278q20-20 37-14m226 26q24-11 37-2" fill="none" stroke="#FFF9DD" strokeWidth="4" strokeLinecap="round" strokeDasharray="1 10"/>
      <g fill="#FFE2A0"><path d="m72 211 3 8 8 3-8 3-3 8-3-8-8-3 8-3zM311 232l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/></g>
    </g>
    <g className="scene-sketch" fill="none" stroke="#628579" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m101 271 180-104-45 142-39-52-96 14 96-14 84-90"/><path d="M68 227q20-18 42-3m153 3q14-14 31-6"/></g>
    <path d="M23 383q74-47 166-12 85-46 180-5l-15 51q-81-17-165 22-88-36-155-23Z" fill="#406D5F"/>
    <path d="M29 376q76-44 158-6v57q-83-29-151-19Zm158-6q86-44 175-4l-7 42q-86-16-168 19Z" fill="#FFF9E8" stroke="#E4D8B5" strokeWidth="3"/>
    <path d="M187 370v56" stroke="#C6B58E" strokeWidth="4"/>
  </svg>;
}

function LoginSceneArt() {
  const sceneId = useId().replace(/:/g, '');
  return <svg className="login-scene-art" viewBox="0 0 390 330" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Khu vườn cổ tích với ngôi nhà kể chuyện, cuốn sách và chú bướm">
    <defs>
      <linearGradient id={`login-sky-${sceneId}`} x1="195" y1="0" x2="195" y2="290" gradientUnits="userSpaceOnUse"><stop stopColor="#8DCDE9"/><stop offset=".68" stopColor="#CFEDF0"/><stop offset="1" stopColor="#EDF2D7"/></linearGradient>
      <linearGradient id={`login-hill-${sceneId}`} x1="85" y1="160" x2="309" y2="314" gradientUnits="userSpaceOnUse"><stop stopColor="#B0D38D"/><stop offset="1" stopColor="#5EA270"/></linearGradient>
      <linearGradient id={`login-roof-${sceneId}`} x1="159" y1="166" x2="249" y2="209" gradientUnits="userSpaceOnUse"><stop stopColor="#DC8B6A"/><stop offset="1" stopColor="#A95549"/></linearGradient>
      <linearGradient id={`login-page-${sceneId}`} x1="208" y1="258" x2="341" y2="326" gradientUnits="userSpaceOnUse"><stop stopColor="#FFFDF2"/><stop offset="1" stopColor="#EAD9B5"/></linearGradient>
    </defs>
    <path d="M0 0h390v330H0z" fill={`url(#login-sky-${sceneId})`}/>
    <g className="login-scene__cloud login-scene__cloud--one" fill="#fff" opacity=".77"><path d="M-25 75c12-18 35-20 49-9 8-23 38-27 55-7 18-7 35 4 35 21 13 4 20 16 13 28H-25z"/></g>
    <g className="login-scene__cloud login-scene__cloud--two" fill="#fff" opacity=".73"><path d="M283 52c8-12 24-15 35-7 7-18 31-19 41-4 17-7 33 3 32 19 12 4 17 15 9 25H283z"/></g>
    <g className="login-scene__sun"><circle cx="310" cy="96" r="38" fill="#FFE4A2" opacity=".42"/><circle cx="310" cy="96" r="25" fill="#FFD66D"/><path d="M310 56v-8m0 96v-8m-40-40h-8m96 0h-8m-68-28-6-6m68 68-6-6m0-52 6-6m-68 68 6-6" stroke="#FFD980" strokeWidth="3" strokeLinecap="round"/></g>
    <g className="login-scene__land">
      <path d="M0 187c55-34 89-34 143-7 42-34 89-37 137-5 43-24 74-23 110-7v162H0z" fill="#C8DFAE"/>
      <path d="M0 218c57-28 103-26 145 0 53-37 100-40 152-11 36-21 65-20 93-9v132H0z" fill={`url(#login-hill-${sceneId})`}/>
      <path d="M0 256c55-19 109-15 159 4 55-23 103-23 151-2 35-16 58-17 80-10v82H0z" fill="#5A986B"/>
      <path d="M0 296c68-24 123-18 181 4 62-24 129-21 209-5v35H0z" fill="#397C62"/>
    </g>
    <g className="login-scene__trees"><path d="M34 250v-52m306 52v-60m-294 45v-35" stroke="#567851" strokeWidth="7" strokeLinecap="round"/><circle cx="34" cy="190" r="24" fill="#67A875"/><circle cx="15" cy="206" r="17" fill="#4A9268"/><circle cx="50" cy="203" r="18" fill="#4F9B6E"/><circle cx="341" cy="182" r="25" fill="#5A9F6D"/><circle cx="361" cy="198" r="20" fill="#4A8E65"/><circle cx="49" cy="192" r="12" fill="#81B97F"/></g>
    <g className="login-scene__house"><path d="M158 202 208 161l52 41v55H158z" fill="#F9E3BC" stroke="#B7835B" strokeWidth="3"/><path d="m150 207 58-51 59 51-9 12-50-42-49 43z" fill={`url(#login-roof-${sceneId})`} stroke="#985447" strokeWidth="3" strokeLinejoin="round"/><rect x="193" y="215" width="29" height="42" rx="12" fill="#9B6550"/><circle cx="216" cy="236" r="2" fill="#F7D081"/><rect x="166" y="214" width="20" height="21" rx="5" fill="#A5D8D9" stroke="#F9F2D9" strokeWidth="4"/><rect x="233" y="214" width="19" height="21" rx="5" fill="#A5D8D9" stroke="#F9F2D9" strokeWidth="4"/><path d="M207 192c-7-10-17-7-17 1 0 9 10 11 17 5 7 6 18 4 18-5 0-8-10-11-18-1Z" fill="#FFF3CB" stroke="#B5805A" strokeWidth="2"/></g>
    <g className="login-scene__butterfly"><path d="M284 166c-12-17-28-17-28-5 0 10 10 15 22 12-7 9-2 18 7 16 8-2 10-11 6-20Z" fill="#F6B774" stroke="#9F7654" strokeWidth="2"/><path d="M291 166c12-18 27-18 29-7 2 10-7 16-19 15 7 8 4 18-5 17-8-1-11-9-7-20Z" fill="#F6D27F" stroke="#9F7654" strokeWidth="2"/><path d="M288 163c-3 10-3 20 0 28" fill="none" stroke="#345A4F" strokeWidth="4" strokeLinecap="round"/></g>
    <g className="login-scene__book"><ellipse cx="241" cy="310" rx="137" ry="18" fill="#215D4E" opacity=".15"/><path d="M114 290q62-39 128-6 58-34 128-4l-8 44q-61-15-121 7-65-24-117-8Z" fill="#47735E"/><path d="M120 282q60-32 120 1v43q-61-22-115-7z" fill="#FFF9E9" stroke="#E7D9B7" strokeWidth="3"/><path d="M240 283q62-35 125-7l-3 42q-59-8-122 8z" fill={`url(#login-page-${sceneId})`} stroke="#E7D9B7" strokeWidth="3"/><path d="M240 283v42" stroke="#C5B18B" strokeWidth="4"/><path d="m145 299 22-9 22 11 20-7m58 6 23-13 22 10 19-7" fill="none" stroke="#91B18A" strokeWidth="3" strokeLinecap="round"/><circle cx="167" cy="289" r="5" fill="#F2CD75"/><circle cx="290" cy="287" r="5" fill="#F2CD75"/></g>
    <g className="login-scene__foreground"><path d="M15 303c3-16 6-32 7-48m48 52c-2-19 2-38 9-52m286 52c1-20 2-33 7-44" stroke="#306C50" strokeWidth="5" strokeLinecap="round"/><path d="M21 274c-19-15-18-26-5-29 14 3 15 16 5 29Zm1-12c2-17 14-23 24-16-4 12-12 17-24 16Zm56 15c-16-13-13-25 0-26 12 4 12 16 0 26Zm1-17c5-15 18-18 26-10-8 11-17 14-26 10Z" fill="#418D61"/><circle cx="372" cy="264" r="9" fill="#F2B475"/><circle cx="363" cy="270" r="8" fill="#F6D184"/><circle cx="380" cy="272" r="8" fill="#F6D184"/><circle cx="372" cy="270" r="5" fill="#A4644C"/></g>
  </svg>;
}

function AuthScene({ onBack, backLabel, disabled = false }: { onBack: () => void; backLabel: string; disabled?: boolean }) {
  return <section className="auth-scene" aria-label="Thế giới truyện Sketch2Life">
    <LoginSceneArt />
    <div className="auth-scene__top">
      <button className="auth-back" type="button" onClick={onBack} disabled={disabled} aria-label={backLabel}><Icon name="back" size={22} /></button>
      <span className="auth-wordmark"><span className="auth-wordmark__leaf"><Icon name="leaf" size={18} /></span> Sketch<span>2</span>Life</span>
    </div>
  </section>;
}

function formatChildAge(ageMonths: number) {
  const years = Math.floor(ageMonths / 12);
  const months = ageMonths % 12;
  return months ? `${years} tuổi ${months} tháng` : `${years} tuổi`;
}

function formatChildGender(gender: Child['gender']) {
  return gender === 'girl' ? 'Bé gái' : gender === 'boy' ? 'Bé trai' : 'Chưa chọn giới tính';
}

function ChildAvatar({ child, size = 'md' }: { child: Child; size?: 'sm' | 'md' | 'lg' }) {
  return <span className={`child-avatar child-avatar--${child.tone} child-avatar--${size}`} aria-hidden="true">{child.photoUrl ? <img src={child.photoUrl} alt="" /> : <span>{child.initial}</span>}<i /></span>;
}

function isSubjectAlignedWithLesson(lessonId: string | null, currentSubject: string): boolean {
  if (!lessonId) return true;
  const normalized = currentSubject.toLocaleLowerCase('vi');
  if (lessonId === 'sky') return /trời|mây|mặt trời|sao/.test(normalized);
  if (lessonId === 'garden') return /bướm|hoa|vườn|cây/.test(normalized);
  if (lessonId === 'seed') return /cây|hạt|lá|hoa|vườn/.test(normalized);
  return true;
}

function SketchGuideIllustration({ topic, stepIndex, detailed }: { topic: string; stepIndex: number; detailed: boolean }) {
  const normalized = topic.toLocaleLowerCase('vi');
  const kind: 'sky' | 'ocean' | 'space' | 'garden' = normalized.includes('trời')
    ? 'sky'
    : normalized.includes('đại dương')
      ? 'ocean'
      : normalized.includes('vũ trụ')
        ? 'space'
        : 'garden';
  const ink = '#28543e';
  const guideStroke = '#3f7559';
  const warmAccent = '#d99a58';
  const gold = '#f5d279';
  const sage = '#8bb499';
  const mint = '#cbe0cf';
  const stepOneDash = stepIndex === 0 ? '7 5' : undefined;
  const stepTwoDash = stepIndex === 1 ? '6 5' : undefined;

  return <svg className={`sketch-preview-svg sketch-preview-svg--${kind}`} viewBox="0 0 360 196" role="img" aria-label={`Minh họa nét vẽ chủ đề ${topic}, bước ${stepIndex + 1} trên 3`}>
    <rect width="360" height="196" rx="14" fill={kind === 'sky' ? '#eaf4f6' : kind === 'ocean' ? '#e7f2ef' : kind === 'space' ? '#ebf0ea' : '#eef4e7'} />
    {kind === 'garden' && <>
      {stepIndex >= 1 && <path d="M16 168q88-46 176-10t152-8v46H16Z" fill={stepIndex >= 2 ? sage : 'none'} stroke={guideStroke} strokeWidth="2.5" strokeDasharray={stepTwoDash} />}
      <g>
        <circle cx="242" cy="84" r="14" fill={stepIndex >= 2 ? warmAccent : '#fff8e2'} stroke={ink} strokeWidth="2.5" strokeDasharray={stepOneDash} />
        {[0, 60, 120, 180, 240, 300].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          return <circle key={angle} cx={242 + Math.cos(rad) * 23} cy={84 + Math.sin(rad) * 23} r="10.5" fill={stepIndex >= 2 ? gold : 'none'} stroke={guideStroke} strokeWidth="2.2" strokeDasharray={stepOneDash} />;
        })}
        {stepIndex >= 1 && <path d="M242 117q-3 28 2 52m-18-33c10-6 14 2 16 10" fill="none" stroke={ink} strokeWidth="3" strokeLinecap="round" strokeDasharray={stepTwoDash} />}
      </g>
      {stepIndex >= 1 && <g>
        <path d="M126 78c-22-24-44-16-40 4 4 16 24 18 38 11m6-15c22-24 44-16 40 4-4 16-24 18-38 11" fill={stepIndex >= 2 ? gold : 'none'} stroke={ink} strokeWidth="2.4" strokeDasharray={stepTwoDash} strokeLinejoin="round" />
        <path d="M129 73v36" stroke={ink} strokeWidth="4" strokeLinecap="round" />
        {detailed && <circle cx="72" cy="40" r="16" fill={stepIndex >= 2 ? gold : 'none'} stroke={warmAccent} strokeWidth="2.2" strokeDasharray={stepTwoDash} />}
      </g>}
    </>}
    {kind === 'sky' && <>
      <g>
        <path d="M118 118h128c14 0 24-9 24-21 0-12-9-21-21-22-5-18-22-30-42-29-17 0-32 10-39 24-13-4-27 2-33 14-14 2-24 11-24 22 0 7 3 12 7 12Z" fill={stepIndex >= 2 ? '#fffef8' : 'none'} stroke={ink} strokeWidth="2.8" strokeDasharray={stepOneDash} strokeLinejoin="round" />
      </g>
      {stepIndex >= 1 && <g>
        <circle cx="292" cy="46" r="20" fill={stepIndex >= 2 ? gold : 'none'} stroke={warmAccent} strokeWidth="2.5" strokeDasharray={stepTwoDash} />
        <path d="m70 144 64-24-20 44-13-16-31-4Z" fill={stepIndex >= 2 ? mint : 'none'} stroke={ink} strokeWidth="2.4" strokeDasharray={stepTwoDash} strokeLinejoin="round" />
        <path d="M46 154c18 2 28-2 36-9" fill="none" stroke={guideStroke} strokeWidth="2.2" strokeDasharray="4 5" strokeLinecap="round" />
        {detailed && <path d="M62 56c10-9 18-9 26 0 7-9 17-9 25 0" fill="none" stroke={guideStroke} strokeWidth="2.2" strokeLinecap="round" />}
      </g>}
    </>}
    {kind === 'ocean' && <>
      <g>
        <path d="M104 98c0-25 34-40 76-40s68 18 76 40c-8 22-34 40-76 40s-76-15-76-40Z" fill={stepIndex >= 2 ? gold : 'none'} stroke={ink} strokeWidth="2.8" strokeDasharray={stepOneDash} />
        <path d="m252 98 38-26v52Z" fill={stepIndex >= 2 ? warmAccent : 'none'} stroke={ink} strokeWidth="2.5" strokeDasharray={stepOneDash} strokeLinejoin="round" />
        <circle cx="136" cy="90" r="4.5" fill={stepIndex >= 2 ? ink : 'none'} stroke={ink} strokeWidth="2" />
      </g>
      {stepIndex >= 1 && <g>
        <path d="M22 154q28-14 56 0t56 0 56 0 56 0 56 0 56 0" fill="none" stroke={guideStroke} strokeWidth="2.8" strokeDasharray={stepTwoDash} strokeLinecap="round" />
        <circle cx="84" cy="70" r="8" fill={stepIndex >= 2 ? '#fffefa' : 'none'} stroke={guideStroke} strokeWidth="2" strokeDasharray={stepTwoDash} />
        <circle cx="72" cy="48" r="5" fill={stepIndex >= 2 ? '#fffefa' : 'none'} stroke={guideStroke} strokeWidth="2" strokeDasharray={stepTwoDash} />
        {detailed && <path d="M298 176q-10-22 2-40m16 40q10-20-2-36" fill="none" stroke={sage} strokeWidth="3.2" strokeLinecap="round" />}
      </g>}
    </>}
    {kind === 'space' && <>
      <g>
        <circle cx="182" cy="98" r="40" fill={stepIndex >= 2 ? gold : 'none'} stroke={ink} strokeWidth="2.8" strokeDasharray={stepOneDash} />
        <ellipse cx="182" cy="100" rx="74" ry="18" transform="rotate(-16 182 100)" fill="none" stroke={warmAccent} strokeWidth="3" strokeDasharray={stepOneDash} />
      </g>
      {stepIndex >= 1 && <g>
        <path d="M68 42a22 22 0 1 0 22 30 16 16 0 0 1-22-30Z" fill={stepIndex >= 2 ? mint : 'none'} stroke={ink} strokeWidth="2.3" strokeDasharray={stepTwoDash} />
        <path d="m288 42 4 11 11 4-11 4-4 11-4-11-11-4 11-4Z" fill={stepIndex >= 2 ? warmAccent : 'none'} stroke={warmAccent} strokeWidth="2" strokeDasharray={stepTwoDash} />
        {detailed && <><circle cx="298" cy="144" r="10" fill={stepIndex >= 2 ? sage : 'none'} stroke={guideStroke} strokeWidth="2" strokeDasharray={stepTwoDash} /><circle cx="72" cy="148" r="3.5" fill={ink} /></>}
      </g>}
    </>}
  </svg>;
}

function App() {
  const [screen, setScreen] = useState<Screen>(() => {
    const preview = new URLSearchParams(window.location.search).get('preview');
    return preview === 'signup' ? 'signup' : preview === 'login' ? 'auth' : 'home';
  });
  const [step, setStep] = useState<Step>('prepare');
  const [guideEnabled, setGuideEnabled] = useState(false);
  const [profiles, setProfiles] = useState<Child[]>(children);
  const [selectedChildId, setSelectedChildId] = useState('an');
  const [detailChildId, setDetailChildId] = useState('an');
  const [lessonInvitations, setLessonInvitations] = useState(initialLessonInvitations);
  const [groupInvitations, setGroupInvitations] = useState(initialGroupInvitations);
  const [selectedLessonId, setSelectedLessonId] = useState<string | null>(null);
  const [lessonPreviewId, setLessonPreviewId] = useState<string | null>(null);
  const [libraryTab, setLibraryTab] = useState<'public' | 'shared'>('public');
  const [showLessonOptions, setShowLessonOptions] = useState(true);
  const [guideTopic, setGuideTopic] = useState('Khu vườn');
  const [guideStepIndex, setGuideStepIndex] = useState(0);
  const [guideDifficulty, setGuideDifficulty] = useState<'Nhẹ nhàng' | 'Thêm chi tiết'>('Nhẹ nhàng');
  const [subject, setSubject] = useState('Bướm');
  const [subjectCorrection, setSubjectCorrection] = useState('Bướm');
  const [idea, setIdea] = useState('');
  const [ideaMode, setIdeaMode] = useState<'initial' | 'rewrite'>('initial');
  const [rewriteSuggestion, setRewriteSuggestion] = useState('');
  const [scriptModifier, setScriptModifier] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioFileName, setAudioFileName] = useState('');
  const [transcriptionStatus, setTranscriptionStatus] = useState<'idle' | 'transcribing' | 'complete' | 'error'>('idle');
  const [recordingError, setRecordingError] = useState('');
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<BlobPart[]>([]);
  const recordingTimer = useRef<number | null>(null);
  const transcriptionTimer = useRef<number | null>(null);
  const flowContentRef = useRef<HTMLElement | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [photoName, setPhotoName] = useState('');
  const [stories, setStories] = useState(initialStories);
  const [activeRun, setActiveRun] = useState<RunRecord | null>(initialRun);
  const [selectedStoryId, setSelectedStoryId] = useState<number | null>(null);
  const [feedbackStoryId, setFeedbackStoryId] = useState<number | null>(null);
  const [sessionRating, setSessionRating] = useState(0);
  const [sessionTags, setSessionTags] = useState<string[]>([]);
  const [sessionNote, setSessionNote] = useState('');
  const [activityLessonId, setActivityLessonId] = useState<string | null>(null);
  const [activityOrigin, setActivityOrigin] = useState<'flow' | 'run-detail'>('flow');
  const [kidView, setKidView] = useState(false);
  const [deliveries, setDeliveries] = useState(initialLessonDeliveries);
  const [selectedDeliveryId, setSelectedDeliveryId] = useState('delivery-1');
  const [selectedLessonDetailId, setSelectedLessonDetailId] = useState('garden');
  const [lessonDetailOrigin, setLessonDetailOrigin] = useState<'library' | 'delivery'>('library');
  const [historyTab, setHistoryTab] = useState<HistoryTab>('stories');
  const [historyStatus, setHistoryStatus] = useState<HistoryStatus>('all');
  const [historyRange, setHistoryRange] = useState<30 | 60>(30);
  const [notices, setNotices] = useState<AppNotice[]>(initialNotifications);
  const [grants, setGrants] = useState(initialShareGrants);
  const [feedbackText, setFeedbackText] = useState('');
  const [shareChildId, setShareChildId] = useState('an');
  const [shareTeacherId, setShareTeacherId] = useState('');
  const [childEditingId, setChildEditingId] = useState<string | null>(null);
  const [childName, setChildName] = useState('');
  const [childAgeYears, setChildAgeYears] = useState('');
  const [childAgeMonths, setChildAgeMonths] = useState('0');
  const [childGender, setChildGender] = useState<Child['gender']>('unspecified');
  const [childNickname, setChildNickname] = useState('');
  const [childSupport, setChildSupport] = useState('');
  const [childInterests, setChildInterests] = useState('');
  const [childObservations, setChildObservations] = useState('');
  const [childAchievements, setChildAchievements] = useState('');
  const [childExperiences, setChildExperiences] = useState('');
  const [childPhotoUrl, setChildPhotoUrl] = useState<string | null>(null);
  const [presetForNextRun, setPresetForNextRun] = useState<string | null>(null);
  const [scriptFollowing, setScriptFollowing] = useState<'lesson' | 'free' | null>(null);
  const [selectedActivityId, setSelectedActivityId] = useState<string | null>(null);
  const [mismatchModalOpen, setMismatchModalOpen] = useState(false);
  const [mismatchDemoChoice, setMismatchDemoChoice] = useState<'lesson' | 'free'>('lesson');
  const [toast, setToast] = useState('');
  const [showAllSubjects, setShowAllSubjects] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [captionsEnabled, setCaptionsEnabled] = useState(true);
  const [playerExpanded, setPlayerExpanded] = useState(false);
  const [previewJobState, setPreviewJobState] = useState<PreviewJobState>('processing');
  const [previewJobStage, setPreviewJobStage] = useState(0);
  const [quotaTopupOpen, setQuotaTopupOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [pendingDelete, setPendingDelete] = useState<number | null>(null);
  const [pendingDeleteChildId, setPendingDeleteChildId] = useState<string | null>(null);
  const [pendingCancel, setPendingCancel] = useState(false);
  const [pendingRegenerate, setPendingRegenerate] = useState(false);
  const [pendingRevoke, setPendingRevoke] = useState<string | null>(null);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authRemember, setAuthRemember] = useState(true);
  const [authPasswordVisible, setAuthPasswordVisible] = useState(false);
  const [authEmailError, setAuthEmailError] = useState('');
  const [authPasswordError, setAuthPasswordError] = useState('');
  const [authPreviewNotice, setAuthPreviewNotice] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirm, setSignupConfirm] = useState('');
  const [signupPasswordVisible, setSignupPasswordVisible] = useState(false);
  const [signupConfirmVisible, setSignupConfirmVisible] = useState(false);
  const [signupErrors, setSignupErrors] = useState({ email: '', password: '', confirm: '' });
  const [signupNotice, setSignupNotice] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changePasswordVisible, setChangePasswordVisible] = useState(false);
  const [changePasswordError, setChangePasswordError] = useState('');
  const [changePasswordNotice, setChangePasswordNotice] = useState('');

  const selectedChild = profiles.find((child) => child.id === selectedChildId) ?? profiles[0] ?? children[0];
  const detailChild = profiles.find((child) => child.id === detailChildId) ?? selectedChild;
  const availableLessons = lessons.filter((lesson) => lesson.id !== 'seed' || lessonInvitations.some((invitation) => invitation.lessonId === lesson.id && invitation.status === 'accepted'));
  const selectedLesson = availableLessons.find((lesson) => lesson.id === selectedLessonId) ?? null;
  const lessonPreview = availableLessons.find((lesson) => lesson.id === lessonPreviewId) ?? null;
  const publicLessons = availableLessons.filter((lesson) => lesson.visibility === 'Công khai');
  const sharedLessons = availableLessons.filter((lesson) => lesson.visibility !== 'Công khai');
  const flowSteps = steps.filter((item) => !['generating', 'ready'].includes(item.key) && (item.key !== 'guide' || guideEnabled));
  const stepIndex = flowSteps.findIndex((item) => item.key === step);
  const currentStory = stories.find((story) => story.id === selectedStoryId) ?? null;
  const visibleStories = stories.filter((story) => !story.hidden && (historyRange === 60 || (story.dateDaysAgo ?? 0) <= 30) && (historyStatus === 'all' || (historyStatus === 'open' ? story.status === 'ready' || story.status === 'active' : story.status === 'completed')));
  const selectedDelivery = deliveries.find((delivery) => delivery.id === selectedDeliveryId) ?? deliveries[0];
  const selectedLessonDetail = availableLessons.find((lesson) => lesson.id === selectedLessonDetailId) ?? availableLessons[0];
  const authReady = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(authEmail.trim()) && authPassword.length > 0;
  const signupReady = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signupEmail.trim()) && signupPassword.length >= 6 && signupPassword.length <= 128 && signupConfirm === signupPassword;
  const subjectAligned = isSubjectAlignedWithLesson(selectedLessonId, subject);
  const topicObject = guideTopic.toLocaleLowerCase('vi').includes('trời') ? 'đám mây & máy bay giấy' : guideTopic.toLocaleLowerCase('vi').includes('đại dương') ? 'chú cá & sóng biển' : guideTopic.toLocaleLowerCase('vi').includes('vũ trụ') ? 'hành tinh có vành đai' : guideTopic.toLocaleLowerCase('vi').includes('vườn') ? 'bông hoa & chú bướm' : 'hình bé thích';
  const guideSteps = [
    { title: 'Bắt đầu bằng một hình lớn', detail: `Vẽ một ${topicObject} bằng hình tròn, bầu dục hoặc nét cong thật đơn giản.` },
    { title: 'Thêm nét gợi ý chủ đề', detail: guideDifficulty === 'Thêm chi tiết' ? `Thêm hai hoặc ba nét nhỏ để bức tranh gợi nhớ đến ${guideTopic.toLocaleLowerCase('vi')}.` : `Thêm một chi tiết mà bé thấy vui trong chủ đề ${guideTopic.toLocaleLowerCase('vi')}.` },
    { title: 'Chọn màu và kể theo cách riêng', detail: 'Bé tự chọn màu, có thể đổi ý hoặc bỏ qua gợi ý bất cứ lúc nào.' },
  ];
  const guideStep = guideSteps[guideStepIndex] ?? guideSteps[0];

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(''), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => () => {
    if (transcriptionTimer.current) window.clearTimeout(transcriptionTimer.current);
  }, []);

  useEffect(() => {
    if (screen !== 'flow' || step !== 'review' || !selectedLesson) return;
    if (!subjectAligned) {
      if (scriptFollowing === null) {
        setMismatchDemoChoice('lesson');
        setMismatchModalOpen(true);
      }
      return;
    }
    if (scriptFollowing === null) {
      setScriptFollowing('lesson');
      setActiveRun((run) => run ? { ...run, scriptFollowing: 'lesson' } : run);
    }
  }, [screen, step, selectedLessonId, subjectAligned, scriptFollowing]);

  useEffect(() => {
    if (screen === 'flow') flowContentRef.current?.scrollTo(0, 0);
  }, [screen, step, guideStepIndex]);

  useEffect(() => {
    const anyModalOpen = Boolean(playerExpanded || showSettings || lessonPreviewId || mismatchModalOpen || recordingError || pendingDelete !== null || pendingDeleteChildId || pendingCancel || pendingRegenerate || pendingRevoke);
    if (!anyModalOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      if (playerExpanded) setPlayerExpanded(false);
      else if (recordingError) setRecordingError('');
      else if (mismatchModalOpen) setMismatchModalOpen(false);
      else if (lessonPreviewId) setLessonPreviewId(null);
      else if (pendingDelete !== null) setPendingDelete(null);
      else if (pendingDeleteChildId) setPendingDeleteChildId(null);
      else if (pendingCancel) setPendingCancel(false);
      else if (pendingRegenerate) setPendingRegenerate(false);
      else if (pendingRevoke) setPendingRevoke(null);
      else if (showSettings) setShowSettings(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [playerExpanded, showSettings, lessonPreviewId, mismatchModalOpen, recordingError, pendingDelete, pendingDeleteChildId, pendingCancel, pendingRegenerate, pendingRevoke]);

  useEffect(() => {
    if (screen !== 'flow' && screen !== 'run-detail') setPlayerExpanded(false);
  }, [screen]);

  useEffect(() => () => {
    if (recordingTimer.current) window.clearTimeout(recordingTimer.current);
    if (mediaRecorder.current?.state === 'recording') mediaRecorder.current.stop();
  }, []);

  const startStory = () => {
    if (!profiles.length) { setScreen('profile'); setToast('Thêm hồ sơ trẻ trước khi bắt đầu câu chuyện.'); return; }
    if (activeRun) {
      setStep(activeRun.step);
      setSelectedChildId(activeRun.childId);
      setSelectedLessonId(activeRun.lessonId);
      setShowLessonOptions(activeRun.step === 'prepare' || Boolean(activeRun.lessonId));
      const beforeAnalysis = ['prepare', 'guide', 'capture', 'idea'].includes(activeRun.step);
      setScriptFollowing(activeRun.lessonId ? beforeAnalysis ? null : activeRun.scriptFollowing : 'free');
      setActiveRun((run) => run && beforeAnalysis && run.lessonId ? { ...run, scriptFollowing: null } : run);
      setScreen('flow');
      return;
    }
    setGuideStepIndex(0);
    setGuideEnabled(false);
    setScriptFollowing(presetForNextRun ? null : 'free');
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    if (transcriptionTimer.current) window.clearTimeout(transcriptionTimer.current);
    setPhotoUrl(null);
    setPhotoName('');
    setAudioUrl(null);
    setAudioFileName('');
    setTranscriptionStatus('idle');
    setRecordingError('');
    setSubject('Bướm');
    setSubjectCorrection('Bướm');
    setIdea('');
    setRewriteSuggestion('');
    setScriptModifier('');
    setMismatchModalOpen(false);
    const initialLessonId = presetForNextRun;
    const initialLesson = availableLessons.find((lesson) => lesson.id === initialLessonId);
    setGuideTopic(initialLessonId === 'sky' ? 'Bầu trời' : 'Khu vườn');
    setPresetForNextRun(null);
    setSelectedLessonId(initialLessonId);
    setShowLessonOptions(true);
    setSelectedActivityId(initialLesson?.activities[0]?.title ?? null);
    setScriptFollowing(initialLessonId ? null : 'free');
    setStep('prepare');
    setActiveRun({ id: String(Date.now()), childId: selectedChildId, lessonId: initialLessonId, step: 'prepare', status: 'active', rewriteCount: 0, regenCount: 0, scriptFollowing: initialLessonId ? null : 'free' });
    setScreen('flow');
  };

  const nextStep = () => {
    if (step === 'guide' && guideStepIndex < guideSteps.length - 1) {
      setGuideStepIndex((index) => Math.min(guideSteps.length - 1, index + 1));
      return;
    }
    if (step === 'prepare') {
      setScriptFollowing(selectedLessonId ? null : 'free');
      setActiveRun((run) => run ? { ...run, lessonId: selectedLessonId, scriptFollowing: selectedLessonId ? null : 'free' } : run);
      if (guideEnabled) {
        setStep('guide');
        setActiveRun((run) => run ? { ...run, step: 'guide' } : run);
        return;
      }
    }
    if (step === 'script') { acceptScript(); return; }
    if (step === 'review' && selectedLesson && !scriptFollowing) {
      setToast('Chọn hướng kể sau khi rà soát kết quả phân tích.');
      return;
    }
    const next = flowSteps[Math.min(stepIndex + 1, flowSteps.length - 1)];
    if (next?.key === 'script' && selectedLesson && !selectedActivityId && selectedLesson.activities.length) {
      setSelectedActivityId(selectedLesson.activities[0].title);
    }
    setStep(next?.key ?? 'review');
    setActiveRun((run) => run ? { ...run, step: next?.key ?? 'review' } : run);
  };

  const previousStep = () => {
    if (step === 'guide' && guideStepIndex > 0) {
      setGuideStepIndex((index) => Math.max(0, index - 1));
      return;
    }
    if (stepIndex <= 0) {
      setStep('prepare');
      setActiveRun((run) => run ? { ...run, step: 'prepare' } : run);
      setScreen('home');
      return;
    }
    const previous = flowSteps[stepIndex - 1];
    setStep(previous.key);
    setActiveRun((run) => run ? { ...run, step: previous.key } : run);
  };

  const acceptScript = () => {
    if (activeRun?.needsRegeneration && activeRun.regenCount >= 2) {
      setToast('Đã hết 2 lượt tạo lại video cho câu chuyện này.');
      return;
    }
    setStep('generating');
    setPreviewJobStage(0);
    setPreviewJobState('processing');
    setActiveRun((run) => run ? { ...run, status: 'active', step: 'generating' } : run);
  };

  const advancePreviewJob = () => {
    if (previewJobState !== 'processing') return;
    if (previewJobStage >= 3) {
      setStep('ready');
      setActiveRun((run) => run ? { ...run, status: 'ready', step: 'ready' } : run);
      return;
    }
    setPreviewJobStage((stage) => Math.min(3, stage + 1));
  };

  const finishStory = () => {
    if (activeRun) setStories((current) => current.map((story) => story.id === Number(activeRun.id) ? { ...story, status: 'completed' } : story));
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setPhotoUrl(null); setAudioUrl(null); setAudioFileName('');
    setActiveRun(null);
    setSelectedLessonId(null);
    setScreen('home');
    setStep('prepare');
    setIsPlaying(false);
    setToast('Đã hoàn tất câu chuyện trong phiên xem trước.');
  };

  const openSessionFeedback = (storyId: number) => {
    setFeedbackStoryId(storyId);
    setSessionRating(0);
    setSessionTags([]);
    setSessionNote('');
    setScreen('session-feedback');
  };

  const saveSessionFeedback = () => {
    if (feedbackStoryId === null || sessionRating < 1 || sessionRating > 5) return;
    const record: StoryFeedback = { rating: sessionRating, tags: sessionTags, note: sessionNote.trim() };
    setStories((current) => current.map((story) => story.id === feedbackStoryId ? { ...story, sessionFeedback: record } : story));
    if (activeRun && Number(activeRun.id) === feedbackStoryId) finishStory();
    else { setScreen('history'); setToast('Đã lưu cảm nhận trong phiên xem trước.'); }
    setFeedbackStoryId(null);
  };

  const skipSessionFeedback = () => {
    if (activeRun && Number(activeRun.id) === feedbackStoryId) finishStory();
    else setScreen('history');
    setFeedbackStoryId(null);
  };

  const openActivities = (lessonId: string, origin: 'flow' | 'run-detail') => {
    if (!availableLessons.some((lesson) => lesson.id === lessonId)) { setToast('Giáo án này hiện không khả dụng.'); return; }
    setActivityLessonId(lessonId);
    setActivityOrigin(origin);
    setKidView(false);
    setScreen('activities');
  };

  const handlePhoto = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) { setToast('Chỉ chọn được tệp ảnh.'); return; }
    const nextUrl = URL.createObjectURL(file);
    setPhotoUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return nextUrl;
    });
    setPhotoName(file.name);
  };

  const removeStory = (id: number) => {
    setStories((current) => current.filter((story) => story.id !== id));
    if (activeRun && Number(activeRun.id) === id) { setActiveRun(null); setStep('prepare'); setScreen('history'); }
    setPendingDelete(null);
    setToast('Đã xóa câu chuyện mẫu khỏi lịch sử xem trước.');
  };

  const applySubjectCorrection = (value: string) => {
    const nextSubject = value.trim();
    if (!nextSubject || nextSubject === subject) return;
    setSubject(nextSubject);
    setSubjectCorrection(nextSubject);
    setToast('Đã đổi chủ thể gợi ý trong bản xem trước; chưa chạy phân tích AI.');
  };

  const runSampleTranscription = () => {
    if (transcriptionTimer.current) window.clearTimeout(transcriptionTimer.current);
    setTranscriptionStatus('transcribing');
    const transcript = 'Con muốn kể về chú bướm đang tìm một vệt nắng ấm trong khu vườn.';
    const words = transcript.split(' ');
    const baseText = idea.trim();
    let idx = 0;
    const stepText = () => {
      idx = Math.min(words.length, idx + 3);
      const chunk = words.slice(0, idx).join(' ');
      setIdea(baseText ? `${baseText}\n${chunk}` : chunk);
      if (idx < words.length) {
        transcriptionTimer.current = window.setTimeout(stepText, 140);
      } else {
        setTranscriptionStatus('complete');
      }
    };
    transcriptionTimer.current = window.setTimeout(stepText, 240);
  };

  const handleAudioFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('audio/')) { setRecordingError('Tệp đã chọn không phải âm thanh.'); return; }
    if (file.size > 20 * 1024 * 1024) { setRecordingError('Tệp quá lớn. Hãy chọn bản ghi ngắn hơn.'); return; }
    const nextUrl = URL.createObjectURL(file);
    const probe = new Audio();
    probe.preload = 'metadata';
    probe.onloadedmetadata = () => {
      if (probe.duration > 120) { URL.revokeObjectURL(nextUrl); setRecordingError('Bản ghi quá dài. Hãy chọn tệp ngắn hơn.'); return; }
      setAudioUrl((previous) => { if (previous) URL.revokeObjectURL(previous); return nextUrl; });
      setAudioFileName(file.name); setRecordingError(''); runSampleTranscription();
    };
    probe.onerror = () => {
      URL.revokeObjectURL(nextUrl);
      setRecordingError('Không thể xác minh thời lượng tệp. Chọn tệp khác hoặc tiếp tục bằng văn bản.');
    };
    probe.src = nextUrl;
  };

  const downloadLesson = () => {
    const content = `${selectedLessonDetail.title} · ${selectedLessonDetail.version}\n\n${selectedLessonDetail.description}\n\n${selectedLessonDetail.activities.map((activity, index) => `${index + 1}. ${activity.title}\nVật liệu: ${activity.materials}\nHướng dẫn: ${activity.instructions}\nLưu ý: ${activity.note}`).join('\n\n')}`;
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${selectedLessonDetail.id}-${selectedLessonDetail.version}.txt`; anchor.style.display = 'none'; document.body.append(anchor); anchor.click(); anchor.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setToast('Đã tải nội dung giáo án được phép. Không bao gồm video của trẻ.');
  };

  const stopRecording = () => {
    if (recordingTimer.current) window.clearTimeout(recordingTimer.current);
    if (mediaRecorder.current?.state === 'recording') mediaRecorder.current.stop();
    setIsRecording(false);
  };

  const toggleRecording = async () => {
    if (isRecording) { stopRecording(); return; }
    setRecordingError('');
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { setRecordingError('Thiết bị chưa hỗ trợ ghi âm.'); return; }
    let openedStream: MediaStream | null = null;
    try {
      openedStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const stream = openedStream;
      const recorder = new MediaRecorder(stream);
      audioChunks.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size) audioChunks.current.push(event.data); };
      recorder.onstop = () => {
        const blob = new Blob(audioChunks.current, { type: recorder.mimeType || 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        if (!blob.size) { setRecordingError('Chưa ghi được âm thanh. Hãy thử lại.'); setTranscriptionStatus('error'); return; }
        if (blob.size > 20 * 1024 * 1024) { setRecordingError('Bản ghi vượt giới hạn cho phép.'); setTranscriptionStatus('error'); return; }
        setAudioUrl((previous) => { if (previous) URL.revokeObjectURL(previous); return URL.createObjectURL(blob); });
        setAudioFileName('Bản ghi giọng nói'); runSampleTranscription();
      };
      mediaRecorder.current = recorder;
      recorder.start();
      setIsRecording(true);
      recordingTimer.current = window.setTimeout(stopRecording, 120_000);
    } catch {
      openedStream?.getTracks().forEach((track) => track.stop());
      setRecordingError('Chưa có quyền dùng micro.');
      setTranscriptionStatus('error');
    }
  };

  const requestRewrite = () => {
    const remaining = 3 - (activeRun?.rewriteCount ?? 0);
    if (remaining <= 0) { setToast('Đã dùng hết 3 lượt yêu cầu viết lại kịch bản.'); return; }
    setIdeaMode('rewrite');
    setRewriteSuggestion('');
    setActiveRun((run) => run ? { ...run, step: 'idea', needsRegeneration: run.status === 'ready' || run.needsRegeneration } : run);
    setScreen('flow');
    setStep('idea');
  };

  const submitRewrite = () => {
    if (!rewriteSuggestion.trim()) { setToast('Nhập gợi ý trước khi gửi yêu cầu viết lại.'); return; }
    setScriptModifier(rewriteSuggestion.trim());
    setActiveRun((run) => run ? { ...run, rewriteCount: run.rewriteCount + 1, status: 'active', step: 'script' } : run);
    setIdeaMode('initial');
    setStep('script');
    setToast('Gợi ý đã lưu trong bản xem trước; chưa gửi đến dịch vụ AI.');
  };

  const beginRegeneration = () => {
    if (!activeRun || activeRun.regenCount >= 2) { setToast('Đã hết lượt tạo lại video.'); return; }
    setPendingRegenerate(false);
    setActiveRun((run) => run ? { ...run, needsRegeneration: true, status: 'active', step: 'script' } : run);
    setStep('script');
    setIsPlaying(false);
    setToast('Đã chuyển về duyệt kịch bản. Video cũ vẫn được giữ đến khi ba mẹ chấp nhận yêu cầu tạo lại.');
  };

  const cancelActiveRun = () => {
    setPendingCancel(false);
    if (activeRun) setStories((current) => current.filter((story) => story.id !== Number(activeRun.id)));
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setPhotoUrl(null); setAudioUrl(null); setAudioFileName('');
    setActiveRun(null);
    setStep('prepare');
    setScreen('home');
    setToast('Đã hủy luồng xem trước; chưa có nội dung nào được gửi đi.');
  };

  const removeChildPreview = (childId: string) => {
    const child = profiles.find((item) => item.id === childId);
    if (!child) { setPendingDeleteChildId(null); return; }
    if (activeRun?.childId === childId) { setPendingDeleteChildId(null); setToast('Hoàn tất hoặc hủy câu chuyện đang mở trước khi xóa hồ sơ này.'); return; }
    if (child.photoUrl?.startsWith('blob:')) URL.revokeObjectURL(child.photoUrl);
    const remaining = profiles.filter((item) => item.id !== childId);
    setProfiles(remaining);
    setStories((current) => current.filter((story) => story.childId !== childId));
    setDeliveries((current) => current.filter((delivery) => delivery.childId !== childId));
    setGrants((current) => current.filter((grant) => grant.childId !== childId));
    if (selectedChildId === childId) setSelectedChildId(remaining[0]?.id ?? '');
    setDetailChildId(remaining[0]?.id ?? '');
    setSelectedStoryId(null);
    setFeedbackStoryId(null);
    setPendingDeleteChildId(null);
    setScreen('profile');
    setToast('Đã xóa hồ sơ và nội dung mẫu liên kết trong phiên xem trước.');
  };

  const saveChild = () => {
    const years = Number(childAgeYears);
    const months = Number(childAgeMonths);
    const ageMonths = years * 12 + months;
    if (!childName.trim() || !Number.isInteger(years) || !Number.isInteger(months) || months < 0 || months > 11 || ageMonths < 36 || ageMonths > 120) {
      setToast('Nhập tuổi từ 3 đến 10 tuổi; tháng lẻ từ 0 đến 11.');
      return;
    }
    if (childEditingId) {
      setProfiles((current) => current.map((child) => child.id === childEditingId ? { ...child, name: childName.trim(), ageMonths, gender: childGender, nickname: childNickname.trim() || undefined, supportNeeds: childSupport.trim() || undefined, photoUrl: childPhotoUrl ?? undefined, interests: childInterests.trim() || undefined, observations: childObservations.trim() || undefined, achievements: childAchievements.trim() || undefined, externalExperiences: childExperiences.trim() || undefined, initial: childName.trim().slice(-1).toUpperCase() } : child));
      setStories((current) => current.map((story) => story.childId === childEditingId ? { ...story, child: childName.trim() } : story));
      setDeliveries((current) => current.map((delivery) => delivery.childId === childEditingId ? { ...delivery, child: childName.trim() } : delivery));
    } else {
      const child: Child = { id: `child-${Date.now()}`, name: childName.trim(), ageMonths, gender: childGender, nickname: childNickname.trim() || undefined, supportNeeds: childSupport.trim() || undefined, photoUrl: childPhotoUrl ?? undefined, interests: childInterests.trim() || undefined, observations: childObservations.trim() || undefined, achievements: childAchievements.trim() || undefined, externalExperiences: childExperiences.trim() || undefined, tone: profiles.length % 2 ? 'lavender' : 'peach', initial: childName.trim().slice(-1).toUpperCase() };
      setProfiles((current) => [...current, child]);
      setSelectedChildId(child.id);
    }
    setScreen('profile');
    setToast('Đã cập nhật hồ sơ trong phiên xem trước; chưa lưu lên tài khoản.');
  };

  const sendShareInvite = () => {
    const teacher = verifiedTeacherPreview.find((item) => item.id === shareTeacherId);
    if (!teacher) { setToast('Chọn một giáo viên đã xác minh để xem thử lời mời.'); return; }
    setGrants((current) => [{ id: `grant-${Date.now()}`, childId: shareChildId, recipient: teacher.name, organization: teacher.school, status: 'invited', date: 'Đang chờ giáo viên chấp nhận' }, ...current]);
    setShareTeacherId(''); setScreen('sharing');
    setToast('Đã thêm lời mời mẫu. Chưa gửi tới giáo viên hay cấp quyền truy cập.');
  };

  const submitFeedback = () => {
    if (!feedbackText.trim()) { setToast('Viết nội dung phản hồi trước khi gửi.'); return; }
    setDeliveries((current) => current.map((delivery) => delivery.id === selectedDeliveryId ? { ...delivery, parentFeedback: feedbackText.trim() } : delivery));
    setFeedbackText(''); setScreen('delivery-detail');
    setToast('Đã lưu phản hồi nháp trong phiên xem trước; chưa gửi tới trường.');
  };

  const selectScreen = (next: Screen) => {
    setScreen(next);
    setShowSettings(false);
  };

  const beginChildForm = (child?: Child) => {
    setChildEditingId(child?.id ?? null);
    setChildName(child?.name ?? '');
    setChildAgeYears(child ? String(Math.floor(child.ageMonths / 12)) : '');
    setChildAgeMonths(child ? String(child.ageMonths % 12) : '0');
    setChildGender(child?.gender ?? 'unspecified');
    setChildNickname(child?.nickname ?? '');
    setChildSupport(child?.supportNeeds ?? '');
    setChildInterests(child?.interests ?? '');
    setChildObservations(child?.observations ?? '');
    setChildAchievements(child?.achievements ?? '');
    setChildExperiences(child?.externalExperiences ?? '');
    setChildPhotoUrl(child?.photoUrl ?? null);
    setScreen('child-form');
  };

  const handleChildPhoto = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) { setToast('Chỉ chọn được tệp ảnh.'); return; }
    const nextUrl = URL.createObjectURL(file);
    setChildPhotoUrl((previous) => { if (previous) URL.revokeObjectURL(previous); return nextUrl; });
  };

  const openStory = (story: Story) => {
    setSelectedStoryId(story.id);
    if (activeRun && story.id === Number(activeRun.id) && activeRun.needsRegeneration) setScreen('run-detail');
    else if (activeRun && story.id === Number(activeRun.id)) { setStep(activeRun.step); setScreen('flow'); }
    else setScreen('run-detail');
  };

  const openDelivery = (delivery: LessonDelivery) => {
    setSelectedDeliveryId(delivery.id);
    setSelectedLessonDetailId(delivery.lessonId);
    setLessonDetailOrigin('delivery');
    setScreen('delivery-detail');
  };

  const openNotice = (notice: AppNotice) => {
    setNotices((current) => current.map((item) => item.id === notice.id ? { ...item, read: true } : item));
    if (notice.kind === 'feedback') { openDelivery(deliveries[0]); return; }
    if (notice.kind === 'run' && activeRun) { setScreen('flow'); setStep(activeRun.step); return; }
    if (notice.kind === 'story') {
      const story = stories.find((item) => item.status === 'ready' || item.status === 'completed');
      if (story) { openStory(story); return; }
    }
    setScreen('history');
  };

  const renderVideoPreview = (caption: string, showDuration = false) => <div className={`story-player ${playerExpanded ? 'is-expanded' : ''}`}>
    <button className={`video-preview ${isPlaying ? 'is-playing' : ''}`} onClick={() => setIsPlaying((value) => !value)} aria-label={isPlaying ? 'Tạm dừng bản xem trước' : 'Xem bản minh họa câu chuyện'}>
      <StoryArt variant="hero" />
      <span className="video-preview__play"><Icon name={isPlaying ? 'check' : 'play'} size={24} /></span>
      {showDuration && <span className="video-preview__duration">01:24</span>}
    </button>
    <button className="story-player__expand" onClick={() => setPlayerExpanded((value) => !value)} aria-label={playerExpanded ? 'Thu nhỏ khung xem' : 'Mở khung xem toàn màn hình'}><Icon name={playerExpanded ? 'close' : 'expand'} size={20} /></button>
    <button className={`story-player__cc ${captionsEnabled ? 'is-on' : ''}`} onClick={() => setCaptionsEnabled((value) => !value)} aria-label={captionsEnabled ? 'Tắt phụ đề' : 'Bật phụ đề'} aria-pressed={captionsEnabled}>CC</button>
    {captionsEnabled && <div className="story-player__caption" aria-live="polite">{caption}</div>}
  </div>;

  const renderFlowStep = () => {
    switch (step) {
      case 'prepare':
        return <>
          <div className="flow-intro flow-intro--prepare">
            <span className="flow-intro__eyebrow"><Icon name="spark" size={14} /> BẮT ĐẦU TỪ BÉ</span>
            <h1>Hôm nay mình kể chuyện cùng bé nào?</h1>
            <p>Chọn bé để bắt đầu.</p>
          </div>
          <section className="flow-section">
            <div className="section-heading"><h2>Chọn hồ sơ trẻ</h2><span>{profiles.length} hồ sơ · Chọn 1 bé</span></div>
            <div className="child-choice-list">
              {profiles.map((child) => <button key={child.id} className={`child-choice ${selectedChildId === child.id ? 'is-selected' : ''}`} onClick={() => { setSelectedChildId(child.id); setActiveRun((run) => run ? { ...run, childId: child.id } : run); }} aria-pressed={selectedChildId === child.id}>
                <ChildAvatar child={child} size="lg" />
                <span className="child-choice__text"><strong>{child.name}</strong><small>{formatChildAge(child.ageMonths)} · {formatChildGender(child.gender)}</small></span>
                <span className="radio-mark"><Icon name="check" size={14} /></span>
              </button>)}
            </div>
          </section>
          <section className="flow-section">
            <div className="section-heading"><h2>Giáo án</h2><span className="optional-label">Tùy chọn</span></div>
            <button className="lesson-setup-toggle" onClick={() => setShowLessonOptions((open) => !open)} aria-expanded={showLessonOptions} aria-controls="story-lesson-library">
              <span className="lesson-setup-toggle__icon"><Icon name={selectedLesson ? 'book' : 'spark'} size={19} /></span>
              <span className="lesson-setup-toggle__copy"><strong>{selectedLesson?.title ?? 'Không dùng giáo án'}</strong><small>{selectedLesson ? `${selectedLesson.version} · đã chọn` : 'Có thể thêm giáo án, hoặc bắt đầu ngay bằng tranh.'}</small></span>
              <span className="lesson-setup-toggle__action">{showLessonOptions ? 'Ẩn' : selectedLesson ? 'Đổi' : 'Thêm'}</span>
            </button>
            {showLessonOptions && <div className="lesson-choice-list" id="story-lesson-library">
              {[{ title: 'Giáo án công khai trên hệ thống', note: 'Giáo án mẫu có thể dùng như preset.', items: publicLessons }, { title: 'Giáo án trường / giáo viên gửi', note: 'Chỉ hiện nội dung đã được chia sẻ cho gia đình.', items: sharedLessons }].map((group) => <section className="lesson-choice-group" key={group.title} aria-label={group.title}>
                <div className="lesson-choice-group__heading"><strong>{group.title}</strong><small>{group.note}</small></div>
                {group.items.length ? group.items.map((lesson) => <article key={lesson.id} className={`lesson-choice-card ${selectedLessonId === lesson.id ? 'is-selected' : ''}`}>
                    <button className="lesson-choice" onClick={() => { setSelectedLessonId(lesson.id); setGuideTopic(lesson.id === 'sky' ? 'Bầu trời' : 'Khu vườn'); setShowLessonOptions(false); setScriptFollowing(null); setSelectedActivityId(lesson.activities[0]?.title ?? null); setActiveRun((run) => run ? { ...run, lessonId: lesson.id, scriptFollowing: null } : run); }} aria-pressed={selectedLessonId === lesson.id}>
                    <span className={`lesson-icon lesson-icon--${lesson.color}`}><Icon name="book" size={20} /></span>
                    <span className="lesson-choice__text"><strong>{lesson.title}</strong><small>{lesson.meta} · {lesson.version}</small></span>
                    <span className="radio-mark"><Icon name="check" size={14} /></span>
                  </button>
                  <button type="button" className="lesson-detail-action" onClick={() => setLessonPreviewId(lesson.id)}>Chi tiết</button>
                </article>) : <p className="lesson-choice-empty">Chưa có giáo án được chia sẻ trong bản xem trước.</p>}
              </section>)}
              <button className={`lesson-choice lesson-choice--plain ${selectedLessonId === null ? 'is-selected' : ''}`} onClick={() => { setSelectedLessonId(null); setSelectedActivityId(null); setGuideTopic('Khu vườn'); setShowLessonOptions(false); setScriptFollowing('free'); setActiveRun((run) => run ? { ...run, lessonId: null, scriptFollowing: 'free' } : run); }} aria-pressed={selectedLessonId === null}>
                <span className="lesson-icon lesson-icon--plain"><Icon name="spark" size={19} /></span>
                <span className="lesson-choice__text"><strong>Tiếp tục không dùng giáo án</strong><small>Câu chuyện vẫn bắt đầu từ tranh của bé</small></span>
                <span className="radio-mark"><Icon name="check" size={14} /></span>
              </button>
            </div>}
          </section>
          <label className="guide-option"><input type="checkbox" checked={guideEnabled} onChange={(event) => setGuideEnabled(event.target.checked)} /><span><strong>Thêm gợi ý vẽ trước khi chụp</strong><small>Tùy chọn · phác thảo nét theo chủ đề, bỏ qua bất cứ lúc nào</small></span><Icon name="spark" size={19} /></label>
        </>;
      case 'guide':
        return <>
          <div className="flow-intro"><span className="flow-intro__eyebrow"><Icon name="spark" size={14} /> GỢI Ý VẼ · TÙY CHỌN</span><h1>Cùng bé phác vài nét nhé.</h1><p>Gợi ý chung theo chủ đề, không dùng hồ sơ hay ảnh của bé.</p></div>
          <section className="guide-options-card" aria-label="Tùy chỉnh gợi ý vẽ"><label htmlFor="guide-topic">Chủ đề gợi ý</label><select id="guide-topic" className="text-field" value={guideTopic} onChange={(event) => { setGuideTopic(event.target.value); setGuideStepIndex(0); }}><option>Khu vườn</option><option>Bầu trời</option><option>Đại dương</option><option>Vũ trụ</option></select><span className="guide-options-label">Mức gợi ý</span><div className="guide-difficulty-choice" role="group" aria-label="Mức độ gợi ý">{(['Nhẹ nhàng', 'Thêm chi tiết'] as const).map((level) => <button type="button" key={level} className={guideDifficulty === level ? 'is-selected' : ''} onClick={() => { setGuideDifficulty(level); setGuideStepIndex(0); }} aria-pressed={guideDifficulty === level}>{level}</button>)}</div></section>
          <section className="parent-sketch-preview" aria-label={`Gợi ý vẽ tĩnh · bước ${guideStepIndex + 1} trên ${guideSteps.length}`}><div className="guide-step-header"><span className="preview-state">BẢN MINH HỌA · CHƯA TẠO AI</span><span>{String(guideStepIndex + 1).padStart(2, '0')} / {String(guideSteps.length).padStart(2, '0')}</span></div><SketchGuideIllustration topic={guideTopic} stepIndex={guideStepIndex} detailed={guideDifficulty === 'Thêm chi tiết'} /><div className="guide-step-copy"><strong>{guideStep.title}</strong><p>{guideStep.detail}</p></div><div className="guide-step-progress" aria-label={`Bước ${guideStepIndex + 1} trên ${guideSteps.length}`}>{guideSteps.map((item, index) => <span key={item.title} className={index === guideStepIndex ? 'is-current' : index < guideStepIndex ? 'is-complete' : ''} />)}</div><div className="guide-step-controls"><button type="button" className="button button--secondary" disabled={guideStepIndex === 0} onClick={() => setGuideStepIndex((index) => Math.max(0, index - 1))}>Bước trước</button><span>Bước {guideStepIndex + 1} / {guideSteps.length}</span></div></section>
          <button type="button" className="text-button text-button--center" onClick={() => { setGuideEnabled(false); setGuideStepIndex(0); setStep('capture'); setActiveRun((run) => run ? { ...run, step: 'capture' } : run); }}>Bỏ qua gợi ý vẽ</button>
        </>;
      case 'capture':
        return <>
          <div className="flow-intro">
            <h1>Chụp tranh của {selectedChild.name}.</h1>
            <p>Chụp rõ trọn trang giấy hoặc chọn ảnh từ máy.</p>
          </div>
          <div className="capture-frame">
            {photoUrl ? <img src={photoUrl} alt="Bức vẽ đã chọn" /> : <><div className="capture-guides" /><div className="capture-empty"><span className="capture-empty__icon"><Icon name="camera" size={25} /></span><strong>Chưa có tranh</strong><small>Ảnh sẽ hiện ở đây sau khi chụp hoặc chọn.</small></div></>}
          </div>
          {photoName && <p className="file-name"><Icon name="check" size={15} /> {photoName}</p>}
          <div className="capture-actions">
            <button className="button button--primary button--wide" onClick={() => document.getElementById('camera-input')?.click()}><Icon name="camera" size={20} /> Chụp tranh</button>
            <button className="button button--secondary button--wide" onClick={() => document.getElementById('gallery-input')?.click()}><Icon name="upload" size={19} /> Chọn ảnh</button>
            <input id="camera-input" className="visually-hidden" type="file" accept="image/*" capture="environment" onChange={handlePhoto} aria-label="Chụp ảnh tranh" />
            <input id="gallery-input" className="visually-hidden" type="file" accept="image/*" onChange={handlePhoto} aria-label="Chọn ảnh tranh từ thư viện" />
          </div>
          <div className="inline-note"><Icon name="lock" size={16} /><span>Ảnh chỉ lưu tạm trong phiên xem trước này.</span></div>
        </>;
      case 'review':
        return <>
          <div className="flow-intro">
            <h1>Trong tranh của bé có gì nhỉ?</h1>
            <p>Kiểm tra chủ thể nhận diện từ tranh của {selectedChild.name}. Hồ sơ bé được áp dụng tự động.</p>
          </div>
          <div className="auto-context-pill" role="note">
            <Icon name="user" size={16} />
            <span>Tự động theo hồ sơ <strong>{selectedChild.name}</strong> ({formatChildAge(selectedChild.ageMonths)}){selectedLesson ? ` · ${selectedLesson.title}` : ''}</span>
          </div>
          <div className="review-art">{photoUrl ? <img src={photoUrl} alt={`Bức vẽ đã chọn của ${selectedChild.name}`} /> : <div className="review-art-empty"><Icon name="camera" size={26} /><span>Chưa có ảnh trong phiên này</span></div>}<span className="image-caption">Tranh của {selectedChild.name}</span></div>
          <section className="subject-panel">
            <div className="subject-panel__title"><Icon name="spark" size={14} /> Chủ thể nhận diện · có thể chỉnh</div>
            <p className="subject-suggestion">Đang chọn: <strong>{subject.toLowerCase()}</strong>.</p>
            <div className="subject-chips">{['Bướm', 'Hoa', 'Bầu trời', ...(showAllSubjects ? ['Cây cỏ', 'Mặt trời'] : [])].map((item) => <button key={item} onClick={() => { applySubjectCorrection(item); if (selectedLesson && !isSubjectAlignedWithLesson(selectedLessonId, item)) { setScriptFollowing(null); setActiveRun((run) => run ? { ...run, scriptFollowing: null } : run); } }} className={`subject-chip ${subject === item ? 'is-selected' : ''}`} aria-pressed={subject === item}>{subject === item && <Icon name="check" size={13} />}{item}</button>)}</div>
            <button className="text-button" onClick={() => setShowAllSubjects((value) => !value)}><Icon name="edit" size={15} /> {showAllSubjects ? 'Thu gọn' : 'Chỉnh chủ thể'}</button>
            {showAllSubjects && <div className="custom-subject"><input className="text-field" value={subjectCorrection} maxLength={40} onChange={(event) => setSubjectCorrection(event.target.value)} aria-label="Chủ thể ba mẹ muốn sửa" placeholder="Nhập chủ thể khác" /><button className="button button--secondary" onClick={() => applySubjectCorrection(subjectCorrection)}>Áp dụng chủ thể</button></div>}
          </section>
          {selectedLesson && <section className={`mismatch-preview-result ${subjectAligned ? 'is-aligned' : 'is-mismatch'}`} aria-live="polite"><div><span className="preview-state">ĐỐI CHIẾU GIÁO ÁN · XEM TRƯỚC</span><strong>{subjectAligned ? 'Chủ thể phù hợp với mục tiêu giáo án' : 'Tranh bé đang mở ra hướng khác giáo án'}</strong><small>Ba mẹ chọn hướng kể cho câu chuyện tiếp theo.</small></div><div className="direction-options">{[{ key: 'lesson' as const, title: 'Ưu tiên mục tiêu giáo án', desc: 'Lồng ghép kiến thức của giáo án.' }, { key: 'free' as const, title: 'Ưu tiên tranh của bé', desc: 'Kể tự do theo nét vẽ bé thích.' }].map((option) => <button key={option.key} type="button" className={scriptFollowing === option.key ? 'is-selected' : ''} onClick={() => { setScriptFollowing(option.key); setActiveRun((run) => run ? { ...run, scriptFollowing: option.key } : run); }} aria-pressed={scriptFollowing === option.key}><strong>{option.title}</strong><small>{option.desc}</small></button>)}</div></section>}
        </>;
      case 'idea':
        return <>
          <div className="flow-intro">
            <h1>{ideaMode === 'rewrite' ? 'Muốn đổi chi tiết nào?' : 'Bé muốn kể điều gì?'}</h1>
            <p>{ideaMode === 'rewrite' ? 'Gửi gợi ý cho kịch bản mới.' : 'Nói hoặc gõ trực tiếp vào khung bên dưới. Có thể bỏ qua.'}</p>
          </div>
          <label className="field-label" htmlFor="story-idea">{ideaMode === 'rewrite' ? 'Gợi ý cần thay đổi' : 'Ý tưởng câu chuyện'} <span>{ideaMode === 'rewrite' ? `Còn ${Math.max(0, 3 - (activeRun?.rewriteCount ?? 0))} lượt` : 'Tùy chọn'}</span></label>
          <textarea id="story-idea" className="idea-field" value={ideaMode === 'rewrite' ? rewriteSuggestion : idea} onChange={(event) => { ideaMode === 'rewrite' ? setRewriteSuggestion(event.target.value) : setIdea(event.target.value); }} rows={5} placeholder={ideaMode === 'rewrite' ? 'Ví dụ: Hãy để câu chuyện có thêm một người bạn mới...' : 'Nói vào micro để chữ chạy trực tiếp tại đây, hoặc gõ ý tưởng của ba mẹ...'} />
          {ideaMode === 'initial' && transcriptionStatus === 'transcribing' && <div className="audio-live-status" role="status" aria-live="polite"><span className="transcription-spinner" /><span>Đang chuyển giọng nói vào khung ý tưởng…</span></div>}
          {ideaMode === 'initial' && transcriptionStatus === 'error' && <div className="audio-live-status audio-live-status--error" role="status"><Icon name="refresh" size={15} /><span>Chưa nhận được lời nói.</span><button type="button" onClick={runSampleTranscription}>Thử lại</button></div>}
          {ideaMode === 'initial' && <button className={`record-button ${isRecording ? 'is-recording' : ''}`} onClick={toggleRecording} aria-pressed={isRecording}>
            <span className="record-button__icon"><Icon name="mic" size={20} /></span><span><strong>{isRecording ? 'Đang ghi âm · chạm để dừng' : 'Ghi âm giọng nói'}</strong><small>{isRecording ? 'Lời kể sẽ hiện trực tiếp ở khung trên' : 'Chạm để nói, đọc lại và chỉnh ngay'}</small></span><span className="record-wave" aria-hidden="true"><i /><i /><i /><i /><i /></span>
          </button>}
          {ideaMode === 'initial' && <label className="audio-upload">{audioFileName ? `Đã đính kèm: ${audioFileName}` : 'Tải tệp ghi âm (tùy chọn)'}<input className="visually-hidden" type="file" accept="audio/*" capture="user" onChange={handleAudioFile} /></label>}
          {audioUrl && <><div className="audio-ready"><Icon name="check" size={16} /><span>{audioFileName}</span><button type="button" onClick={() => { URL.revokeObjectURL(audioUrl); setAudioUrl(null); setAudioFileName(''); setTranscriptionStatus('idle'); setIdea(''); }}>Xóa</button></div><audio className="audio-player" controls src={audioUrl} aria-label="Nghe lại bản ghi ý tưởng" /></>}
          {ideaMode === 'rewrite' && <div className="soft-card soft-card--blue"><Icon name="edit" size={18} /><p>Ba mẹ sẽ xem lại kịch bản trước khi tạo video.</p></div>}
        </>;
      case 'script': {
        const chosenActivity = selectedLesson?.activities.find((activity) => activity.title === selectedActivityId) ?? selectedLesson?.activities[0] ?? null;
        return <>
          <div className="flow-intro">
            <h1>Kịch bản & hoạt động của {selectedChild.name}.</h1>
            <p>Chọn hoạt động cùng bé rồi duyệt kịch bản trước khi tạo video.</p>
          </div>
          {selectedLesson && selectedLesson.activities.length > 0 && <section className="prevideo-activity-panel" aria-label="Chọn hoạt động ngoài trời trước khi tạo video">
            <div className="section-heading"><h2>Hoạt động cùng bé</h2><span className="pill pill--green">Trước bước tạo video</span></div>
            <p className="prevideo-activity-panel__hint">Video sẽ lồng ghép hoạt động bên dưới để gia đình thực hành cùng con.</p>
            <div className="lesson-activity-choice-list">
              {selectedLesson.activities.map((activity, index) => {
                const isSelected = (chosenActivity?.title ?? null) === activity.title;
                return <button key={activity.title} type="button" className={`lesson-activity-choice ${isSelected ? 'is-selected' : ''}`} onClick={() => { setSelectedActivityId(activity.title); setToast(`Đã chọn hoạt động “${activity.title}” cho video.`); }} aria-pressed={isSelected}>
                  <span className="lesson-activity-choice__number">{String(index + 1).padStart(2, '0')}</span>
                  <span className="lesson-activity-choice__copy"><strong>{activity.title}</strong><small>Chuẩn bị: {activity.materials}</small><span>{activity.instructions}</span></span>
                  <span className="radio-mark"><Icon name="check" size={14} /></span>
                </button>;
              })}
            </div>
            <button type="button" className="text-button" onClick={() => openActivities(selectedLesson.id, 'flow')}><Icon name="leaf" size={15} /> Mở hướng dẫn đầy đủ & chế độ cùng bé</button>
          </section>}
          <article className="script-card">
            <div className="script-card__top"><span className="pill pill--peach">KỊCH BẢN XEM TRƯỚC</span><span className="script-revision">Sửa lại: {activeRun?.rewriteCount ?? 0}/3</span></div>
            <h2>{subject === 'Bướm' ? 'Chú bướm tìm nắng' : `${subject} và khu vườn nhỏ`}</h2>
            <div className="script-lead">
              {idea.trim() && <p><strong>Ý tưởng của gia đình:</strong> {idea.trim()}</p>}
              {chosenActivity && <p><strong>Hoạt động gắn kèm:</strong> {chosenActivity.title}</p>}
              {audioUrl && !idea.trim() && <p><strong>Bản ghi âm:</strong> Đã đính kèm trong phiên xem trước.</p>}
              {!idea.trim() && !audioUrl && !chosenActivity && <p>{`Một câu chuyện dịu dàng bắt đầu từ bức vẽ ${subject.toLowerCase()} của gia đình.`}</p>}
            </div>
            {scriptModifier && <div className="script-request"><strong>Gợi ý viết lại:</strong> {scriptModifier}</div>}
            <div className="story-scene"><span>01</span><p>Buổi sáng, chú {subject.toLowerCase()} nhỏ thức dậy giữa những bông hoa còn đọng sương.</p></div>
            <div className="story-scene"><span>02</span><p>Chú bay qua khu vườn, gặp một người bạn mới đang tìm ánh nắng ấm.</p></div>
            <div className="story-scene"><span>03</span><p>Người bạn mời chú quan sát những màu sắc đang hiện ra quanh mình.</p></div>
            <div className="story-scene"><span>04</span><p>Chú thử lắng nghe và phát hiện một điều thú vị ở khu vườn.</p></div>
            <div className="story-scene"><span>05</span><p>{chosenActivity ? `Kết chuyện, hai bạn rủ ${selectedChild.name} cùng thực hành “${chosenActivity.title}”.` : 'Cùng nhau, hai bạn tìm được nơi rực rỡ nhất để bắt đầu một ngày vui.'}</p></div>
            <div className="script-card__footer"><Icon name="lock" size={15} /><span>{scriptFollowing === 'lesson' ? 'Ưu tiên mục tiêu giáo án đã chọn' : 'Ưu tiên câu chuyện từ tranh của bé'} · riêng tư</span></div>
          </article>
          {activeRun?.needsRegeneration && <div className="soft-card soft-card--blue"><Icon name="lock" size={18} /><p>Video cũ vẫn được giữ cho đến khi ba mẹ chấp nhận tạo lại.</p><button className="text-button" onClick={() => { setSelectedStoryId(Number(activeRun.id)); setScreen('run-detail'); }}>Xem video cũ</button></div>}
          <button className="text-button text-button--center" onClick={requestRewrite} disabled={(activeRun?.rewriteCount ?? 0) >= 3}><Icon name="edit" size={15} /> Gửi gợi ý viết lại ({Math.max(0, 3 - (activeRun?.rewriteCount ?? 0))} lượt còn lại)</button>
        </>;
      }
      case 'generating':
        return <div className="processing-state processing-state--mockup">
          <span className="unavailable-icon"><Icon name="spark" size={28} /></span>
          <span className="pill pill--peach">TIẾN TRÌNH MINH HỌA</span>
          <h1>{previewJobState === 'failed' ? 'Tạm thời chưa hoàn tất.' : previewJobState === 'safety-blocked' ? 'Nội dung đang được giữ an toàn.' : 'Câu chuyện đang được chuẩn bị.'}</h1>
          <p>{previewJobState === 'failed' ? 'Có thể thử lại từ bước đang lỗi. Trạng thái này chỉ minh họa cách khôi phục.' : previewJobState === 'safety-blocked' ? 'Tình huống mẫu minh họa việc dừng tự động khi nội dung cần được rà soát.' : 'Theo dõi từng giai đoạn chuẩn bị câu chuyện cho bé.'}</p>
          <ol className="parent-job-timeline" aria-label="Các giai đoạn câu chuyện">
            {['Phân tích bức tranh', 'Tạo các cảnh câu chuyện', 'Lời kể và phụ đề', 'Kiểm tra an toàn tự động'].map((label, index) => <li key={label} className={index < previewJobStage ? 'is-complete' : index === previewJobStage && previewJobState === 'processing' ? 'is-current' : ''}><span>{index < previewJobStage ? <Icon name="check" size={15}/> : String(index + 1).padStart(2, '0')}</span><strong>{label}</strong><small>{index < previewJobStage ? 'Hoàn tất' : index === previewJobStage && previewJobState === 'processing' ? 'Đang xử lý' : 'Đang chờ'}</small></li>)}
          </ol>
          {previewJobState === 'failed' && <div className="parent-job-alert" role="alert"><strong>Đã xảy ra lỗi tạm thời</strong><span>Giữ nguyên bản nháp. Ba mẹ có thể thử lại giai đoạn này.</span></div>}
          {previewJobState === 'safety-blocked' && <div className="parent-job-alert parent-job-alert--safety" role="status"><strong>Đã dừng ở bước kiểm tra an toàn</strong><span>Quay lại kịch bản để chỉnh nội dung cho phù hợp.</span></div>}
          <div className="parent-job-actions">
            {previewJobState === 'processing' && <button className="button button--primary button--wide" onClick={advancePreviewJob}>{previewJobStage === 3 ? 'Hoàn tất & mở video' : 'Mô phỏng bước tiếp theo'} <Icon name="arrow" size={18}/></button>}
            {previewJobState === 'processing' && <button className="button button--secondary button--wide" onClick={() => setPreviewJobState('failed')}>Xem trạng thái lỗi mẫu</button>}
            {previewJobState === 'processing' && <button className="text-button text-button--center" onClick={() => setPreviewJobState('safety-blocked')}>Xem tình huống an toàn chặn</button>}
            {previewJobState === 'failed' && <button className="button button--primary button--wide" onClick={() => { setPreviewJobState('processing'); setToast('Đã thử lại bước minh họa.'); }}>Thử lại bước này</button>}
            {previewJobState === 'safety-blocked' && <button className="button button--secondary button--wide" onClick={() => { setStep('script'); setActiveRun((run) => run ? { ...run, step: 'script' } : run); }}>Quay lại kịch bản</button>}
          </div>
          <div className="preview-capability-list"><span><Icon name="lock" size={15}/>Ảnh và thông tin chỉ nằm trong phiên xem trước</span><span><Icon name="refresh" size={15}/>Có thể thu nhỏ rồi tiếp tục từ Trang chủ</span></div>
        </div>;
      case 'ready': {
        const chosenActivity = selectedLesson?.activities.find((activity) => activity.title === selectedActivityId) ?? selectedLesson?.activities[0] ?? null;
        return <>
          <div className="flow-intro flow-intro--center">
            <span className="success-seal"><Icon name="check" size={25} /></span>
            <span className="pill pill--green">Video sẵn sàng</span>
            <h1>{subject === 'Bướm' ? 'Chú bướm tìm nắng' : `${subject} và khu vườn nhỏ`}</h1>
            <p>Câu chuyện riêng của {selectedChild.name}.</p>
          </div>
          {renderVideoPreview(`Câu chuyện riêng của ${selectedChild.name}.`, true)}
          <div className="private-badge"><Icon name="lock" size={15} /> Riêng tư · phát trực tuyến trong gia đình</div>
          {selectedLesson && <section className="activity-callout">
            <span className="activity-callout__icon"><Icon name="leaf" size={22} /></span>
            <div><strong>{chosenActivity ? `Hoạt động cùng bé: ${chosenActivity.title}` : 'Hoạt động cùng bé'}</strong><small>{chosenActivity ? chosenActivity.instructions : `${selectedLesson.activities.length} hoạt động trong ${selectedLesson.title}`}</small></div>
            <button onClick={() => openActivities(selectedLesson.id, 'flow')} aria-label="Mở hướng dẫn hoạt động cùng bé"><Icon name="arrow" size={18} /></button>
          </section>}
          <div className="ready-actions"><button className="button button--primary button--wide" onClick={() => openSessionFeedback(Number(activeRun?.id))}>Hoàn tất · chia sẻ cảm nhận</button><button className="text-button text-button--center" disabled={(activeRun?.regenCount ?? 0) >= 2} onClick={() => setPendingRegenerate(true)}>{(activeRun?.regenCount ?? 0) >= 2 ? 'Đã dùng tối đa 2 lượt tạo lại' : `Đánh dấu video không phù hợp · còn ${2 - (activeRun?.regenCount ?? 0)} lượt tạo lại`}</button></div>
        </>;
      }
    }
  };

  const renderHome = () => <div className="parent-home">
    <header className="home-header">
      <div className="brand-lockup"><span className="brand-mark"><span /><span /><i /></span><span className="brand-name">Sketch<span>2</span>Life</span></div>
      <div className="home-header__actions">
        <button className="icon-button notification-button" onClick={() => setScreen('notifications')} aria-label="Mở thông báo"><Icon name="bell" size={20} />{notices.some((notice) => !notice.read) && <i />}</button>
        <button className="icon-button settings-trigger-button" onClick={() => setShowSettings(true)} aria-label="Mở cài đặt"><Icon name="settings" size={20} /></button>
      </div>
    </header>
    <main className="parent-home-content">
      <section className="parent-home-hero"><div className="parent-home-hero-copy"><span className="world-kicker"><Icon name="spark" size={15}/> GÓC TRUYỆN CỦA BÉ</span><h1>Nét vẽ<br/><em>nở hoa.</em></h1><p>Một câu chuyện mới bắt đầu từ tranh của con.</p></div><div className="parent-home-art" aria-hidden="true"><WonderWorldArt/></div></section>
      {activeRun && <section className={`active-run-card ${activeRun.status === 'ready' ? 'active-run-card--ready' : ''}`}><span className="active-run-card__icon"><Icon name={activeRun.status === 'ready' ? 'play' : 'refresh'} size={19} /></span><span><strong>{activeRun.status === 'ready' ? 'Video đã sẵn sàng' : 'Câu chuyện đang chờ tiếp tục'}</strong><small>{profiles.find((child) => child.id === activeRun.childId)?.name ?? 'Hồ sơ trẻ'} · {steps.find((item) => item.key === activeRun.step)?.label}</small></span><button onClick={() => { setStep(activeRun.step); setScreen('flow'); }}>Tiếp tục <Icon name="arrow" size={15} /></button>{activeRun.status !== 'ready' && <button className="active-run-cancel" onClick={() => setPendingCancel(true)}>Hủy</button>}</section>}
      <section className="home-start"><div><span className="home-start__eyebrow">TỪ TRANH CỦA CON</span><h2>Sẵn sàng kể chuyện?</h2><p>Chụp tranh, thêm ý tưởng rồi cùng xem lại câu chuyện.</p></div><button className="button button--hero" onClick={startStory}>{activeRun ? 'Tiếp tục kể' : 'Bắt đầu kể'} <Icon name="arrow" size={18} /></button></section>
    </main>
  </div>;

  const renderHistory = () => <>
    <PageHeader title="Lịch sử" subtitle="Câu chuyện và giáo án đã đến với gia đình" onBack={() => setScreen('home')} />
    <main className="subpage-content">
      <div className="preview-inline-note" role="note"><strong>Dữ liệu minh họa</strong><span>Câu chuyện, lượt phát và giáo án bên dưới chưa được đồng bộ với tài khoản.</span></div>
      <div className="segmented-control"><button className={historyTab === 'stories' ? 'is-active' : ''} onClick={() => setHistoryTab('stories')}>Câu chuyện</button><button className={historyTab === 'lessons' ? 'is-active' : ''} onClick={() => setHistoryTab('lessons')}>Giáo án đã nhận</button></div>
      {historyTab === 'stories' ? <>
        <div className="history-range-filter" role="group" aria-label="Khoảng thời gian"><span>Khoảng thời gian</span>{([30, 60] as const).map((days) => <button key={days} type="button" className={historyRange === days ? 'is-active' : ''} aria-pressed={historyRange === days} onClick={() => setHistoryRange(days)}>{days} ngày</button>)}</div>
        <div className="history-summary"><span className="history-summary__icon"><Icon name="book" size={21} /></span><div><strong>{stories.filter((story) => !story.hidden).length} câu chuyện mẫu</strong><small>Playback thật chưa được kết nối</small></div></div>
        <div className="history-filters" role="group" aria-label="Lọc câu chuyện">{([['all', 'Tất cả'], ['open', 'Chờ hoàn tất'], ['completed', 'Đã hoàn tất']] as const).map(([value, label]) => <button key={value} className={historyStatus === value ? 'is-active' : ''} onClick={() => setHistoryStatus(value)} aria-pressed={historyStatus === value}>{label}</button>)}</div>
        {visibleStories.length ? <div className="history-list">{visibleStories.map((story) => <StoryRow key={story.id} story={story} large profiles={profiles} onOpen={() => openStory(story)} onDelete={() => setPendingDelete(story.id)} />)}</div> : historyStatus !== 'all' ? <div className="history-filter-empty"><Icon name="book" size={21} /><p>Chưa có câu chuyện ở trạng thái này.</p><button onClick={() => setHistoryStatus('all')}>Xem tất cả</button></div> : <EmptyState title="Chưa có câu chuyện nào" body="Bức vẽ đầu tiên của bé có thể bắt đầu một chuyến phiêu lưu." action="Bắt đầu kể chuyện" onAction={startStory} />}
        {stories.some((story) => !story.hidden && story.sessionFeedback) && <section className="session-feedback-history"><div className="section-heading"><h2>Cảm nhận đã lưu</h2></div>{stories.filter((story) => !story.hidden && story.sessionFeedback).map((story) => <button key={story.id} onClick={() => openStory(story)}><Icon name="star" size={20} /><span><strong>{story.title} · {story.sessionFeedback?.rating}/5</strong><small>{story.sessionFeedback?.tags.join(' · ') || story.sessionFeedback?.note || 'Đánh giá của gia đình'}</small></span><Icon name="chevron" size={18} /></button>)}</section>}
      </> : <>
        <div className="history-summary"><span className="history-summary__icon"><Icon name="book" size={21} /></span><div><strong>{deliveries.length} giáo án đã nhận</strong><small>Giáo án được gửi đến hồ sơ trẻ có liên kết</small></div></div>
        {deliveries.map((delivery) => <button className="delivery-row" key={delivery.id} onClick={() => openDelivery(delivery)}><span className="lesson-icon lesson-icon--sage"><Icon name="book" size={19} /></span><span><strong>{delivery.title}</strong><small>{delivery.child} · {delivery.date} · {delivery.school}</small></span><Icon name="chevron" size={18} /></button>)}
      </>}
    </main>
  </>;

  const renderProfile = () => <>
    <PageHeader title="Hồ sơ gia đình" subtitle="Chọn hồ sơ cho câu chuyện" onBack={() => setScreen('home')} />
    <main className="subpage-content">
      <div className="profile-selection-hint">Hồ sơ đang chọn: <strong>{profiles.length ? selectedChild.name : 'Chưa có hồ sơ'}</strong></div>
      <section className="profile-list">{profiles.map((child) => <article className={`profile-card profile-card--editable ${selectedChildId === child.id ? 'is-selected' : ''}`} key={child.id}><button className="profile-card__select" onClick={() => { setSelectedChildId(child.id); setToast(`Đã chọn ${child.name}`); }} aria-pressed={selectedChildId === child.id}><ChildAvatar child={child} size="lg" /><span><strong>{child.name}</strong><small>{formatChildAge(child.ageMonths)} · {formatChildGender(child.gender)}</small></span><span className="radio-mark"><Icon name="check" size={14} /></span></button><button className="icon-button profile-edit" aria-label={`Xem hồ sơ ${child.name}`} onClick={() => { setDetailChildId(child.id); setScreen('child-detail'); }}><Icon name="chevron" size={19} /></button></article>)}<button className="add-profile" onClick={() => beginChildForm()}><span><Icon name="plus" size={19} /></span> Thêm hồ sơ trẻ</button></section>
      <div className="prototype-note">Thay đổi hồ sơ trong bản xem trước chỉ có hiệu lực trong phiên này.</div>
    </main>
  </>;

  const renderChildDetail = () => <>
    <PageHeader title="Hồ sơ của bé" subtitle="Thông tin do gia đình quản lý" onBack={() => setScreen('profile')} />
    <main className="subpage-content">
      <section className="child-detail-card"><ChildAvatar child={detailChild} size="lg" /><div><h2>{detailChild.name}</h2><p>{formatChildAge(detailChild.ageMonths)} · {formatChildGender(detailChild.gender)}</p></div></section>
      <div className="quota-row"><span>Biệt danh</span><strong>{detailChild.nickname || 'Chưa thêm'}</strong></div>
      <div className="child-detail-note"><span>Nhu cầu hỗ trợ</span><p>{detailChild.supportNeeds || 'Chưa thêm thông tin.'}</p></div>
      {profileContextFields.some((field) => detailChild[field.key]) && <section className="child-context-summary"><h3>Điều ba mẹ ghi nhận</h3>{profileContextFields.filter((field) => detailChild[field.key]).map((field) => <div key={field.key}><strong>{field.label}</strong><p>{detailChild[field.key]}</p></div>)}</section>}
      <div className="privacy-banner"><Icon name="lock" size={18} /><p>Thông tin độ tuổi của bé được áp dụng tự động khi tạo chuyện. Tên, ảnh hồ sơ và nhu cầu hỗ trợ không được gửi theo mặc định.</p></div>
      <div className="child-detail-actions">
        <button className="button button--primary button--wide" onClick={() => beginChildForm(detailChild)}><Icon name="edit" size={18} /> Sửa hồ sơ</button>
        <button className="button button--secondary button--wide" onClick={() => setPendingDeleteChildId(detailChild.id)}><Icon name="trash" size={18} /> Xóa hồ sơ mẫu</button>
      </div>
      <p className="prototype-note">Thông tin hồ sơ đang là dữ liệu mẫu trong phiên xem trước.</p>
    </main>
  </>;

  const renderPrivacy = () => <>
    <PageHeader title="Dữ liệu của bé" subtitle="Quyền riêng tư trong từng câu chuyện" onBack={() => setScreen('profile')} />
    <main className="subpage-content privacy-page">
      <section className="privacy-summary"><Icon name="lock" size={25} /><h2>Ba mẹ là người quyết định</h2><p>Thông tin hồ sơ chỉ thuộc tài khoản gia đình trong thiết kế mục tiêu.</p></section>
      <article><h3>Ngữ cảnh từ hồ sơ</h3><p>Độ tuổi và thông tin cơ bản của bé được áp dụng tự động từ hồ sơ đang chọn. Ảnh đại diện và ghi chú hỗ trợ riêng vẫn được giữ kín theo mặc định.</p></article>
      <article><h3>Chia sẻ với giáo viên</h3><p>Lời mời cần đúng tài khoản, phạm vi dữ liệu và sự đồng ý. Một lời mời đang chờ chưa cấp quyền xem.</p><button onClick={() => setScreen('sharing')}>Xem quyền chia sẻ <Icon name="arrow" size={17} /></button></article>
      <article><h3>Xóa hồ sơ và câu chuyện</h3><p>Trong bản thật, yêu cầu xóa cần thu hồi quyền ngay và theo dõi tiến trình xóa nội dung liên kết. Bản xem trước chỉ thao tác trên dữ liệu mẫu.</p></article>
      <p className="prototype-note">Các mô tả là mục tiêu thiết kế theo SRS; bản xem trước chưa đồng bộ dữ liệu hoặc xác minh quyền chia sẻ.</p>
    </main>
  </>;

  const renderGroupInvitations = () => <>
    <PageHeader title="Nhóm phụ huynh" subtitle="Lời mời từ trường hoặc lớp" onBack={() => setScreen('profile')} />
    <main className="subpage-content">
      <div className="privacy-banner"><Icon name="lock" size={18} /><p>Tham gia nhóm không tự động chia sẻ hồ sơ, tranh hay video của bé. Quyền chia sẻ với giáo viên được quản lý riêng.</p></div>
      {groupInvitations.filter((invitation) => invitation.status === 'pending').map((invitation) => <article className="invite-card" key={invitation.id}><span className="invite-card__icon"><Icon name="user" size={22} /></span><div><strong>{invitation.name}</strong><small>{invitation.school}</small></div><div className="invite-actions"><button className="button button--primary" onClick={() => { setGroupInvitations((current) => current.map((item) => item.id === invitation.id ? { ...item, status: 'accepted' } : item)); setToast('Đã tham gia nhóm trong bản xem trước.'); }}>Chấp nhận lời mời</button></div></article>)}
      {groupInvitations.filter((invitation) => invitation.status === 'accepted').map((invitation) => <article className="invite-card invite-card--accepted" key={invitation.id}><span className="invite-card__icon"><Icon name="check" size={22} /></span><div><strong>{invitation.name}</strong><small>{invitation.school} · Đã tham gia</small></div></article>)}
      {!groupInvitations.length && <div className="empty-state"><h2>Chưa có lời mời</h2><p>Lời mời từ trường sẽ xuất hiện ở đây.</p></div>}
      <p className="prototype-note">Trạng thái nhóm là dữ liệu mẫu, chưa gửi yêu cầu đến trường.</p>
    </main>
  </>;

  const submitChangePassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const error = !currentPassword ? 'Nhập mật khẩu hiện tại.' : newPassword.length < 6 || newPassword.length > 128 ? 'Mật khẩu mới cần từ 6 đến 128 ký tự.' : newPassword === currentPassword ? 'Hãy chọn mật khẩu khác mật khẩu hiện tại.' : confirmPassword !== newPassword ? 'Hai mật khẩu mới chưa khớp.' : '';
    setChangePasswordError(error);
    setChangePasswordNotice(error ? '' : 'Biểu mẫu hợp lệ. Bản xem trước chưa đổi mật khẩu trên Firebase.');
  };

  const renderChangePassword = () => <>
    <PageHeader title="Đổi mật khẩu" subtitle="Bảo vệ tài khoản gia đình" onBack={() => setScreen('profile')} />
    <main className="subpage-content"><form className="password-form" onSubmit={submitChangePassword} noValidate>
      <div className="privacy-banner"><Icon name="lock" size={18} /><p>Khi kết nối tài khoản thật, ba mẹ sẽ cần xác thực mật khẩu hiện tại trước khi cập nhật.</p></div>
      <label className="field-label" htmlFor="current-password">Mật khẩu hiện tại</label><input id="current-password" className="text-field" type={changePasswordVisible ? 'text' : 'password'} autoComplete="current-password" value={currentPassword} onChange={(event) => { setCurrentPassword(event.target.value); setChangePasswordError(''); setChangePasswordNotice(''); }} />
      <label className="field-label" htmlFor="new-password">Mật khẩu mới <span>6–128 ký tự</span></label><input id="new-password" className="text-field" type={changePasswordVisible ? 'text' : 'password'} autoComplete="new-password" value={newPassword} onChange={(event) => { setNewPassword(event.target.value); setChangePasswordError(''); setChangePasswordNotice(''); }} />
      <label className="field-label" htmlFor="confirm-password">Nhập lại mật khẩu mới</label><input id="confirm-password" className="text-field" type={changePasswordVisible ? 'text' : 'password'} autoComplete="new-password" value={confirmPassword} onChange={(event) => { setConfirmPassword(event.target.value); setChangePasswordError(''); setChangePasswordNotice(''); }} />
      <button type="button" className="password-visibility" onClick={() => setChangePasswordVisible((visible) => !visible)} aria-pressed={changePasswordVisible}><Icon name={changePasswordVisible ? 'eyeOff' : 'eye'} size={18} />{changePasswordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}</button>
      {changePasswordError && <p className="form-feedback form-feedback--error" role="alert">{changePasswordError}</p>}
      {changePasswordNotice && <p className="form-feedback" role="status">{changePasswordNotice}</p>}
      <button type="submit" className="button button--primary button--wide">Kiểm tra thông tin đổi mật khẩu</button>
    </form></main>
  </>;

  const renderActivities = () => {
    const lesson = availableLessons.find((item) => item.id === activityLessonId);
    const inPreVideoScript = activityOrigin === 'flow' && activeRun?.status !== 'ready';
    return <>
      <PageHeader title="Hoạt động cùng bé" subtitle={inPreVideoScript ? 'Chọn hoạt động gắn kèm trước khi tạo video' : 'Gắn kèm câu chuyện & thực hành cùng con'} onBack={() => setScreen(activityOrigin)} />
      <main className={`subpage-content activity-page ${kidView ? 'activity-page--kid' : ''}`}>
        {lesson ? <>
          <section className="activity-page__intro"><span className="activity-callout__icon"><Icon name="leaf" size={23} /></span><div><h2>{lesson.title}</h2><p>{lesson.activities.length} hoạt động từ giáo án {lesson.version}</p></div></section>
          <button type="button" className="kid-view-toggle" role="switch" aria-checked={kidView} onClick={() => setKidView((value) => !value)}><span><strong>Chế độ xem cùng bé</strong><small>Chữ lớn, dễ đọc hơn</small></span><span className={`switch ${kidView ? 'is-on' : ''}`}><i /></span></button>
          {lesson.activities.length ? lesson.activities.map((activity, index) => <article className={`activity-page__card ${selectedActivityId === activity.title ? 'is-selected' : ''}`} key={activity.title}><div className="activity-page__title"><span>{String(index + 1).padStart(2, '0')}</span><h3>{activity.title}</h3></div><div className="activity-page__detail"><strong>Chuẩn bị</strong><p>{activity.materials}</p></div><div className="activity-page__detail"><strong>Cùng làm</strong><p>{activity.instructions}</p></div><div className="activity-page__safety"><Icon name="lock" size={16} /><p>{activity.note}</p></div><button type="button" className="button button--secondary activity-page__select" onClick={() => { setSelectedActivityId(activity.title); setToast(`Đã chọn hoạt động “${activity.title}” cho bé.`); }} aria-pressed={selectedActivityId === activity.title}>{selectedActivityId === activity.title ? 'Đã chọn hoạt động này' : 'Chọn hoạt động này'}</button></article>) : <div className="empty-state"><h2>Chưa có hoạt động</h2><p>Ba mẹ vẫn có thể xem và hoàn tất câu chuyện.</p></div>}
          {inPreVideoScript && <button className="button button--primary button--wide" onClick={() => setScreen('flow')}>Tiếp tục duyệt kịch bản & tạo video <Icon name="arrow" size={18} /></button>}
          {activityOrigin === 'flow' && activeRun?.status === 'ready' && activeRun.lessonId === activityLessonId && <button className="button button--primary button--wide" onClick={() => openSessionFeedback(Number(activeRun.id))}>Hoàn tất · chia sẻ cảm nhận</button>}
          <p className="prototype-note">Hoạt động từ giáo án hiển thị cho phiên xem trước.</p>
        </> : <div className="empty-state"><h2>Giáo án không khả dụng</h2><p>Hãy quay lại câu chuyện để tiếp tục.</p><button className="button button--primary" onClick={() => setScreen(activityOrigin)}>Quay lại</button></div>}
      </main>
    </>;
  };

  const renderSessionFeedback = () => {
    const story = stories.find((item) => item.id === feedbackStoryId);
    const completingCurrentRun = activeRun?.id === String(feedbackStoryId);
    const ratingLabels = ['', 'Chưa hài lòng', 'Cần cải thiện', 'Bình thường', 'Hài lòng', 'Rất thích'];
    return <>
      <PageHeader title="Cảm nhận sau câu chuyện" subtitle={story?.title ?? 'Câu chuyện của gia đình'} onBack={() => setScreen(activeRun?.id === String(feedbackStoryId) ? 'flow' : 'run-detail')} />
      <main className="subpage-content session-feedback-page">
        <section className="session-feedback-hero"><span className="session-feedback-hero__spark"><Icon name="spark" size={27} /></span><h2>Hôm nay bé thấy thế nào?</h2><p>Ba mẹ chia sẻ cảm nhận sau khi xem. Có thể bỏ qua bước này.</p></section>
        <section className="session-feedback-card" aria-labelledby="session-rating-title"><h3 id="session-rating-title">Đánh giá câu chuyện</h3><div className="session-stars" role="group" aria-label="Chọn từ một đến năm sao">{[1, 2, 3, 4, 5].map((rating) => <button key={rating} type="button" className={sessionRating >= rating ? 'is-on' : ''} onClick={() => setSessionRating(rating)} aria-label={`${rating} sao`} aria-pressed={sessionRating === rating}><Icon name="star" size={29} /></button>)}</div><p className="session-rating-label" aria-live="polite">{sessionRating ? `${sessionRating}/5 · ${ratingLabels[sessionRating]}` : 'Chạm vào số sao phù hợp'}</p></section>
        <section className="session-feedback-card"><h3>Cảm nhận nhanh <span>Tùy chọn</span></h3><div className="session-tags">{quickSessionTags.map((tag) => <button key={tag} type="button" className={sessionTags.includes(tag) ? 'is-on' : ''} onClick={() => setSessionTags((current) => current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag])} aria-pressed={sessionTags.includes(tag)}>{sessionTags.includes(tag) && <Icon name="check" size={15} />}{tag}</button>)}</div><label className="field-label" htmlFor="session-feedback-note">Ghi chú thêm <span>Tùy chọn</span></label><textarea id="session-feedback-note" className="idea-field" rows={3} maxLength={500} value={sessionNote} onChange={(event) => setSessionNote(event.target.value)} placeholder="Điều bé thích hoặc mong muốn cải thiện..." /><div className="character-count">{sessionNote.length}/500</div></section>
        <button className="button button--primary button--wide" onClick={saveSessionFeedback} disabled={sessionRating === 0}>{completingCurrentRun ? 'Lưu đánh giá & hoàn tất' : 'Lưu đánh giá'}</button>
        <button className="button button--secondary button--wide" onClick={skipSessionFeedback}>{completingCurrentRun ? 'Bỏ qua & hoàn tất' : 'Bỏ qua'}</button>
        <p className="prototype-note">Đánh giá này chỉ lưu trong phiên xem trước; chưa gửi cho giáo viên. Phản hồi giáo án là một luồng riêng.</p>
      </main>
    </>;
  };

  const renderLibrary = () => <>
    <PageHeader title="Thư viện giáo án" subtitle="Bản công khai và nội dung được gửi đến gia đình" onBack={() => setScreen('home')} />
    <main className="subpage-content">
      <section className="library-child-switcher" aria-label="Hồ sơ trẻ đang xem"><ChildAvatar child={selectedChild} size="md"/><div><span>CHỌN HỒ SƠ CHO CÂU CHUYỆN</span><strong>{selectedChild.name}</strong><small>{formatChildAge(selectedChild.ageMonths)} · {formatChildGender(selectedChild.gender)}</small></div><select aria-label="Chọn hồ sơ trẻ" value={selectedChild.id} onChange={(event) => { setSelectedChildId(event.target.value); setToast('Đã đổi hồ sơ xem trong thư viện.'); }}><option value="" disabled>Chọn bé</option>{profiles.map((child) => <option key={child.id} value={child.id}>{child.name} · {formatChildGender(child.gender)}</option>)}</select></section>
      {activeRun && <button type="button" className="library-resume-card" onClick={() => { setStep(activeRun.step); setScreen('flow'); }}><span className="active-run-card__icon"><Icon name={activeRun.status === 'ready' ? 'play' : 'refresh'} size={18}/></span><span><strong>{activeRun.status === 'ready' ? 'Câu chuyện đã sẵn sàng' : 'Tiếp tục câu chuyện đang dở'}</strong><small>{steps.find((item) => item.key === activeRun.step)?.label ?? 'Đang xử lý'} · của {profiles.find((child) => child.id === activeRun.childId)?.name ?? 'bé'}</small></span><Icon name="arrow" size={18}/></button>}
      <button type="button" className="library-quota-summary" onClick={() => setScreen('quota')}><span><strong>2 lượt video</strong><small>Còn lại trong dữ liệu minh họa</small></span><span className="library-quota-meter"><i/></span><span>4 gợi ý vẽ</span><Icon name="chevron" size={17}/></button>
      <div className="library-tabs" role="tablist" aria-label="Nhóm giáo án"><button role="tab" aria-selected={libraryTab === 'public'} className={libraryTab === 'public' ? 'is-active' : ''} onClick={() => setLibraryTab('public')}>Giáo án công khai</button><button role="tab" aria-selected={libraryTab === 'shared'} className={libraryTab === 'shared' ? 'is-active' : ''} onClick={() => setLibraryTab('shared')}>Trường / giáo viên gửi</button></div>
      {libraryTab === 'public' ? <section className="library-group"><div className="library-group-heading"><span className="pill pill--green">HỆ THỐNG</span><p>Giáo án công khai có thể xem và dùng như preset.</p></div>{publicLessons.length ? publicLessons.map((lesson) => <article className="library-card" key={lesson.id}><button className="library-card-main" onClick={() => setLessonPreviewId(lesson.id)}><span className="library-card__art">{lesson.color === 'sky' ? <SkyLessonArt /> : <StoryArt variant="thumb" />}</span><span className="library-card__body"><strong>{lesson.title}</strong><small>{lesson.meta}</small><em>{lesson.version} · {lesson.visibility}</em></span><Icon name="chevron" size={18} /></button><button type="button" className="lesson-detail-action" onClick={() => setLessonPreviewId(lesson.id)}>Chi tiết</button></article>) : <p className="library-empty">Chưa có giáo án công khai trong bản xem trước.</p>}</section> : <section className="library-group"><div className="library-group-heading"><span className="pill pill--blue">ĐƯỢC CHIA SẺ</span><p>Giáo án từ trường hoặc giáo viên gửi riêng cho gia đình.</p></div>
        {lessonInvitations.some((invitation) => invitation.status === 'pending') && <section className="invite-section" aria-label="Lời mời giáo án"><div className="section-heading"><h2>Lời mời giáo án</h2><span className="pill pill--green">Mới</span></div>{lessonInvitations.filter((invitation) => invitation.status === 'pending').map((invitation) => { const lesson = lessons.find((item) => item.id === invitation.lessonId); return lesson && <article className="invite-card" key={invitation.id}><span className="invite-card__icon"><Icon name="book" size={22} /></span><div><strong>{lesson.title}</strong><small>{invitation.teacher} · {invitation.school}</small></div><div className="invite-actions"><button className="button button--primary" onClick={() => { setLessonInvitations((current) => current.map((item) => item.id === invitation.id ? { ...item, status: 'accepted' } : item)); setToast('Đã chấp nhận lời mời trong bản xem trước.'); }}>Chấp nhận</button><button className="button button--secondary" onClick={() => { setLessonInvitations((current) => current.map((item) => item.id === invitation.id ? { ...item, status: 'declined' } : item)); setToast('Đã từ chối lời mời trong bản xem trước.'); }}>Từ chối</button></div></article>; })}</section>}
        {sharedLessons.map((lesson) => <article className="library-card" key={lesson.id}><button className="library-card-main" onClick={() => setLessonPreviewId(lesson.id)}><span className="library-card__art"><StoryArt variant="thumb" /></span><span className="library-card__body"><strong>{lesson.title}</strong><small>{lesson.meta}</small><em>{lesson.version} · {lesson.visibility}</em></span><Icon name="chevron" size={18} /></button><button type="button" className="lesson-detail-action" onClick={() => setLessonPreviewId(lesson.id)}>Chi tiết</button></article>)}
      </section>}
      <p className="prototype-note">Thư viện và lời mời đang dùng dữ liệu mẫu; chưa đồng bộ tài khoản thật.</p>
    </main>
  </>;

  const renderLessonDetail = () => <>
     <PageHeader title="Chi tiết giáo án" subtitle={`${selectedLessonDetail.version} · ${selectedLessonDetail.visibility}`} onBack={() => setScreen(lessonDetailOrigin === 'delivery' ? 'delivery-detail' : 'library')} />
    <main className="subpage-content">
       <div className="preview-inline-note" role="note"><strong>Chi tiết giáo án minh họa</strong><span>Quyền truy cập và trạng thái phát hành bên dưới chỉ là minh họa.</span></div>
       <section className="lesson-detail-hero"><span className={`lesson-icon lesson-icon--${selectedLessonDetail.color}`}><Icon name="book" size={25} /></span><span className="pill pill--green">Trạng thái mẫu</span><h2>{selectedLessonDetail.title}</h2><p>{selectedLessonDetail.description}</p><small>Độ tuổi tham khảo: {selectedLessonDetail.ageTarget}</small></section>
       <div className="section-heading"><h2>Hoạt động trong giáo án</h2><span>{selectedLessonDetail.activities.length} hoạt động</span></div>
      {selectedLessonDetail.activities.map((activity, index) => <article className="activity-detail" key={activity.title}><span className="activity-number">{String(index + 1).padStart(2, '0')}</span><strong>{activity.title}</strong><small><b>Vật liệu:</b> {activity.materials}</small><p>{activity.instructions}</p><small><b>Lưu ý:</b> {activity.note}</small></article>)}
       <button className="button button--secondary button--wide" onClick={downloadLesson}><Icon name="download" size={18} /> Tải nội dung giáo án này</button>
       <button className="button button--primary button--wide" disabled={Boolean(activeRun)} onClick={() => { setPresetForNextRun(selectedLessonDetail.id); setScreen('home'); setToast('Đã chọn giáo án cho lần tạo tiếp theo.'); }}>Dùng giáo án cho câu chuyện</button>
       {activeRun && <div className="inline-note"><Icon name="refresh" size={16} /><span>Hoàn tất hoặc hủy câu chuyện hiện tại trước khi bắt đầu câu chuyện mới.</span></div>}
       <div className="inline-note"><Icon name="lock" size={16} /><span>Giáo án đã ngừng chia sẻ sẽ không mở được nội dung. Thông tin vẫn có thể xuất hiện trong lịch sử.</span></div>
    </main>
  </>;

  const renderDeliveryDetail = () => <>
    <PageHeader title="Giáo án đã nhận" subtitle={`${selectedDelivery.child} · ${selectedDelivery.date}`} onBack={() => { setHistoryTab('lessons'); setScreen('history'); }} />
    <main className="subpage-content">
       <section className="lesson-detail-hero"><small className="lesson-source">{selectedDelivery.school}</small><h2>{selectedDelivery.title}</h2><p>Được giao bởi {selectedDelivery.teacher} cho hồ sơ {selectedDelivery.child}.</p><small>Chi tiết theo phiên bản giáo án đã gửi</small></section>
       <button className="delivery-row" onClick={() => { setSelectedLessonDetailId(selectedDelivery.lessonId); setLessonDetailOrigin('delivery'); setScreen('lesson-detail'); }}><span className="lesson-icon lesson-icon--sage"><Icon name="book" size={19} /></span><span><strong>Xem nội dung giáo án</strong><small>{lessons.find((lesson) => lesson.id === selectedDelivery.lessonId)?.version ?? 'Phiên bản đã gửi'}</small></span><Icon name="chevron" size={18} /></button>
       <section className="reply-card"><h2 className="reply-card__title">Phản hồi giáo án</h2>{selectedDelivery.parentFeedback && <p><strong>Gia đình:</strong> {selectedDelivery.parentFeedback}</p>}<p><strong>{selectedDelivery.teacher}:</strong> {selectedDelivery.teacherReply ?? 'Chưa có phản hồi từ giáo viên.'}</p><small>Trao đổi gắn với giáo án này trong cùng trường.</small></section>
       <button className="button button--primary button--wide" onClick={() => { setFeedbackText(''); setScreen('feedback'); }}>Gửi phản hồi về giáo án</button>
      <div className="inline-note"><Icon name="lock" size={16} /><span>Đây không phải chat chung. Phản hồi không kèm ảnh đính kèm hoặc trạng thái hoàn thành.</span></div>
    </main>
  </>;

  const renderNotifications = () => <>
      <PageHeader title="Thông báo" subtitle="Cập nhật về câu chuyện và giáo án" onBack={() => setScreen('home')} />
    <main className="subpage-content">
      <div className="preview-inline-note" role="note"><strong>Thông báo minh họa</strong><span>Các thông báo bên dưới là nội dung minh họa.</span></div>
      <button className="link-button mark-all-read" onClick={() => setNotices((current) => current.map((notice) => ({ ...notice, read: true })))}>Đánh dấu đã đọc</button>
      {notices.length ? notices.map((notice) => <button className={`notice-row ${notice.read ? '' : 'is-unread'}`} key={notice.id} onClick={() => openNotice(notice)}><span className="notice-row__icon"><Icon name={notice.kind === 'feedback' ? 'message' : notice.kind === 'run' ? 'refresh' : 'play'} size={19} /></span><span><strong>{notice.title}</strong><small>{notice.body}</small><em>{notice.date}</em></span>{!notice.read && <i className="unread-dot" />}</button>) : <EmptyState title="Bạn đã xem hết thông báo" body="Khi có giáo án hoặc câu chuyện mới, cập nhật sẽ xuất hiện ở đây." action="Về trang chủ" onAction={() => setScreen('home')} />}
    </main>
  </>;

  const renderSharing = () => <>
    <PageHeader title="Chia sẻ hồ sơ" subtitle="Quản lý quyền truy cập của giáo viên" onBack={() => setScreen('profile')} />
    <main className="subpage-content">
      <div className="preview-inline-note" role="note"><strong>Quyền chia sẻ mẫu</strong><span>Lời mời và thu hồi chỉ đổi trạng thái trong phiên; chưa có grant thật được gửi hoặc thu hồi.</span></div>
      <button className="button button--primary button--wide" onClick={() => { setShareChildId(selectedChildId); setScreen('share-form'); }}>Mời giáo viên cụ thể</button>
      <div className="sharing-policy"><Icon name="lock" size={18} /><p>Lời mời chỉ có hiệu lực sau khi giáo viên chấp nhận. Ba mẹ có thể thu hồi quyền chia sẻ bất cứ lúc nào.</p></div>
      <div className="section-heading"><h2>Giáo viên & trường</h2><span>{grants.length} lời mời/quyền</span></div>
      {grants.map((grant) => <article className="grant-card" key={grant.id}><span className={`grant-status grant-status--${grant.status}`}>{grant.status === 'active' ? 'Đã chấp nhận · mẫu' : 'Đang chờ · mẫu'}</span><strong>{grant.recipient}</strong><small>{grant.organization} · {profiles.find((child) => child.id === grant.childId)?.name ?? 'Hồ sơ trẻ'}</small><small>{grant.date}</small>{grant.status === 'active' ? <button className="text-button" onClick={() => setPendingRevoke(grant.id)}>Thu hồi quyền mẫu</button> : <p>Chưa có quyền truy cập trước khi giáo viên chấp nhận.</p>}</article>)}
    </main>
  </>;

  const renderShareForm = () => <>
    <PageHeader title="Mời giáo viên" subtitle="Gửi lời mời cho một người cụ thể" onBack={() => setScreen('sharing')} />
    <main className="subpage-content">
      <label className="field-label" htmlFor="share-child">Hồ sơ trẻ</label><select id="share-child" className="text-field" value={shareChildId} onChange={(event) => setShareChildId(event.target.value)}>{profiles.map((child) => <option key={child.id} value={child.id}>{child.name}</option>)}</select>
      <label className="field-label" htmlFor="teacher-identity">Giáo viên mẫu</label><select id="teacher-identity" className="text-field" value={shareTeacherId} onChange={(event) => setShareTeacherId(event.target.value)}><option value="">Chọn giáo viên</option>{verifiedTeacherPreview.map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.name} · {teacher.school}</option>)}</select>
      <div className="sharing-policy"><Icon name="lock" size={18} /><p>Chỉ mời tài khoản giáo viên được hệ thống xác minh. Danh sách ở đây là mẫu; lời mời chưa gửi thật và chưa mở quyền xem hồ sơ.</p></div>
       <button className="button button--primary button--wide" onClick={sendShareInvite}>Tạo lời mời</button>
    </main>
  </>;

  const renderQuota = () => <>
    <PageHeader title="Lượt tạo" subtitle="Lượt tạo video và gợi ý vẽ của gia đình" onBack={() => setScreen('profile')} />
    <main className="subpage-content">
      <div className="preview-inline-note" role="note"><strong>Số liệu minh họa</strong><span>Các con số và gói bên dưới chỉ dựng trạng thái UI, chưa có quota hoặc Billing thật.</span></div>
      <section className="quota-card"><span className="quota-icon"><Icon name="spark" size={22} /></span><strong>Gia đình còn 2 lượt video</strong><p>Gói minh họa · chu kỳ tháng · làm mới theo thông tin tài khoản khi tích hợp.</p></section>
      <div className="quota-row"><span>Video câu chuyện</span><strong>2 / 5 lượt còn lại</strong></div><div className="quota-row"><span>Gói sử dụng</span><strong>Gia đình · minh họa</strong></div><div className="quota-row"><span>Gợi ý nét vẽ</span><strong>4 / 8 lượt còn lại</strong></div>
      <button className="button button--primary button--wide" onClick={() => setQuotaTopupOpen((open) => !open)} aria-expanded={quotaTopupOpen}>Xem lựa chọn nạp thêm</button>
      {quotaTopupOpen && <section className="quota-topup-preview"><h2>Lựa chọn thanh toán</h2><p>Chọn một phương thức để xem trạng thái mẫu. Không mở cổng thanh toán và không tạo giao dịch.</p><div><button type="button" onClick={() => setToast('MoMo · chưa mở thanh toán trong bản xem trước.')}>MoMo · xem thử</button><button type="button" onClick={() => setToast('VNPAY · chưa mở thanh toán trong bản xem trước.')}>VNPAY · xem thử</button></div></section>}
      <button className="button button--secondary button--wide" onClick={() => setToast('Lịch sử gói và hóa đơn chỉ hiển thị sau khi có dữ liệu thật.')}>Thông tin gói sử dụng</button>
    </main>
  </>;

  const renderFeedback = () => <>
    <PageHeader title="Phản hồi giáo án" subtitle={`${selectedDelivery.title} · ${selectedDelivery.teacher}`} onBack={() => setScreen('delivery-detail')} />
    <main className="subpage-content">
      <div className="feedback-context"><Icon name="message" size={19} /><span>Phản hồi được gắn với giáo án và lần giao cụ thể này.</span></div>
      <label className="field-label" htmlFor="feedback-message">Nội dung phản hồi <span>Không đính kèm ảnh</span></label><textarea id="feedback-message" className="idea-field" rows={5} maxLength={1000} value={feedbackText} onChange={(event) => setFeedbackText(event.target.value)} placeholder="Chia sẻ câu hỏi hoặc góp ý về giáo án..." />
      <div className="character-count">{feedbackText.length}/1000</div>
      <button className="button button--primary button--wide" onClick={submitFeedback}>Gửi phản hồi</button>
      <div className="preview-inline-note" role="note"><strong>Phản hồi chưa được gửi</strong><span>Nút lưu chỉ giữ bản nháp trong phiên xem trước; chưa được gửi đi.</span></div>
    </main>
  </>;

  const renderChildForm = () => <>
    <PageHeader title={childEditingId ? 'Sửa hồ sơ trẻ' : 'Thêm hồ sơ trẻ'} subtitle="Hồ sơ do Parent quản lý" onBack={() => setScreen('profile')} />
    <main className="subpage-content">
      <div className="privacy-banner"><Icon name="lock" size={18} /><p>Tên hiển thị và độ tuổi giúp ba mẹ quản lý hồ sơ. Biệt danh, nhu cầu hỗ trợ và ảnh không gửi cho AI theo mặc định.</p></div>
      <div className="child-photo-form"><ChildAvatar child={{ id: 'draft', name: childName || 'Trẻ', ageMonths: (Number(childAgeYears) || 0) * 12 + (Number(childAgeMonths) || 0), initial: childName.trim().slice(-1).toUpperCase() || '?', tone: 'peach', gender: childGender, photoUrl: childPhotoUrl ?? undefined }} size="lg" /><div><strong>Ảnh hồ sơ</strong><small>Một ảnh từ camera hoặc thư viện</small><div className="child-photo-actions"><button onClick={() => document.getElementById('child-camera')?.click()}>Chụp ảnh</button><button onClick={() => document.getElementById('child-gallery')?.click()}>Chọn ảnh</button></div></div><input id="child-camera" className="visually-hidden" type="file" accept="image/*" capture="user" onChange={handleChildPhoto} /><input id="child-gallery" className="visually-hidden" type="file" accept="image/*" onChange={handleChildPhoto} /></div>
      <label className="field-label" htmlFor="child-name">Tên hiển thị <span>Bắt buộc</span></label><input id="child-name" className="text-field" value={childName} onChange={(event) => setChildName(event.target.value)} placeholder="Ví dụ: Bé An" />
      <div className="age-fields"><div><label className="field-label" htmlFor="child-age-years">Tuổi <span>3–10</span></label><input id="child-age-years" className="text-field" inputMode="numeric" type="number" min="3" max="10" step="1" value={childAgeYears} onChange={(event) => setChildAgeYears(event.target.value)} placeholder="Số năm" /></div><div><label className="field-label" htmlFor="child-age-months">Tháng lẻ <span>0–11</span></label><input id="child-age-months" className="text-field" inputMode="numeric" type="number" min="0" max="11" step="1" value={childAgeMonths} onChange={(event) => setChildAgeMonths(event.target.value)} placeholder="Số tháng" /></div></div>
      <label className="field-label" htmlFor="child-gender">Giới tính <span>Tùy chọn</span></label><select id="child-gender" className="text-field" value={childGender} onChange={(event) => setChildGender(event.target.value as Child['gender'])}><option value="unspecified">Chưa chọn</option><option value="girl">Bé gái</option><option value="boy">Bé trai</option></select>
      <div className="preview-inline-note" role="note"><strong>Trường giới tính đang ở dạng UI mẫu</strong><span>Thuộc tính này chưa có trong SRS/API hiện hành và chỉ lưu trong phiên xem trước.</span></div>
      <label className="field-label" htmlFor="child-nickname">Biệt danh <span>Tùy chọn</span></label><input id="child-nickname" className="text-field" value={childNickname} onChange={(event) => setChildNickname(event.target.value)} placeholder="Chỉ lưu trong hồ sơ" />
      <details className="child-context-form"><summary>Thêm điều ba mẹ biết về bé <Icon name="chevron" size={17} /></summary><p>Những mục này chỉ lưu trong hồ sơ. Mỗi lần tạo chuyện, ba mẹ chọn riêng mục nào được dùng.</p>
        <label className="field-label" htmlFor="child-interests">Sở thích <span>Tùy chọn</span></label><textarea id="child-interests" className="idea-field" rows={2} maxLength={300} value={childInterests} onChange={(event) => setChildInterests(event.target.value)} placeholder="Ví dụ: thích quan sát bướm" />
        <label className="field-label" htmlFor="child-observations">Quan sát của ba mẹ <span>Tùy chọn</span></label><textarea id="child-observations" className="idea-field" rows={2} maxLength={300} value={childObservations} onChange={(event) => setChildObservations(event.target.value)} placeholder="Điều ba mẹ muốn ghi nhớ" />
        <label className="field-label" htmlFor="child-achievements">Điều bé đã làm được <span>Tùy chọn</span></label><textarea id="child-achievements" className="idea-field" rows={2} maxLength={300} value={childAchievements} onChange={(event) => setChildAchievements(event.target.value)} placeholder="Một mốc nhỏ của bé" />
        <label className="field-label" htmlFor="child-experiences">Trải nghiệm ngoài ứng dụng <span>Tùy chọn</span></label><textarea id="child-experiences" className="idea-field" rows={2} maxLength={300} value={childExperiences} onChange={(event) => setChildExperiences(event.target.value)} placeholder="Ví dụ: cùng gia đình trồng cây" />
      </details>
      <label className="field-label" htmlFor="child-support">Nhu cầu hỗ trợ <span>Tùy chọn · riêng tư</span></label><textarea id="child-support" className="idea-field" rows={3} value={childSupport} onChange={(event) => setChildSupport(event.target.value)} placeholder="Thông tin này không được dùng cho câu chuyện mặc định" />
      <button className="button button--primary button--wide" onClick={saveChild}>Lưu hồ sơ</button>
      <div className="preview-inline-note" role="note"><strong>Hồ sơ chỉ lưu trong phiên</strong><span>Ảnh hồ sơ và thông tin này chỉ ở trong phiên xem trước.</span></div>
    </main>
  </>;

  const renderStoryDetail = () => <>
    <PageHeader title="Câu chuyện của gia đình" subtitle={currentStory?.child ?? 'Hồ sơ trẻ'} onBack={() => setScreen('history')} />
    <main className="subpage-content">
      {currentStory && <>
        <div className="flow-intro"><h1>{currentStory.title}</h1><p>{currentStory.subtitle}</p></div>
        {renderVideoPreview(currentStory.subtitle)}
        <div className="private-badge"><Icon name="lock" size={15} /> Chỉ phát trực tuyến · không tải hoặc xuất video</div>
        {currentStory.lessonId && availableLessons.some((lesson) => lesson.id === currentStory.lessonId) && <button className="button button--secondary button--wide" onClick={() => openActivities(currentStory.lessonId!, 'run-detail')}><Icon name="leaf" size={18} /> Xem hoạt động cùng bé</button>}
        {activeRun?.needsRegeneration && <button className="button button--primary button--wide" onClick={() => { setStep(activeRun.step); setScreen('flow'); }}>Tiếp tục duyệt kịch bản để tạo lại</button>}
        {currentStory.status === 'ready' && !activeRun?.needsRegeneration && <button className="button button--primary button--wide" onClick={() => openSessionFeedback(currentStory.id)}>Hoàn tất · chia sẻ cảm nhận</button>}
        {currentStory.sessionFeedback ? <div className="saved-session-feedback"><Icon name="star" size={20} /><div><strong>Ba mẹ đã đánh giá {currentStory.sessionFeedback.rating}/5</strong><small>{[...currentStory.sessionFeedback.tags, currentStory.sessionFeedback.note].filter(Boolean).join(' · ') || 'Không có ghi chú thêm'}</small></div></div> : currentStory.status === 'completed' && <button className="button button--secondary button--wide" onClick={() => openSessionFeedback(currentStory.id)}><Icon name="star" size={18} /> Đánh giá câu chuyện</button>}
        <button className="button button--secondary button--wide" onClick={() => setPendingDelete(currentStory.id)}><Icon name="trash" size={17} /> Xóa câu chuyện</button>
        <p className="prototype-note">Video xem trước mang tính minh họa. Video thật cần hoàn tất kiểm tra trước khi phát.</p>
      </>}
    </main>
  </>;

  const submitAuthPreview = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(authEmail.trim());
    setAuthEmailError(emailValid ? '' : 'Nhập email hợp lệ để tiếp tục.');
    setAuthPasswordError(authPassword ? '' : 'Nhập mật khẩu để tiếp tục.');
    if (!emailValid || !authPassword) return;
    setAuthPreviewNotice('Đăng nhập chưa được kết nối. Thông tin bạn nhập không được gửi đi.');
  };

  const renderAuth = () => <main className="auth-screen">
    <AuthScene onBack={() => setScreen('profile')} backLabel="Quay lại hồ sơ" />
    <form className="auth-panel" onSubmit={submitAuthPreview} noValidate>
      <div className="auth-panel__heading"><span className="auth-panel__kicker">CHÀO MỪNG BA MẸ</span><h1>Chào mừng trở lại</h1><p>Tiếp tục những câu chuyện của gia đình.</p></div>
      <div className="auth-field">
        <label htmlFor="parent-email">Email</label>
        <div className={`auth-field__control ${authEmailError ? 'has-error' : ''}`}><Icon name="mail" size={19} /><input id="parent-email" type="email" inputMode="email" autoComplete="email" value={authEmail} onChange={(event) => { setAuthEmail(event.target.value); setAuthEmailError(''); setAuthPreviewNotice(''); }} placeholder="Email của ba mẹ" aria-invalid={Boolean(authEmailError)} aria-describedby={authEmailError ? 'auth-email-error' : undefined} /></div>
        {authEmailError && <small className="auth-field__error" id="auth-email-error">{authEmailError}</small>}
      </div>
      <div className="auth-field">
        <label htmlFor="parent-password">Mật khẩu</label>
        <div className={`auth-field__control ${authPasswordError ? 'has-error' : ''}`}><Icon name="lock" size={19} /><input id="parent-password" type={authPasswordVisible ? 'text' : 'password'} autoComplete="current-password" value={authPassword} onChange={(event) => { setAuthPassword(event.target.value); setAuthPasswordError(''); setAuthPreviewNotice(''); }} placeholder="Nhập mật khẩu" aria-invalid={Boolean(authPasswordError)} aria-describedby={authPasswordError ? 'auth-password-error' : undefined} /><button type="button" className="auth-password-toggle" onClick={() => setAuthPasswordVisible((visible) => !visible)} aria-label={authPasswordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}><Icon name={authPasswordVisible ? 'eyeOff' : 'eye'} size={19} /></button></div>
        {authPasswordError && <small className="auth-field__error" id="auth-password-error">{authPasswordError}</small>}
      </div>
      <div className="auth-options"><label className="auth-remember"><input type="checkbox" checked={authRemember} onChange={(event) => setAuthRemember(event.target.checked)} /><span>Ghi nhớ đăng nhập</span></label><button type="button" onClick={() => setScreen('recovery')}>Quên mật khẩu?</button></div>
      <button type="submit" className={`auth-submit ${authReady ? 'is-ready' : ''}`}>Đăng nhập <Icon name="arrow" size={19} /></button>
      {authPreviewNotice && <p className="auth-preview-result" role="status">{authPreviewNotice}</p>}
      <p className="auth-register">Chưa có tài khoản? <button type="button" onClick={() => setScreen('signup')}>Tạo tài khoản</button></p>
      <button className="auth-demo-link" type="button" onClick={() => setScreen('home')}>Xem thử ứng dụng</button>
      <p className="auth-preview-note">Bản xem trước chưa kết nối xác thực.</p>
    </form>
  </main>;

  const submitSignupPreview = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const errors = {
      email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signupEmail.trim()) ? '' : 'Nhập email hợp lệ.',
      password: signupPassword.length >= 6 && signupPassword.length <= 128 ? '' : 'Mật khẩu cần từ 6 đến 128 ký tự.',
      confirm: !signupConfirm ? 'Nhập lại mật khẩu.' : signupConfirm !== signupPassword ? 'Hai mật khẩu chưa khớp.' : '',
    };
    setSignupErrors(errors);
    if (Object.values(errors).some(Boolean)) { setSignupNotice(''); return; }
    setSignupNotice('Biểu mẫu đã hợp lệ. Bản xem trước chưa tạo tài khoản thật.');
  };

  const renderSignup = () => <main className="auth-screen auth-screen--signup">
    <AuthScene onBack={() => setScreen('auth')} backLabel="Quay lại đăng nhập" />
    <form className="auth-panel signup-panel" onSubmit={submitSignupPreview} noValidate>
      <div className="auth-panel__heading"><span className="auth-panel__kicker">DÀNH CHO BA MẸ</span><h1>Tạo tài khoản</h1><p>Lưu giữ câu chuyện riêng của gia đình.</p></div>
      <div className="auth-field">
        <label htmlFor="signup-email">Email</label>
        <div className={`auth-field__control ${signupErrors.email ? 'has-error' : ''}`}><Icon name="mail" size={19} /><input id="signup-email" type="email" inputMode="email" autoComplete="email" value={signupEmail} onChange={(event) => { setSignupEmail(event.target.value); setSignupErrors((errors) => ({ ...errors, email: '' })); setSignupNotice(''); }} onBlur={() => { if (signupEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signupEmail.trim())) setSignupErrors((errors) => ({ ...errors, email: 'Nhập email hợp lệ.' })); }} placeholder="Email của ba mẹ" aria-invalid={Boolean(signupErrors.email)} aria-describedby={signupErrors.email ? 'signup-email-error' : undefined} /></div>
        {signupErrors.email && <small className="auth-field__error" id="signup-email-error">{signupErrors.email}</small>}
      </div>
      <div className="auth-field">
        <label htmlFor="signup-password">Mật khẩu</label>
        <div className={`auth-field__control ${signupErrors.password ? 'has-error' : ''}`}><Icon name="lock" size={19} /><input id="signup-password" type={signupPasswordVisible ? 'text' : 'password'} autoComplete="new-password" value={signupPassword} onChange={(event) => { setSignupPassword(event.target.value); setSignupErrors((errors) => ({ ...errors, password: '', confirm: '' })); setSignupNotice(''); }} placeholder="Tạo mật khẩu" aria-invalid={Boolean(signupErrors.password)} aria-describedby={signupErrors.password ? 'signup-password-error' : undefined} /><button type="button" className="auth-password-toggle" onClick={() => setSignupPasswordVisible((visible) => !visible)} aria-label={signupPasswordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}><Icon name={signupPasswordVisible ? 'eyeOff' : 'eye'} size={19} /></button></div>
        {signupErrors.password && <small className="auth-field__error" id="signup-password-error">{signupErrors.password}</small>}
      </div>
      <div className="auth-field">
        <label htmlFor="signup-confirm">Nhập lại mật khẩu</label>
        <div className={`auth-field__control ${signupErrors.confirm ? 'has-error' : ''}`}><Icon name="lock" size={19} /><input id="signup-confirm" type={signupConfirmVisible ? 'text' : 'password'} autoComplete="new-password" value={signupConfirm} onChange={(event) => { setSignupConfirm(event.target.value); setSignupErrors((errors) => ({ ...errors, confirm: '' })); setSignupNotice(''); }} onBlur={() => { if (signupConfirm && signupConfirm !== signupPassword) setSignupErrors((errors) => ({ ...errors, confirm: 'Hai mật khẩu chưa khớp.' })); }} placeholder="Nhập lại mật khẩu" aria-invalid={Boolean(signupErrors.confirm)} aria-describedby={signupErrors.confirm ? 'signup-confirm-error' : undefined} /><button type="button" className="auth-password-toggle" onClick={() => setSignupConfirmVisible((visible) => !visible)} aria-label={signupConfirmVisible ? 'Ẩn mật khẩu nhập lại' : 'Hiện mật khẩu nhập lại'}><Icon name={signupConfirmVisible ? 'eyeOff' : 'eye'} size={19} /></button></div>
        {signupErrors.confirm && <small className="auth-field__error" id="signup-confirm-error">{signupErrors.confirm}</small>}
      </div>
      <button type="submit" className={`auth-submit signup-submit ${signupReady ? 'is-ready' : ''}`}>Tạo tài khoản <Icon name="arrow" size={19} /></button>
      {signupNotice && <p className="signup-notice" role="status"><Icon name="check" size={17} />{signupNotice}</p>}
      <p className="auth-register">Đã có tài khoản? <button type="button" onClick={() => setScreen('auth')}>Đăng nhập</button></p>
      <p className="auth-preview-note">Có thể thêm hồ sơ trẻ sau.</p>
    </form>
  </main>;

  const renderRecovery = () => <>
    <PageHeader title="Khôi phục tài khoản" subtitle="Lấy lại quyền truy cập tài khoản Parent" onBack={() => setScreen('auth')} />
    <main className="subpage-content"><div className="privacy-banner"><Icon name="lock" size={18} /><p>Nhập email đã đăng ký. Màn hình này không tiết lộ email có tài khoản hay không.</p></div><label className="field-label" htmlFor="recovery-email">Email tài khoản</label><input id="recovery-email" type="email" className="text-field" placeholder="you@example.com" /><button className="button button--primary button--wide" onClick={() => setToast('Chưa thể gửi liên kết khôi phục trong bản xem trước.')}>Gửi liên kết khôi phục</button><div className="prototype-note">Chưa thể gửi email khôi phục từ màn hình xem trước này.</div></main>
  </>;

  return <SettingsContext.Provider value={() => setShowSettings(true)}><div className="app-stage">
    <div className={`phone-shell ${screen === 'flow' ? 'phone-shell--flow' : ''} ${screen === 'home' ? 'phone-shell--home' : ''} ${['auth', 'signup'].includes(screen) ? 'phone-shell--auth' : ''}`}>
      <div className="android-status"><span className="android-status__time">9:41 <em className="android-preview-badge" aria-label="Chế độ xem thử">BẢN THỬ</em></span><span className="status-icons"><i className="signal-bars"><b /><b /><b /><b /></i><i className="wifi-icon" /><i className="battery-icon"><b /></i></span></div>
      {screen === 'home' && renderHome()}
      {screen === 'history' && renderHistory()}
      {screen === 'profile' && renderProfile()}
      {screen === 'child-detail' && renderChildDetail()}
      {screen === 'privacy' && renderPrivacy()}
      {screen === 'group-invitations' && renderGroupInvitations()}
      {screen === 'change-password' && renderChangePassword()}
      {screen === 'activities' && renderActivities()}
      {screen === 'session-feedback' && renderSessionFeedback()}
      {screen === 'library' && renderLibrary()}
      {screen === 'lesson-detail' && renderLessonDetail()}
      {screen === 'delivery-detail' && renderDeliveryDetail()}
      {screen === 'notifications' && renderNotifications()}
      {screen === 'sharing' && renderSharing()}
      {screen === 'share-form' && renderShareForm()}
      {screen === 'quota' && renderQuota()}
      {screen === 'feedback' && renderFeedback()}
      {screen === 'child-form' && renderChildForm()}
      {screen === 'run-detail' && renderStoryDetail()}
      {screen === 'auth' && renderAuth()}
      {screen === 'signup' && renderSignup()}
      {screen === 'recovery' && renderRecovery()}
      {screen === 'flow' && <>
        <header className="flow-header"><button className="back-button" onClick={() => step === 'generating' || step === 'ready' ? setScreen('home') : previousStep()} aria-label={step === 'generating' || step === 'ready' ? 'Về trang chủ, tiếp tục ở nền' : 'Quay lại bước trước'}><Icon name="back" size={22} /></button><span>{activeRun?.status === 'ready' ? 'Câu chuyện của gia đình' : 'Tạo câu chuyện'}</span><div className="flow-header__actions"><button className="icon-button flow-settings" onClick={() => setShowSettings(true)} aria-label="Mở cài đặt"><Icon name="settings" size={18} /></button><button className="close-flow" onClick={() => setScreen('home')} aria-label="Thu nhỏ luồng, tiếp tục ở nền"><Icon name="close" size={20} /></button></div></header>
        {step !== 'generating' && step !== 'ready' && <div className="progress-wrap"><div className="progress-label"><span>{flowSteps[stepIndex]?.label}</span><small>Bước {stepIndex + 1} / {flowSteps.length}</small></div><div className="step-progress" aria-label={`Bước ${stepIndex + 1} trên ${flowSteps.length}`}>{flowSteps.map((item, index) => <i key={item.key} className={index <= stepIndex ? 'is-done' : ''} />)}</div></div>}
        <main ref={flowContentRef} className={`flow-content flow-content--${step}`}>{renderFlowStep()}</main>
        {step !== 'generating' && step !== 'ready' && <div className="flow-footer"><button className="button button--primary button--wide" onClick={step === 'idea' && ideaMode === 'rewrite' ? submitRewrite : nextStep} disabled={(step === 'capture' && !photoUrl) || (step === 'review' && Boolean(selectedLesson && !scriptFollowing)) || (step === 'script' && Boolean(activeRun?.needsRegeneration && activeRun.regenCount >= 2))}>{step === 'script' ? activeRun?.needsRegeneration ? `Xem trước yêu cầu tạo lại (${Math.max(0, 2 - (activeRun?.regenCount ?? 0))} lượt còn)` : 'Duyệt kịch bản & tạo video' : step === 'capture' ? 'Tiếp tục với bức tranh' : step === 'idea' && ideaMode === 'rewrite' ? 'Gửi gợi ý viết lại' : step === 'guide' ? guideStepIndex < guideSteps.length - 1 ? 'Bước tiếp theo' : 'Tiếp tục đến chụp tranh' : 'Tiếp tục'} <Icon name="arrow" size={18} /></button></div>}
        {step === 'generating' && <div className="flow-footer flow-footer--ready"><button className="button button--secondary button--wide" onClick={() => { setStep('script'); setActiveRun((run) => run ? { ...run, step: 'script' } : run); }}>Quay lại kịch bản</button><button className="text-button text-button--center" onClick={() => setScreen('home')}>Về trang chủ</button></div>}
        {step === 'ready' && <div className="flow-footer flow-footer--ready"><button className="button button--secondary button--wide" onClick={() => { setScreen('home'); setToast('Bạn có thể quay lại câu chuyện từ Trang chủ trong phiên này.'); }}>Để sau trong phiên này <Icon name="clock" size={17} /></button></div>}
      </>}
      {!['flow', 'session-feedback', 'activities', 'auth', 'signup', 'recovery'].includes(screen) && <BottomNav active={(['history', 'delivery-detail'].includes(screen) ? 'history' : ['library', 'lesson-detail'].includes(screen) ? 'library' : ['profile', 'child-detail', 'privacy', 'group-invitations', 'change-password', 'sharing', 'share-form', 'quota', 'child-form'].includes(screen) ? 'profile' : 'home') as Screen} onSelect={selectScreen} onStart={startStory} />}
      {showSettings && <div className="scrim" role="presentation" onClick={() => setShowSettings(false)}><section className="settings-sheet" role="dialog" aria-modal="true" aria-labelledby="settings-title" onClick={(event) => event.stopPropagation()}><div className="sheet-handle"/><div className="sheet-top"><h2 id="settings-title">Cài đặt</h2><button className="icon-button" onClick={() => setShowSettings(false)} aria-label="Đóng"><Icon name="close"/></button></div>
        <button className="setting-option setting-option--button" role="switch" aria-checked={pushNotifications} onClick={() => setPushNotifications((value) => !value)}><span><strong>Thông báo câu chuyện</strong><small>Nhắc khi video đã sẵn sàng</small></span><span className={`switch ${pushNotifications ? 'is-on' : ''}`}><i/></span></button>
        <button className="setting-option setting-option--button" onClick={() => setToast('Bản xem trước hiện hỗ trợ tiếng Việt.')}><span><strong>Ngôn ngữ</strong><small>Tiếng Việt</small></span><Icon name="chevron"/></button>
        <div className="settings-shortcuts"><span>TÀI KHOẢN & QUYỀN RIÊNG TƯ</span><button onClick={() => { setShowSettings(false); setScreen('privacy'); }}>Dữ liệu và quyền riêng tư <Icon name="chevron" size={17}/></button><button onClick={() => { setShowSettings(false); setScreen('sharing'); }}>Chia sẻ hồ sơ với giáo viên <Icon name="chevron" size={17}/></button><button onClick={() => { setShowSettings(false); setScreen('group-invitations'); }}>Lời mời từ trường <Icon name="chevron" size={17}/></button><button onClick={() => { setShowSettings(false); setScreen('quota'); }}>Lượt tạo và gói sử dụng <Icon name="chevron" size={17}/></button><button onClick={() => { setShowSettings(false); setScreen('change-password'); }}>Đổi mật khẩu <Icon name="chevron" size={17}/></button></div>
        <div className="permission-copy"><Icon name="lock" size={15}/> Camera và micro chỉ được hỏi khi ba mẹ dùng chức năng tương ứng. Từ chối quyền không làm mất các luồng nhập bằng chữ hoặc chọn ảnh.</div><button className="button button--primary button--wide" onClick={() => setShowSettings(false)}>Đóng cài đặt</button></section></div>}
      {lessonPreview && <div className="scrim lesson-preview-scrim" role="presentation" onClick={() => setLessonPreviewId(null)}><section className="lesson-preview-sheet" role="dialog" aria-modal="true" aria-labelledby="lesson-preview-title" onClick={(event) => event.stopPropagation()}><div className="sheet-handle"/><div className="sheet-top"><div><span className="pill pill--green">{lessonPreview.visibility}</span><h2 id="lesson-preview-title">{lessonPreview.title}</h2><small>{lessonPreview.version} · {lessonPreview.ageTarget}</small></div><button className="icon-button" onClick={() => setLessonPreviewId(null)} aria-label="Đóng chi tiết giáo án"><Icon name="close"/></button></div><p className="lesson-preview-description">{lessonPreview.description}</p><div className="lesson-preview-activities"><h3>Hoạt động trong giáo án</h3>{lessonPreview.activities.map((activity, index) => <article key={activity.title}><b>{String(index + 1).padStart(2, '0')}</b><div><strong>{activity.title}</strong><small>Vật liệu: {activity.materials}</small><p>{activity.instructions}</p></div></article>)}</div>{activeRun && screen !== 'flow' && <p className="inline-note"><Icon name="refresh" size={16}/> Hoàn tất câu chuyện đang mở trước khi chọn giáo án khác.</p>}<button className="button button--primary button--wide" disabled={Boolean(activeRun && screen !== 'flow')} onClick={() => { if (screen === 'flow' && step === 'prepare') { setSelectedLessonId(lessonPreview.id); setShowLessonOptions(false); setScriptFollowing(null); setSelectedActivityId(lessonPreview.activities[0]?.title ?? null); setActiveRun((run) => run ? { ...run, lessonId: lessonPreview.id, scriptFollowing: null } : run); } else { setPresetForNextRun(lessonPreview.id); setScreen('home'); } setLessonPreviewId(null); setToast('Đã chọn giáo án trong bản xem trước.'); }}>{screen === 'flow' && step === 'prepare' ? 'Chọn giáo án' : 'Dùng giáo án cho câu chuyện'}</button><p className="prototype-note">Chi tiết này là dữ liệu minh họa cho giao diện.</p></section></div>}
      {mismatchModalOpen && <div className="scrim mismatch-preview-scrim" role="presentation" onClick={() => setMismatchModalOpen(false)}><section className="confirm-sheet mismatch-preview-sheet" role="dialog" aria-modal="true" aria-labelledby="mismatch-preview-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="refresh" size={20}/></span><span className="preview-state">ĐỐI CHIẾU GIÁO ÁN · XEM TRƯỚC</span><h2 id="mismatch-preview-title">Tranh bé đang mở ra hướng khác giáo án?</h2><p>Chủ thể “{subject}” chưa trùng hoàn toàn với giáo án “{selectedLesson?.title ?? 'đã chọn'}”. Ba mẹ muốn kể theo hướng nào? (Phân tích xem trước cục bộ.)</p><div className="mismatch-preview-options"><button type="button" className={mismatchDemoChoice === 'lesson' ? 'is-selected' : ''} onClick={() => setMismatchDemoChoice('lesson')} aria-pressed={mismatchDemoChoice === 'lesson'}><strong>Theo mục tiêu giáo án</strong><small>Giữ hướng học tập đã chọn.</small></button><button type="button" className={mismatchDemoChoice === 'free' ? 'is-selected' : ''} onClick={() => setMismatchDemoChoice('free')} aria-pressed={mismatchDemoChoice === 'free'}><strong>Để tranh dẫn dắt</strong><small>Ưu tiên cách kể riêng của bé.</small></button></div><button type="button" className="button button--primary button--wide" onClick={() => { setScriptFollowing(mismatchDemoChoice); setActiveRun((run) => run ? { ...run, scriptFollowing: mismatchDemoChoice } : run); setMismatchModalOpen(false); setToast('Đã áp dụng hướng kể trong bản xem trước.'); }}>Dùng lựa chọn này</button><button type="button" className="button button--secondary button--wide" onClick={() => setMismatchModalOpen(false)}>Đóng</button></section></div>}
      {recordingError && <div className="scrim" role="presentation" onClick={() => setRecordingError('')}><section className="confirm-sheet" role="alertdialog" aria-modal="true" aria-labelledby="microphone-error-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="mic" size={20}/></span><h2 id="microphone-error-title">Không thể tiếp tục với âm thanh</h2><p>{recordingError}</p><button className="button button--primary button--wide" onClick={() => setRecordingError('')}>Đã hiểu</button></section></div>}
      {pendingDelete !== null && <div className="scrim" role="presentation" onClick={() => setPendingDelete(null)}><section className="confirm-sheet" role="alertdialog" aria-modal="true" aria-labelledby="delete-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="trash" size={20} /></span><h2 id="delete-title">Xóa câu chuyện này?</h2><p>Câu chuyện cùng nội dung liên quan sẽ bị xóa khỏi lịch sử.</p><button className="button button--danger button--wide" onClick={() => removeStory(pendingDelete)}>Xóa câu chuyện</button><button className="button button--secondary button--wide" onClick={() => setPendingDelete(null)}>Giữ lại</button></section></div>}
      {pendingDeleteChildId && <div className="scrim" role="presentation" onClick={() => setPendingDeleteChildId(null)}><section className="confirm-sheet" role="alertdialog" aria-modal="true" aria-labelledby="delete-child-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="trash" size={20} /></span><h2 id="delete-child-title">Xóa hồ sơ của bé?</h2><p>Hồ sơ, câu chuyện, giáo án đã giao và lời mời liên quan sẽ biến mất khỏi phiên xem trước. Bản xem trước không thể xác nhận việc xóa trên hệ thống thật.</p><button className="button button--danger button--wide" disabled={activeRun?.childId === pendingDeleteChildId} onClick={() => removeChildPreview(pendingDeleteChildId)}>Xóa dữ liệu mẫu</button>{activeRun?.childId === pendingDeleteChildId && <small>Hãy hoàn tất hoặc hủy câu chuyện đang mở trước.</small>}<button className="button button--secondary button--wide" onClick={() => setPendingDeleteChildId(null)}>Giữ hồ sơ</button></section></div>}
      {pendingCancel && <div className="scrim" role="presentation" onClick={() => setPendingCancel(false)}><section className="confirm-sheet" role="alertdialog" aria-modal="true" aria-labelledby="cancel-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="close" size={20} /></span><h2 id="cancel-title">Hủy câu chuyện đang tạo?</h2><p>Câu chuyện hiện tại sẽ bị hủy. Ba mẹ có thể bắt đầu câu chuyện mới sau đó.</p><button className="button button--danger button--wide" onClick={cancelActiveRun}>Hủy câu chuyện</button><button className="button button--secondary button--wide" onClick={() => setPendingCancel(false)}>Tiếp tục làm</button></section></div>}
      {pendingRegenerate && <div className="scrim" role="presentation" onClick={() => setPendingRegenerate(false)}><section className="confirm-sheet" role="alertdialog" aria-modal="true" aria-labelledby="regen-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="refresh" size={20} /></span><h2 id="regen-title">Đưa câu chuyện về duyệt lại?</h2><p>Video hiện tại vẫn được giữ khi ba mẹ xem lại kịch bản. Video chỉ bị ẩn sau khi ba mẹ chấp nhận yêu cầu tạo lại. Còn {Math.max(0, 2 - (activeRun?.regenCount ?? 0))} lượt.</p><button className="button button--primary button--wide" onClick={beginRegeneration}>Xem lại kịch bản</button><button className="button button--secondary button--wide" onClick={() => setPendingRegenerate(false)}>Quay lại video</button></section></div>}
      {pendingRevoke && <div className="scrim" role="presentation" onClick={() => setPendingRevoke(null)}><section className="confirm-sheet" role="alertdialog" aria-modal="true" aria-labelledby="revoke-title" onClick={(event) => event.stopPropagation()}><span className="confirm-icon"><Icon name="lock" size={20} /></span><h2 id="revoke-title">Gỡ quyền mẫu?</h2><p>Thao tác này chỉ xóa fixture khỏi phiên xem trước. Quyền thật chưa bị thu hồi.</p><button className="button button--danger button--wide" onClick={() => { setGrants((current) => current.filter((grant) => grant.id !== pendingRevoke)); setPendingRevoke(null); setToast('Đã gỡ grant mẫu trong phiên xem trước.'); }}>Gỡ grant mẫu</button><button className="button button--secondary button--wide" onClick={() => setPendingRevoke(null)}>Giữ lại</button></section></div>}
      {toast && <div className="toast-message" role="status"><Icon name="check" size={17} />{toast}</div>}
      <div className="android-gesture" aria-hidden="true"><i /></div>
    </div>
  </div></SettingsContext.Provider>;
}

function BottomNav({ active, onSelect, onStart }: { active: Screen; onSelect: (screen: Screen) => void; onStart: () => void }) {
  const items: { key: Screen | 'start'; label: string; icon: IconName }[] = [
    { key: 'home', label: 'Trang chủ', icon: 'home' },
    { key: 'history', label: 'Lịch sử', icon: 'clock' },
    { key: 'start', label: 'Tạo mới', icon: 'plus' },
    { key: 'library', label: 'Giáo án', icon: 'book' },
    { key: 'profile', label: 'Hồ sơ', icon: 'user' },
  ];
  return <nav className="bottom-nav" aria-label="Điều hướng chính">{items.map((item) => item.key === 'start' ? <button key={item.key} className="bottom-nav__create" onClick={onStart} aria-label="Bắt đầu câu chuyện mới"><span className="bottom-nav__create-icon"><Icon name="plus" size={25}/></span><span>{item.label}</span></button> : <button key={item.key} className={active === item.key ? 'is-active' : ''} onClick={() => onSelect(item.key)} aria-current={active === item.key ? 'page' : undefined}><span className="bottom-nav__icon"><Icon name={item.icon} size={21} /></span><span>{item.label}</span></button>)}</nav>;
}

function PageHeader({ title, subtitle, onBack }: { title: string; subtitle: string; onBack: () => void }) {
  const openSettings = useContext(SettingsContext);
  return <header className="subpage-header"><button className="back-button" onClick={onBack} aria-label="Quay lại"><Icon name="back" size={22} /></button><div className="subpage-header__title"><h1>{title}</h1><p>{subtitle}</p></div>{openSettings && <button className="icon-button subpage-settings-button" onClick={openSettings} aria-label="Mở cài đặt"><Icon name="settings" size={20} /></button>}</header>;
}

function StoryRow({ story, large = false, profiles = children, onOpen, onDelete }: { story: Story; large?: boolean; profiles?: Child[]; onOpen: () => void; onDelete?: () => void }) {
  return <article className={`story-row ${large ? 'story-row--large' : ''}`}>
    <button className={`story-thumb story-thumb--${story.color}`} onClick={onOpen} aria-label={`Mở ${story.title}`}>{story.color === 'sea' ? <SeaStoryArt /> : <StoryArt variant="thumb" />}<span className="thumb-play"><Icon name="play" size={13} /></span></button>
    <button className="story-row__details" onClick={onOpen}><span className="story-row__top"><strong>{story.title}</strong><small>{story.date}</small></span><span className="story-row__subtitle">{story.subtitle}</span><span className="story-row__child"><ChildAvatar child={profiles.find((child) => child.id === story.childId) ?? profiles[0] ?? children[0]} size="sm" /> {story.child}</span></button>
    {onDelete && <button className="icon-button story-delete" onClick={onDelete} aria-label={`Xóa ${story.title}`}><Icon name="trash" size={17} /></button>}
  </article>;
}

function EmptyState({ title, body, action, onAction }: { title: string; body: string; action: string; onAction: () => void }) {
  return <div className="empty-state"><div className="empty-state__art"><StoryArt variant="thumb" /></div><h2>{title}</h2><p>{body}</p><button className="button button--primary" onClick={onAction}>{action} <Icon name="arrow" size={18} /></button></div>;
}

export default App;
