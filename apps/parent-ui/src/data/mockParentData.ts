export interface SceneItem {
  index: number;
  title: string;
  narration: string;
  durationSec: number;
}

export interface LessonCardItem {
  id: string;
  title: string;
  ageBand: string;
  summary: string;
  topic: string;
  tags: string[];
  coverKind: "butterfly" | "tree";
  knowledgePoints: {
    icon: string;
    title: string;
    text: string;
  }[];
  drawingSteps: {
    step: number;
    title: string;
    hint: string;
  }[];
  outdoorActivities: {
    id: string;
    title: string;
    materials: string;
    firstStep: string;
    safetyNote?: string;
  }[];
}

export interface ChildProfileItem {
  id: string;
  displayName: string;
  ageMonths: number;
  ageLabel: string;
  ageGroup: string;
  interests: string[];
  learningNotes: string;
  supportNeedsNote: string;
  consentAccepted: boolean;
  consentUpdatedAt: string;
  archived?: boolean;
  deletionStatus?: "ACTIVE" | "DELETE_PENDING" | "DELETED";
}

export interface AccessGrantItem {
  id: string;
  kind: "LESSON" | "CHILD_PROFILE";
  recipient: string;
  scope: string;
  expiresAt: string;
  status: "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi" | "Đã từ chối";
  updatedAt: string;
}

export interface VideoJobSpecimen {
  id: string;
  title: string;
  date: string;
  status:
    | "Đang kiểm tra đầu vào"
    | "Đang xếp hàng"
    | "Đang tạo video"
    | "Đang kiểm tra video"
    | "Đang đối soát trạng thái"
    | "Video chưa thể hiển thị"
    | "Tạo video thất bại"
    | "Hoàn thành";
  badgeTone: "warn" | "info" | "off" | "err" | "ok";
  description: string;
  quotaNote: string;
  actionLabel?: "Tạo lại" | "Xem video";
}

export interface QuotaLedgerEntry {
  id: string;
  date: string;
  runTitle: string;
  sourceBucket: "Lượt định kỳ" | "Lượt mua thêm (FIFO)" | "Trước khi nhận job" | "Nạp thêm (Top-up)";
  delta: string;
  outcome: string;
  tone: "ok" | "warn" | "err" | "info";
}

export interface ParentNotificationItem {
  id: string;
  category: "REMINDER_144H" | "AUTOCLOSE_168H" | "TEACHER_INVITE" | "VIDEO_JOB" | "QUOTA_PAYMENT";
  title: string;
  body: string;
  timestamp: string;
  unread: boolean;
  targetPath: string;
  actionLabel: string;
}

export interface RunHistoryRecord {
  id: string;
  title: string;
  childName: string;
  ageLabel: string;
  date: string;
  lifecycleState: "COMPLETED" | "VIDEO_READY_144H" | "ABANDONED_168H" | "DELETE_PENDING" | "DELETED";
  idleHours: number;
  scriptRevision: number;
  regenUsed: number;
  note: string;
}

export const INITIAL_PROFILES: ChildProfileItem[] = [
  {
    id: "child-minh",
    displayName: "Bé Minh",
    ageMonths: 60,
    ageLabel: "5 tuổi (60 tháng)",
    ageGroup: "36–120 tháng · Mẫu giáo (4–5 tuổi)",
    interests: ["Thích vẽ động vật", "Màu sắc tươi sáng", "Khám phá thiên nhiên"],
    learningNotes: "Bé hào hứng khi quan sát côn trùng và thích nghe câu chuyện có nhịp điệu vui tươi.",
    supportNeedsNote: "Cần nhắc bé nghỉ mắt sau 10 phút nhìn màn hình (Mặc định loại khỏi ngữ cảnh AI).",
    consentAccepted: true,
    consentUpdatedAt: "30/10/2026 08:30",
    archived: false,
    deletionStatus: "ACTIVE",
  },
  {
    id: "child-an",
    displayName: "Bé An",
    ageMonths: 48,
    ageLabel: "4 tuổi (48 tháng)",
    ageGroup: "36–120 tháng · Mầm (3–4 tuổi)",
    interests: ["Cây cối", "Kể chuyện"],
    learningNotes: "Thích vẽ lá cây và tô màu xanh lá.",
    supportNeedsNote: "Không gửi ghi chú riêng sang mô hình tạo kịch bản.",
    consentAccepted: true,
    consentUpdatedAt: "25/10/2026 09:15",
    archived: false,
    deletionStatus: "ACTIVE",
  },
];

export const INITIAL_LESSONS: LessonCardItem[] = [
  {
    id: "lesson-butterfly",
    title: "Vòng đời bướm",
    ageBand: "4–5 tuổi (36–120 tháng)",
    summary: "Cùng bé quan sát hành trình từ trứng nhỏ, sâu bướm, kén nhộng thành chú bướm nhiều màu sắc.",
    topic: "Con bướm",
    tags: ["Tự nhiên", "Sáng tạo", "Khám phá"],
    coverKind: "butterfly",
    knowledgePoints: [
      {
        icon: "🥚",
        title: "Trứng và sâu nhỏ",
        text: "Bướm bắt đầu từ trứng nhỏ trên chiếc lá xanh rồi nở thành sâu bướm.",
      },
      {
        icon: "🌿",
        title: "Kén nhộng ấm áp",
        text: "Sâu bướm ăn lá lớn lên và cuộn mình nghỉ ngơi trong chiếc kén nhộng.",
      },
      {
        icon: "🦋",
        title: "Đôi cánh rực rỡ",
        text: "Từ kén nhộng, chú bướm xòe đôi cánh đầy màu sắc bay lên bầu trời.",
      },
    ],
    drawingSteps: [
      { step: 1, title: "Vẽ trứng", hint: "Chấm tròn nhỏ trên chiếc lá xanh" },
      { step: 2, title: "Vẽ sâu bướm", hint: "Nối các vòng tròn nhỏ thành thân sâu" },
      { step: 3, title: "Vẽ nhộng", hint: "Hình bầu dục nhỏ treo dưới cành cây" },
      { step: 4, title: "Vẽ bướm", hint: "Thân giữa và bốn cánh rộng rực rỡ" },
    ],
    outdoorActivities: [
      {
        id: "act-butterfly-1",
        title: "Quan sát vòng đời bướm ngoài vườn",
        materials: "Vật liệu: Sổ tay, bút màu, kính lúp nhựa trẻ em",
        firstStep: "Bước 1: Tìm bướm hoặc lá cây có sâu bướm ở vườn, công viên.",
        safetyNote: "Không chạm tay trực tiếp vào sâu hoặc côn trùng lạ; luôn có người lớn đi cùng.",
      },
      {
        id: "act-butterfly-2",
        title: "Nhật ký sắc màu cánh bướm",
        materials: "Vật liệu: Sổ tay, bút sáp màu",
        firstStep: "Bước 1: Vẽ lại màu cánh bướm và những chiếc lá bé quan sát được.",
        safetyNote: "Chọn khu vực sân phẳng, râm mát.",
      },
    ],
  },
  {
    id: "lesson-tree",
    title: "Cây xanh quanh em",
    ageBand: "4–5 tuổi (36–120 tháng)",
    summary: "Tìm hiểu rễ, thân, lá và vẽ cây xanh tỏa bóng mát ngoài sân vườn.",
    topic: "Cây xanh",
    tags: ["Tự nhiên", "Khám phá"],
    coverKind: "tree",
    knowledgePoints: [
      {
        icon: "🌱",
        title: "Mầm cây từ hạt",
        text: "Hạt nhỏ nảy mầm khi có đất ẩm, ánh nắng và nước tưới mỗi ngày.",
      },
      {
        icon: "🌳",
        title: "Thân và tán lá",
        text: "Thân cây vững chãi nâng đỡ những chiếc lá xanh đón ánh mặt trời.",
      },
      {
        icon: "🍃",
        title: "Bóng mát sân vườn",
        text: "Cây xanh cho bóng mát và là ngôi nhà của chim chóc, bướm nhỏ.",
      },
    ],
    drawingSteps: [
      { step: 1, title: "Vẽ mặt đất", hint: "Một nét ngang nhẹ ở cuối trang giấy" },
      { step: 2, title: "Vẽ thân cây", hint: "Hai nét dọc thẳng vươn lên cao" },
      { step: 3, title: "Vẽ tán lá", hint: "Đường lượn sóng tròn như đám mây xanh" },
      { step: 4, title: "Vẽ hoa và quả", hint: "Tô điểm thêm lá non và quả chín" },
    ],
    outdoorActivities: [
      {
        id: "act-tree-1",
        title: "Quan sát lá cây quanh nhà",
        materials: "Vật liệu: Sổ tay, bút sáp màu",
        firstStep: "Bước 1: Tìm 2–3 chiếc lá rụng có hình dáng khác nhau ngoài sân.",
        safetyNote: "Rửa tay sạch sau khi nhặt lá rụng.",
      },
      {
        id: "act-tree-2",
        title: "In vân lá lên giấy",
        materials: "Vật liệu: Giấy trắng, bút sáp màu",
        firstStep: "Bước 1: Đặt lá dưới trang giấy và tô nhẹ để hiện đường gân lá.",
        safetyNote: "Chọn lá khô ráo, sạch sẽ.",
      },
    ],
  },
];

export const INITIAL_SCENES: SceneItem[] = [
  {
    index: 1,
    title: "Cảnh 1 · Chú sâu nhỏ trên chiếc lá",
    narration: "Sáng sớm trong khu vườn, chú sâu nhỏ bò chậm rãi trên chiếc lá xanh mướt\u00A0đẫm\u00A0sương.",
    durationSec: 12,
  },
  {
    index: 2,
    title: "Cảnh 2 · Chiếc kén ấm áp",
    narration: "Chú sâu cuộn mình trong chiếc kén nhỏ dưới cành cây và nghỉ ngơi thật yên bình.",
    durationSec: 12,
  },
  {
    index: 3,
    title: "Cảnh 3 · Đôi cánh rực rỡ mở ra",
    narration: "Từ chiếc kén, chú bướm có đôi cánh màu sáp rực rỡ nhẹ nhàng xòe cánh đón nắng.",
    durationSec: 12,
  },
  {
    index: 4,
    title: "Cảnh 4 · Chuyến bay qua khóm hoa",
    narration: "Bướm nhỏ bay lượn qua những bông hoa vàng trong vườn cùng làn gió mát.",
    durationSec: 12,
  },
  {
    index: 5,
    title: "Cảnh 5 · Lời chào khu vườn",
    narration: "Bướm vẫy đôi cánh nhiều màu sắc, hẹn gặp lại khu vườn trong những ngày\u00A0nắng\u00A0đẹp.",
    durationSec: 12,
  },
];

export const INITIAL_GRANTS: AccessGrantItem[] = [
  {
    id: "grant-lesson-1",
    kind: "LESSON",
    recipient: "Nhóm phụ huynh Lớp Mầm 2",
    scope: "Giáo án: Vòng đời bướm · Bản 3 (Cô Thảo chia sẻ)",
    expiresAt: "30/11/2026",
    status: "Đang hiệu lực",
    updatedAt: "30/10/2026",
  },
  {
    id: "grant-lesson-2",
    kind: "LESSON",
    recipient: "Cô Mai · Trường Mầm non Ánh Dương",
    scope: "Giáo án: Cây xanh quanh em · Bản 1",
    expiresAt: "15/11/2026",
    status: "Đang chờ",
    updatedAt: "30/10/2026",
  },
  {
    id: "grant-profile-1",
    kind: "CHILD_PROFILE",
    recipient: "Cô Thảo · Trường Mầm non Ánh Dương (Lớp Mầm 2)",
    scope: "Hồ sơ bé: Minh · 60 tháng (Không gồm ghi chú hỗ trợ riêng)",
    expiresAt: "31/05/2027",
    status: "Đang hiệu lực",
    updatedAt: "30/10/2026",
  },
  {
    id: "grant-profile-2",
    kind: "CHILD_PROFILE",
    recipient: "Cô Lan · Trường Mầm non Ánh Dương (Lớp Chồi 1)",
    scope: "Lời mời chia sẻ hồ sơ bé Minh cho học kỳ mới",
    expiresAt: "15/11/2026",
    status: "Đang chờ",
    updatedAt: "30/10/2026",
  },
  {
    id: "grant-profile-3",
    kind: "CHILD_PROFILE",
    recipient: "Lớp Hè Khám Phá 2026",
    scope: "Hồ sơ bé: Minh · 60 tháng",
    expiresAt: "31/08/2026",
    status: "Đã thu hồi",
    updatedAt: "30/10/2026",
  },
];

export const UI07_VIDEO_JOBS: VideoJobSpecimen[] = [
  {
    id: "job-0",
    title: "Bông hoa mặt trời",
    date: "30/10/2026",
    status: "Đang kiểm tra đầu vào",
    badgeTone: "info",
    description: "Kiểm tra điều kiện quota & khóa run trước khi nhận job (ADMISSION_PENDING).",
    quotaNote: "Nếu từ chối ở bước này: 0 lượt bị trừ.",
  },
  {
    id: "job-1",
    title: "Chuyến du hành vũ trụ",
    date: "30/10/2026",
    status: "Đang xếp hàng",
    badgeTone: "warn",
    description: "Job đã được chấp nhận vào hàng đợi xử lý (QUEUED · Hạn tối đa 6 giờ).",
    quotaNote: "Đã giữ 1 lượt định kỳ trong tháng.",
  },
  {
    id: "job-2",
    title: "Khủng long phiêu lưu",
    date: "30/10/2026",
    status: "Đang tạo video",
    badgeTone: "info",
    description: "AI đang dựng các cảnh và lồng tiếng từ kịch bản đã xác nhận (GENERATING).",
    quotaNote: "Đã tính 1 lượt.",
  },
  {
    id: "job-3",
    title: "Chú cá dưới biển",
    date: "30/10/2026",
    status: "Đang kiểm tra video",
    badgeTone: "info",
    description: "Kiểm tra an toàn hình ảnh, âm thanh và phụ đề trước khi mở quyền xem (SAFETY_VALIDATING).",
    quotaNote: "Đã tính 1 lượt.",
  },
  {
    id: "job-3b",
    title: "Đàn kiến chăm chỉ",
    date: "30/10/2026",
    status: "Đang đối soát trạng thái",
    badgeTone: "warn",
    description: "Đang đồng bộ trạng thái với dịch vụ tạo video (AWAITING_RECONCILIATION).",
    quotaNote: "Không tạo bản ghi trùng lặp.",
  },
  {
    id: "job-4",
    title: "Ngôi nhà mơ ước",
    date: "30/10/2026",
    status: "Video chưa thể hiển thị",
    badgeTone: "off",
    description: "Bị chặn bởi bộ lọc an toàn (SAFETY_BLOCKED). Quyền phát bị khóa hoàn toàn.",
    quotaNote: "Lượt đã nhận vẫn được tính (không hoàn lại).",
  },
  {
    id: "job-5",
    title: "Chiếc xe màu đỏ",
    date: "30/10/2026",
    status: "Tạo video thất bại",
    badgeTone: "err",
    description: "Lỗi dịch vụ hoặc quá thời hạn 6 giờ (FAILED / SERVICE_ERROR).",
    quotaNote: "Lượt đã nhận vẫn được tính.",
    actionLabel: "Tạo lại",
  },
  {
    id: "job-6",
    title: "Chuyến bay của bướm",
    date: "30/10/2026",
    status: "Hoàn thành",
    badgeTone: "ok",
    description: "Video đã vượt qua kiểm duyệt an toàn và sẵn sàng phát (VIDEO_READY).",
    quotaNote: "Đã trừ 1 lượt định kỳ.",
    actionLabel: "Xem video",
  },
];

export const INITIAL_QUOTA_LEDGER: QuotaLedgerEntry[] = [
  {
    id: "led-1",
    date: "30/10/2026 09:40",
    runTitle: "Vòng đời bướm · Bản kịch bản #1",
    sourceBucket: "Lượt định kỳ",
    delta: "-1 định kỳ",
    outcome: "Đã nhận job & tạo video thành công (VIDEO_READY)",
    tone: "ok",
  },
  {
    id: "led-2",
    date: "29/10/2026 10:00",
    runTitle: "Gói bổ sung +3 lượt (MoMo #MM98241)",
    sourceBucket: "Nạp thêm (Top-up)",
    delta: "+3 mua thêm",
    outcome: "Lượt mua thêm giữ qua kỳ, dùng theo FIFO sau khi hết lượt định kỳ",
    tone: "ok",
  },
  {
    id: "led-3",
    date: "28/10/2026 20:10",
    runTitle: "Bầu trời sao (Hủy trước khi nhận job)",
    sourceBucket: "Trước khi nhận job",
    delta: "0 lượt",
    outcome: "Đang có 1 run khác chưa đóng (409 Conflict — không trừ lượt)",
    tone: "info",
  },
  {
    id: "led-4",
    date: "26/10/2026 16:05",
    runTitle: "Chiếc xe màu đỏ · Bản kịch bản #1",
    sourceBucket: "Lượt mua thêm (FIFO)",
    delta: "-1 mua thêm",
    outcome: "Lỗi dịch vụ sau khi đã nhận job (FAILED — không hoàn lượt)",
    tone: "err",
  },
  {
    id: "led-5",
    date: "24/10/2026 19:15",
    runTitle: "Ngôi nhà mơ ước · Bản kịch bản #2",
    sourceBucket: "Lượt định kỳ",
    delta: "-1 kỳ trước",
    outcome: "Đã nhận job nhưng bị chặn an toàn (SAFETY_BLOCKED — không hoàn lượt)",
    tone: "warn",
  },
];

export const INITIAL_NOTIFICATIONS: ParentNotificationItem[] = [
  {
    id: "notif-1",
    category: "REMINDER_144H",
    title: "Nhắc hạn 144h: Buổi học đang chờ xác nhận",
    body: "Buổi học 'Cây xanh quanh em' của Minh đã tạm dừng 144 giờ (6 ngày). Nếu không tiếp tục trong 24 giờ tới, hệ thống sẽ tự đóng ở mốc 168 giờ.",
    timestamp: "10 phút trước",
    unread: true,
    targetPath: "/p09-history-feedback",
    actionLabel: "Xem & Xử lý",
  },
  {
    id: "notif-2",
    category: "TEACHER_INVITE",
    title: "Lời mời chia sẻ hồ sơ trẻ từ Cô Lan",
    body: "Cô Lan (Lớp Chồi 1 · Trường Mầm non Ánh Dương) gửi lời mời kết nối hồ sơ của Minh cho học kỳ mới.",
    timestamp: "1 giờ trước",
    unread: true,
    targetPath: "/p13-settings",
    actionLabel: "Xem lời mời",
  },
  {
    id: "notif-3",
    category: "VIDEO_JOB",
    title: "Video 'Chuyến bay của bướm' đã sẵn sàng",
    body: "Video đã vượt qua bước kiểm tra an toàn và mở hoạt động ngoài trời cho bé.",
    timestamp: "2 giờ trước",
    unread: false,
    targetPath: "/p08-video-and-activities",
    actionLabel: "Mở video",
  },
  {
    id: "notif-4",
    category: "AUTOCLOSE_168H",
    title: "Tự đóng sau 168h không tương tác",
    body: "Buổi học 'Chú cá nhỏ' ở trạng thái chờ duyệt kịch bản quá 168 giờ đã tự chuyển sang ABANDONED để giải phóng khóa tạo bài mới.",
    timestamp: "Hôm qua",
    unread: false,
    targetPath: "/p09-history-feedback",
    actionLabel: "Xem lịch sử",
  },
  {
    id: "notif-5",
    category: "QUOTA_PAYMENT",
    title: "Cập nhật lượt tạo video trong tháng",
    body: "Bạn còn 1 lượt định kỳ trong tháng và 1 lượt mua thêm (giữ qua kỳ).",
    timestamp: "28/10/2026",
    unread: false,
    targetPath: "/p12-video-quota",
    actionLabel: "Xem quota",
  },
];

export const INITIAL_RUN_HISTORY: RunHistoryRecord[] = [
  {
    id: "run-hist-1",
    title: "Vòng đời bướm",
    childName: "Minh",
    ageLabel: "5 tuổi (60 tháng)",
    date: "30/10/2026",
    lifecycleState: "COMPLETED",
    idleHours: 2,
    scriptRevision: 1,
    regenUsed: 0,
    note: "Đã hoàn tất buổi học & gửi phản hồi cho\u00A0Cô\u00A0Thảo.",
  },
  {
    id: "run-hist-2",
    title: "Cây xanh quanh em (Đang chờ ở mốc 144h)",
    childName: "Minh",
    ageLabel: "5 tuổi (60 tháng)",
    date: "24/10/2026",
    lifecycleState: "VIDEO_READY_144H",
    idleHours: 144,
    scriptRevision: 2,
    regenUsed: 1,
    note: "Đã gửi nhắc hạn 144h. Nếu qua 168h ở trạng thái VIDEO_READY sẽ tự chuyển sang COMPLETED.",
  },
  {
    id: "run-hist-3",
    title: "Chú cá nhỏ (Tự đóng ở mốc 168h)",
    childName: "Minh",
    ageLabel: "5 tuổi (60 tháng)",
    date: "20/10/2026",
    lifecycleState: "ABANDONED_168H",
    idleHours: 168,
    scriptRevision: 1,
    regenUsed: 0,
    note: "Không tương tác sau 168h ở bước chờ người lớn xác nhận → tự chuyển ABANDONED & mở khóa run mới.",
  },
];
