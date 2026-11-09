export interface TeacherLessonCard {
  id: string;
  title: string;
  version: string;
  versionHistory: string[];
  visibility: "Riêng tư" | "Trong trường" | "Công khai";
  publicReviewStatus: "Bản nháp" | "Chờ duyệt công khai" | "Đã duyệt công khai" | "Yêu cầu chỉnh sửa";
  updatedAt: string;
  ageBand: string;
  topic: string;
  description: string;
  objectives: string;
  activities: string[];
  approvedForSession?: boolean;
  remixedFrom?: string;
  authorName?: string;
}

export interface ClassRosterRow {
  id: string;
  displayLabel: string;
  ageMonths: number;
  ageText: string;
  profileShared: boolean;
  consentAccepted: boolean;
  className: string;
  enrollmentStatus: "ACTIVE" | "TRANSFERRED_HISTORY" | "DELETE_PENDING" | "DELETED";
  interests: string[];
  learningNotes: string;
  supportNeedsNote: string;
  previousClassHistory?: string;
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
  consentState: "Đã đồng ý" | "Đang chờ phụ huynh" | "Đã rút Consent";
  expiresAt: string;
  status: "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi";
}

export interface TeacherFeedbackItem {
  id: string;
  sender: string;
  lessonTitle: string;
  text: string;
  date: string;
}

export interface TeacherAssignedClassInfo {
  id: string;
  className: string;
  ageRangeLabel: string;
  studentCount: number;
  rbacState: "ACTIVE" | "TRANSFER_PENDING" | "SUSPENDED_READONLY" | "UNASSIGNED_403";
  ownerTeacher: string;
  pendingTargetTeacher?: string;
  hasActiveRunConflict?: boolean;
}

export interface TeacherNotificationItem {
  id: string;
  category: "OCCURRENCE" | "VIDEO_JOB" | "FEEDBACK" | "GRANT_CONSENT" | "CLASS_RBAC";
  title: string;
  body: string;
  timestamp: string;
  unread: boolean;
  targetRoute: string;
}

export interface PresentationAuditEntry {
  id: string;
  timestamp: string;
  teacherName: string;
  className: string;
  occurrenceId: string;
  scriptRevision: number;
  tokenSummary: string;
}

export interface OrgQuotaLedgerItem {
  id: string;
  date: string;
  runTitle: string;
  bucket: "Gói trường hàng tháng" | "Gói mua thêm (FIFO)" | "Trước khi nhận job";
  delta: string;
  note: string;
}

export const INITIAL_ASSIGNED_CLASSES: TeacherAssignedClassInfo[] = [
  {
    id: "cls-mam-2",
    className: "Lớp Mầm 2",
    ageRangeLabel: "4–5 tuổi (36–120 th)",
    studentCount: 24,
    rbacState: "ACTIVE",
    ownerTeacher: "Cô Thảo",
  },
  {
    id: "cls-choi-1",
    className: "Lớp Chồi 1",
    ageRangeLabel: "5–6 tuổi (36–120 th)",
    studentCount: 22,
    rbacState: "TRANSFER_PENDING",
    ownerTeacher: "Cô Thảo",
    pendingTargetTeacher: "Cô Mai",
    hasActiveRunConflict: true,
  },
  {
    id: "cls-la-3",
    className: "Lớp Lá 3",
    ageRangeLabel: "5–6 tuổi (36–120 th)",
    studentCount: 20,
    rbacState: "SUSPENDED_READONLY",
    ownerTeacher: "Cô Thảo",
  },
  {
    id: "cls-mam-1",
    className: "Lớp Mầm 1",
    ageRangeLabel: "3–4 tuổi (36–120 th)",
    studentCount: 18,
    rbacState: "UNASSIGNED_403",
    ownerTeacher: "Cô Lan",
  },
];

export const INITIAL_TEACHER_LESSONS: TeacherLessonCard[] = [
  {
    id: "les-butterfly-v3",
    title: "Vòng đời bướm",
    version: "Bản 3",
    versionHistory: ["Bản 1 (20/10/2026)", "Bản 2 (25/10/2026)", "Bản 3 (30/10/2026 · Đang dùng)"],
    visibility: "Trong trường",
    publicReviewStatus: "Đã duyệt công khai",
    updatedAt: "30/10/2026",
    ageBand: "4–5 tuổi (48–59 tháng)",
    topic: "Con bướm",
    description:
      "Bài học khám phá thiên nhiên giúp trẻ quan sát sự biến đổi kỳ diệu từ trứng, chú sâu nhỏ ăn lá xanh, kén nhộng trên cành đến chú bướm mùa xuân bay quanh sân trường.",
    objectives:
      "Nhận biết 4 giai đoạn phát triển của bướm, rèn kỹ năng quan sát đối xứng hai bên cánh và vẽ bướm màu sáp trên giấy A4.",
    activities: [
      "Hoạt động 1: Quan sát tranh & mô hình 4 giai đoạn vòng đời bướm",
      "Hoạt động 2: Dạo vườn trường tìm chiếc lá xanh và chú sâu nhỏ",
      "Hoạt động 3: Vẽ đôi cánh bướm mùa xuân đối xứng trên giấy A4",
      "Hoạt động 4: Kể chuyện chú bướm nhỏ cùng các bạn trong lớp",
    ],
    approvedForSession: true,
    authorName: "Cô Nguyễn Phương Thảo",
  },
  {
    id: "les-tree-v1",
    title: "Cây xanh quanh lớp",
    version: "Bản 1",
    versionHistory: ["Bản 1 (30/10/2026 · Bản gốc)"],
    visibility: "Riêng tư",
    publicReviewStatus: "Bản nháp",
    updatedAt: "30/10/2026",
    ageBand: "4–5 tuổi (48–59 tháng)",
    topic: "Cây xanh",
    description:
      "Trẻ làm quen với các bộ phận của cây xanh (rễ, thân, cành, tán lá, hoa quả) và hiểu vai trò của cây che bóng mát cho sân chơi của lớp.",
    objectives:
      "Phân biệt thân cây, cành lá, phối hợp màu xanh lá – nâu đất để vẽ tán cây xanh quanh lớp và hình thành thói quen chăm tưới cây.",
    activities: [
      "Hoạt động 1: Chạm và cảm nhận vỏ cây, chiếc lá ngoài sân trường",
      "Hoạt động 2: Trò chơi ghép hình rễ – thân – tán lá xanh",
      "Hoạt động 3: Vẽ cây xanh sân trường trên giấy A4 theo bảng hướng dẫn 16:9",
    ],
    approvedForSession: false,
    authorName: "Cô Nguyễn Phương Thảo",
  },
  {
    id: "les-rain-v2",
    title: "Hạt mưa mùa xuân",
    version: "Bản 2",
    versionHistory: ["Bản 1 (12/10/2026)", "Bản 2 (28/10/2026)"],
    visibility: "Công khai",
    publicReviewStatus: "Đã duyệt công khai",
    updatedAt: "28/10/2026",
    ageBand: "5–6 tuổi (60–83 tháng)",
    topic: "Mây và mưa",
    description:
      "Khám phá hiện tượng mây trắng, mây xám và những hạt mưa mùa xuân tưới mát vườn hoa qua thí nghiệm trực quan và hoạt động vẽ sáng tạo.",
    objectives:
      "Hiểu vòng tuần hoàn đơn giản của nước, luyện nét cong vẽ đám mây bồng bềnh và nét xiên vẽ hạt mưa tưới mát cây cối.",
    activities: [
      "Hoạt động 1: Thí nghiệm nhỏ chiếc cốc mây mưa vui nhộn",
      "Hoạt động 2: Vận động theo nhạc bài hát Cho tôi đi làm mưa với",
      "Hoạt động 3: Vẽ đám mây bồng bềnh và hạt mưa mùa xuân trên giấy vẽ",
      "Hoạt động 4: Kể câu chuyện hạt mưa đi du lịch quanh vườn hoa",
    ],
    approvedForSession: false,
    authorName: "Cô Lê Thu Hà",
  },
  {
    id: "les-ocean-v1",
    title: "Đàn cá nhỏ dưới đại dương",
    version: "Bản 2",
    versionHistory: ["Bản 1 (15/10/2026)", "Bản 2 (29/10/2026 · Đã kiểm duyệt)"],
    visibility: "Công khai",
    publicReviewStatus: "Đã duyệt công khai",
    updatedAt: "29/10/2026",
    ageBand: "3–4 tuổi (36–47 tháng)",
    topic: "Đại dương",
    description:
      "Chuyến du hành dưới đáy biển xanh giúp trẻ làm quen với đàn cá nhỏ, sao biển, rong biển và rạn san hô rực rỡ\u00A0sắc\u00A0màu.",
    objectives:
      "Nhận biết hình dáng chú cá (thân bầu dục, vây, đuôi), tập vẽ đường lượn sóng biển và tô màu đàn cá bơi theo đàn.",
    activities: [
      "Hoạt động 1: Khám phá tranh đại dương và gọi tên các loài sinh vật biển",
      "Hoạt động 2: Vẽ chú cá nhỏ và những gợn sóng biển xanh",
      "Hoạt động 3: Trò chơi vận động đàn cá bơi theo nhịp vỗ tay của cô",
    ],
    approvedForSession: false,
    authorName: "Cô Phạm Minh Châu",
  },
];

export const PUBLIC_LIBRARY_TEMPLATES: TeacherLessonCard[] = [
  ...INITIAL_TEACHER_LESSONS.map((l) => ({
    ...l,
    visibility: "Công khai" as const,
    publicReviewStatus: "Đã duyệt công khai" as const,
  })),
  {
    id: "tpl-sunflower-v1",
    title: "Vườn hoa hướng dương đón nắng",
    version: "Bản chuẩn",
    versionHistory: ["Bản chuẩn (26/10/2026 · Thư viện Sketch2Life)"],
    visibility: "Công khai",
    publicReviewStatus: "Đã duyệt công khai",
    updatedAt: "26/10/2026",
    ageBand: "4–5 tuổi (48–59 tháng)",
    topic: "Bông hoa",
    description:
      "Bài học mỹ thuật kết hợp khám phá ánh nắng mặt trời và những bông hoa hướng dương xoay cánh vàng rực rỡ trong khu vườn nhỏ.",
    objectives:
      "Luyện vẽ hình tròn làm nhụy hoa, xếp đều các cánh hoa xung quanh và phối hợp gam màu ấm vàng – cam – xanh lá.",
    activities: [
      "Hoạt động 1: Quan sát bông hoa hướng dương thật và đếm cánh hoa",
      "Hoạt động 2: Vẽ nhụy hoa tròn, cánh hoa xòe đều và chiếc lá răng cưa",
      "Hoạt động 3: Trưng bày góc nghệ thuật Vườn hoa lớp em",
    ],
    approvedForSession: false,
    authorName: "Tổ chuyên môn Mầm non Ánh Dương",
  },
];

export const INITIAL_ROSTER: ClassRosterRow[] = [
  {
    id: "roster-minh",
    displayLabel: "Bé Minh · 5 tuổi",
    ageMonths: 60,
    ageText: "60 tháng · 5 tuổi",
    profileShared: true,
    consentAccepted: true,
    className: "Lớp Mầm 2",
    enrollmentStatus: "ACTIVE",
    interests: ["Thích vẽ động vật", "Màu sắc tươi sáng", "Khám phá thiên nhiên"],
    learningNotes: "Hào hứng với các bài học có hoạt động quan sát ngoài vườn trường và kể chuyện.",
    supportNeedsNote: "Nhắc bé nghỉ mắt sau 10 phút nhìn màn hình (Loại khỏi ngữ cảnh AI).",
  },
  {
    id: "roster-ha",
    displayLabel: "Bé H.A · 5 tuổi",
    ageMonths: 58,
    ageText: "58 tháng · 4 tuổi",
    profileShared: true,
    consentAccepted: true,
    className: "Lớp Mầm 2",
    enrollmentStatus: "ACTIVE",
    interests: ["Cây xanh", "Kể chuyện", "Màu nước"],
    learningNotes: "Thích phối hợp màu xanh lá và màu vàng khi vẽ phong cảnh sân trường.",
    supportNeedsNote: "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
  },
  {
    id: "roster-tm",
    displayLabel: "Bé T.M · 4 tuổi",
    ageMonths: 52,
    ageText: "52 tháng · 4 tuổi",
    profileShared: false,
    consentAccepted: false,
    className: "Lớp Mầm 2",
    enrollmentStatus: "ACTIVE",
    interests: ["Vẽ hình khối", "Đàn cá nhỏ"],
    learningNotes: "Bé tập trung tốt khi có bảng hướng dẫn từng nét rõ ràng.",
    supportNeedsNote: "Ngồi bàn đầu để nhìn rõ bảng chiếu 16:9 (Loại khỏi ngữ cảnh AI).",
  },
  {
    id: "roster-khang",
    displayLabel: "Bé Gia Khang · 5 tuổi",
    ageMonths: 64,
    ageText: "64 tháng · 5 tuổi",
    profileShared: true,
    consentAccepted: true,
    className: "Lớp Chồi 1",
    enrollmentStatus: "ACTIVE",
    interests: ["Vũ trụ", "Khủng long", "Màu sáp dầu"],
    learningNotes: "Thích đặt câu hỏi vì sao và kể lại câu chuyện theo bức tranh tự vẽ.",
    supportNeedsNote: "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
  },
  {
    id: "roster-linh",
    displayLabel: "Bé Bảo Linh · 5 tuổi",
    ageMonths: 66,
    ageText: "66 tháng · 5 tuổi",
    profileShared: true,
    consentAccepted: true,
    className: "Lớp Chồi 1",
    enrollmentStatus: "ACTIVE",
    interests: ["Bông hoa", "Cầu vồng", "Âm nhạc"],
    learningNotes: "Nét vẽ mềm mại, hay giúp các bạn cùng bàn chọn màu.",
    supportNeedsNote: "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
  },
  {
    id: "roster-nam",
    displayLabel: "Bé Hải Nam · 6 tuổi",
    ageMonths: 72,
    ageText: "72 tháng · 6 tuổi",
    profileShared: true,
    consentAccepted: true,
    className: "Lớp Lá 3",
    enrollmentStatus: "ACTIVE",
    interests: ["Mây và mưa", "Thuyền buồm"],
    learningNotes: "Hoàn thành bài vẽ nhanh và thích thuyết trình trước lớp.",
    supportNeedsNote: "Mặc định loại khỏi ngữ cảnh AI (BR-20).",
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
    recipient: "Nhóm giáo viên Khối Mẫu giáo",
    scope: "Giáo án: Vòng đời bướm · Bản 3 (Quyền xem & Remix nội bộ)",
    consentState: "Đã đồng ý",
    expiresAt: "30/11/2026",
    status: "Đang hiệu lực",
  },
  {
    id: "tg-lesson-2",
    kind: "LESSON",
    recipient: "Cô Mai · Lớp Chồi 1",
    scope: "Giáo án: Cây xanh quanh lớp · Bản 1 (Quyền dạy thay buổi sáng)",
    consentState: "Đã đồng ý",
    expiresAt: "15/11/2026",
    status: "Đang hiệu lực",
  },
  {
    id: "tg-lesson-3",
    kind: "LESSON",
    recipient: "Tổ chuyên môn Khối Lá",
    scope: "Giáo án: Hạt mưa mùa xuân · Bản 1",
    consentState: "Đã rút Consent",
    expiresAt: "15/10/2026",
    status: "Đã thu hồi",
  },
];

export const INITIAL_TEACHER_FEEDBACK: TeacherFeedbackItem[] = [
  {
    id: "tfb-1",
    sender: "Tổ chuyên môn · Trường Mầm non Ánh Dương",
    lessonTitle: "Vòng đời bướm · Bản 3",
    text: "Giáo án có cấu trúc 4 hoạt động rõ ràng, phù hợp chuẩn an toàn lứa tuổi 4–5 tuổi.",
    date: "30/10/2026 08:45",
  },
  {
    id: "tfb-2",
    sender: "Cô Thảo · Trường Mầm non Ánh Dương",
    lessonTitle: "Vòng đời bướm · Bản 3",
    text: "Em đã bổ sung bước quan sát lá cây ngoài vườn trường trước khi vào giờ vẽ 16:9.",
    date: "30/10/2026 09:10",
  },
];

export const INITIAL_TEACHER_NOTIFICATIONS: TeacherNotificationItem[] = [
  {
    id: "tnotif-1",
    category: "OCCURRENCE",
    title: "Giáo án 'Vòng đời bướm · Bản 3' đã được duyệt công khai",
    body: "Quản lý trường đã xác nhận giáo án đạt chuẩn sư phạm và an toàn nội dung.",
    timestamp: "15 phút trước",
    unread: true,
    targetRoute: "/t02-lesson-authoring",
  },
  {
    id: "tnotif-2",
    category: "GRANT_CONSENT",
    title: "Quyền chia sẻ giáo án cho Khối Mẫu giáo đang hiệu lực",
    body: "Nhóm giáo viên Khối Mẫu giáo đã có thể xem và sử dụng 'Vòng đời bướm · Bản 3'.",
    timestamp: "1 giờ trước",
    unread: true,
    targetRoute: "/t02-lesson-authoring",
  },
  {
    id: "tnotif-3",
    category: "VIDEO_JOB",
    title: "Video mẫu 'Vòng đời bướm' sẵn sàng trình chiếu",
    body: "Video mẫu của buổi học #occ-20261030 đã vượt qua kiểm duyệt an toàn (VIDEO_READY).",
    timestamp: "2 giờ trước",
    unread: false,
    targetRoute: "/t07-video-presentation-confirmation",
  },
  {
    id: "tnotif-4",
    category: "CLASS_RBAC",
    title: "Bàn giao Lớp Chồi 1 đang chờ đóng run xung đột",
    body: "Quản lý trường yêu cầu bàn giao Lớp Chồi 1 sang Cô Mai (2-Owner Reassignment Saga).",
    timestamp: "Hôm qua",
    unread: false,
    targetRoute: "/t05-classes-and-children",
  },
];

export const INITIAL_PRESENTATION_AUDIT: PresentationAuditEntry[] = [
  {
    id: "aud-1",
    timestamp: "28/10/2026 09:30",
    teacherName: "Cô Thảo",
    className: "Lớp Mầm 2",
    occurrenceId: "occ-20261028",
    scriptRevision: 1,
    tokenSummary: "jwt:proj_98a1...3c (TTL 15 phút · Nội bộ lớp)",
  },
];

export const INITIAL_ORG_QUOTA_LEDGER: OrgQuotaLedgerItem[] = [
  {
    id: "org-led-1",
    date: "30/10/2026 09:20",
    runTitle: "Video mẫu Lớp Mầm 2 · Vòng đời bướm (Bản #1)",
    bucket: "Gói trường hàng tháng",
    delta: "-1 lượt",
    note: "VIDEO_READY · Chiếm vĩnh viễn 1 suất mẫu của buổi học (SAMPLE_USED)",
  },
  {
    id: "org-led-2",
    date: "27/10/2026 14:10",
    runTitle: "Video mẫu Lớp Mầm 2 · Cây xanh (Bị lỗi dịch vụ trước khi phát)",
    bucket: "Gói trường hàng tháng",
    delta: "-1 lượt",
    note: "FAILED · Trừ 1 lượt tổ chức nhưng KHÔNG mất suất mẫu của buổi học (SAMPLE_AVAILABLE)",
  },
  {
    id: "org-led-3",
    date: "25/10/2026 10:05",
    runTitle: "Yêu cầu bị từ chối ở bước kiểm tra đầu vào",
    bucket: "Trước khi nhận job",
    delta: "0 lượt",
    note: "Chưa nhận job nên không trừ quota tổ chức và không mất suất mẫu",
  },
];
