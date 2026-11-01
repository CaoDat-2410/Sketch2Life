export interface TeacherLessonCard {
  id: string;
  title: string;
  version: string;
  visibility: "Bản nháp" | "Trong trường" | "Công khai";
  updatedAt: string;
  ageBand: string;
  topic: string;
  objectives: string;
}

export interface ClassRosterRow {
  id: string;
  displayLabel: string;
  ageMonths: number;
  ageText: string;
  profileShared: boolean;
  className: string;
}

export interface SampleSceneItem {
  index: number;
  title: string;
  narration: string;
}

export interface TeacherGrantRow {
  id: string;
  kind: "LESSON" | "CHILD_PROFILE";
  recipient: string;
  scope: string;
  expiresAt: string;
  status: "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi";
}

export interface TeacherFeedbackItem {
  id: string;
  sender: "Phụ huynh bé Minh" | "Cô Thảo · Trường Mầm non Ánh Dương";
  text: string;
  date: string;
}

export const INITIAL_TEACHER_LESSONS: TeacherLessonCard[] = [
  {
    id: "les-butterfly-v3",
    title: "Vòng đời bướm",
    version: "Bản 3",
    visibility: "Trong trường",
    updatedAt: "30/10/2026",
    ageBand: "4–5 tuổi (Mẫu giáo)",
    topic: "Con bướm",
    objectives: "Nhận biết 4 giai đoạn phát triển của bướm và vẽ bướm màu sáp trên giấy.",
  },
  {
    id: "les-tree-v1",
    title: "Cây xanh quanh lớp",
    version: "Bản 1",
    visibility: "Bản nháp",
    updatedAt: "30/10/2026",
    ageBand: "4–5 tuổi (Mẫu giáo)",
    topic: "Cây xanh",
    objectives: "Quan sát lá cây trong sân trường và vẽ tán cây.",
  },
];

export const INITIAL_ROSTER: ClassRosterRow[] = [
  {
    id: "roster-minh",
    displayLabel: "Minh · 5 tuổi",
    ageMonths: 60,
    ageText: "60 tháng",
    profileShared: true,
    className: "Lớp Mầm 2",
  },
  {
    id: "roster-ha",
    displayLabel: "Bé H.A · 5 tuổi",
    ageMonths: 58,
    ageText: "58 tháng",
    profileShared: false,
    className: "Lớp Mầm 2",
  },
  {
    id: "roster-tm",
    displayLabel: "Bé T.M · 4 tuổi",
    ageMonths: 52,
    ageText: "52 tháng",
    profileShared: false,
    className: "Lớp Mầm 2",
  },
];

export const INITIAL_SAMPLE_SCENES: SampleSceneItem[] = [
  {
    index: 1,
    title: "Cảnh 1 · Chú sâu nhỏ trên lá xanh",
    narration: "Sáng sớm ở vườn trường, chú sâu nhỏ bò trên chiếc lá non.",
  },
  {
    index: 2,
    title: "Cảnh 2 · Kén nhỏ dưới cành cây",
    narration: "Chú sâu nằm yên trong chiếc kén ấm áp chờ ngày thay áo mới.",
  },
  {
    index: 3,
    title: "Cảnh 3 · Đôi cánh bướm màu sáp",
    narration: "Từ chiếc kén, chú bướm mang đôi cánh màu sáp của Minh bay lên.",
  },
  {
    index: 4,
    title: "Cảnh 4 · Dạo chơi quanh vườn trường",
    narration: "Bướm bay qua khóm hoa vàng trong sân Lớp Mầm 2.",
  },
  {
    index: 5,
    title: "Cảnh 5 · Cùng các bạn ra sân quan sát",
    narration: "Chú bướm vẫy cánh mời các bạn nhỏ cùng ra vườn tìm hiểu thiên nhiên.",
  },
];

export const INITIAL_TEACHER_GRANTS: TeacherGrantRow[] = [
  {
    id: "tg-lesson-1",
    kind: "LESSON",
    recipient: "Nhóm phụ huynh Lớp Mầm 2",
    scope: "Giáo án: Vòng đời bướm · Bản 3",
    expiresAt: "30/11/2026",
    status: "Đang hiệu lực",
  },
  {
    id: "tg-lesson-2",
    kind: "LESSON",
    recipient: "Nhóm giáo viên Khối Mẫu giáo",
    scope: "Giáo án: Cây xanh quanh lớp · Bản 1",
    expiresAt: "15/11/2026",
    status: "Đang chờ",
  },
  {
    id: "tg-lesson-3",
    kind: "LESSON",
    recipient: "Nhóm phụ huynh Lớp Mầm 1",
    scope: "Giáo án: Vòng đời bướm · Bản 2",
    expiresAt: "15/10/2026",
    status: "Đã thu hồi",
  },
  {
    id: "tg-profile-1",
    kind: "CHILD_PROFILE",
    recipient: "Cô Thảo · Lớp Mầm 2",
    scope: "Hồ sơ trẻ: Minh · 5 tuổi (60 tháng)",
    expiresAt: "31/05/2027",
    status: "Đang hiệu lực",
  },
  {
    id: "tg-profile-2",
    kind: "CHILD_PROFILE",
    recipient: "Cô Thảo · Lớp Mầm 2",
    scope: "Lời mời chia sẻ hồ sơ: Bé H.A · 5 tuổi",
    expiresAt: "15/11/2026",
    status: "Đang chờ",
  },
];

export const INITIAL_TEACHER_FEEDBACK: TeacherFeedbackItem[] = [
  {
    id: "tfb-1",
    sender: "Phụ huynh bé Minh",
    text: "Bé thích phần quan sát cánh bướm và về nhà đã vẽ thêm 2 chú bướm vàng.",
    date: "30/10/2026",
  },
  {
    id: "tfb-2",
    sender: "Cô Thảo · Trường Mầm non Ánh Dương",
    text: "Cô sẽ chuẩn bị thêm hoạt động quan sát lá cây ngoài vườn trường vào buổi tới nhé.",
    date: "30/10/2026",
  },
];
