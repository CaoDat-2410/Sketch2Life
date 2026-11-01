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
  }[];
}

export interface ChildProfileItem {
  id: string;
  displayName: string;
  ageMonths: number;
  ageLabel: string;
  ageGroup: string;
  interests: string[];
  archived?: boolean;
}

export interface AccessGrantItem {
  id: string;
  kind: "LESSON" | "CHILD_PROFILE";
  recipient: string;
  scope: string;
  expiresAt: string;
  status: "Đang hiệu lực" | "Đang chờ" | "Đã thu hồi";
  updatedAt: string;
}

export interface VideoJobSpecimen {
  id: string;
  title: string;
  date: string;
  status:
    | "Đang xếp hàng"
    | "Đang tạo video"
    | "Đang kiểm tra video"
    | "Video chưa thể hiển thị"
    | "Tạo video thất bại"
    | "Hoàn thành";
  badgeTone: "warn" | "info" | "off" | "err" | "ok";
  description: string;
  actionLabel?: "Tạo lại" | "Xem video";
}

export const INITIAL_PROFILES: ChildProfileItem[] = [
  {
    id: "child-minh",
    displayName: "Minh",
    ageMonths: 60,
    ageLabel: "5 tuổi",
    ageGroup: "4–5 tuổi (Mẫu giáo)",
    interests: ["Thích vẽ động vật", "Màu sắc tươi sáng", "Khám phá thiên nhiên"],
    archived: false,
  },
  {
    id: "child-an",
    displayName: "Bé An",
    ageMonths: 48,
    ageLabel: "4 tuổi",
    ageGroup: "3–4 tuổi (Mầm)",
    interests: ["Cây cối", "Kể chuyện"],
    archived: true,
  },
];

export const INITIAL_LESSONS: LessonCardItem[] = [
  {
    id: "lesson-butterfly",
    title: "Vòng đời bướm",
    ageBand: "4–5 tuổi",
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
        title: "Quan sát vòng đời bướm",
        materials: "Vật liệu: Sổ tay, bút màu",
        firstStep: "Bước 1: Tìm bướm hoặc sâu bướm ở vườn, công viên.",
      },
      {
        id: "act-butterfly-2",
        title: "Ghi lại điều con thấy",
        materials: "Vật liệu: Sổ tay, bút màu",
        firstStep: "Bước 1: Vẽ hoặc chụp hình bướm và những điều thú vị con thấy.",
      },
    ],
  },
  {
    id: "lesson-tree",
    title: "Cây xanh quanh em",
    ageBand: "4–5 tuổi",
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
      },
      {
        id: "act-tree-2",
        title: "In vân lá lên giấy",
        materials: "Vật liệu: Giấy trắng, bút sáp màu",
        firstStep: "Bước 1: Đặt lá dưới trang giấy và tô nhẹ để hiện đường gân lá.",
      },
    ],
  },
];

export const INITIAL_SCENES: SceneItem[] = [
  {
    index: 1,
    title: "Cảnh 1 · Chú sâu nhỏ trên chiếc lá",
    narration: "Sáng sớm trong khu vườn, chú sâu nhỏ bò chậm rãi trên chiếc lá xanh mướt đẫm sương.",
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
    narration: "Bướm vẫy đôi cánh nhiều màu sắc, hẹn gặp lại khu vườn trong những ngày nắng đẹp.",
    durationSec: 12,
  },
];

export const INITIAL_GRANTS: AccessGrantItem[] = [
  {
    id: "grant-lesson-1",
    kind: "LESSON",
    recipient: "Nhóm phụ huynh Lớp Mầm 2",
    scope: "Giáo án: Vòng đời bướm · Bản 3",
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
    recipient: "Trường Mầm non Ánh Dương · Lớp Mầm 2",
    scope: "Hồ sơ bé: Minh · 5 tuổi (Cô Thảo)",
    expiresAt: "31/05/2027",
    status: "Đang hiệu lực",
    updatedAt: "30/10/2026",
  },
  {
    id: "grant-profile-2",
    kind: "CHILD_PROFILE",
    recipient: "Trường Mầm non Ánh Dương · Lớp Chồi 1",
    scope: "Lời mời chia sẻ hồ sơ kỳ mới",
    expiresAt: "15/11/2026",
    status: "Đang chờ",
    updatedAt: "30/10/2026",
  },
  {
    id: "grant-profile-3",
    kind: "CHILD_PROFILE",
    recipient: "Lớp Hè Khám Phá 2026",
    scope: "Hồ sơ bé: Minh · 5 tuổi",
    expiresAt: "31/08/2026",
    status: "Đã thu hồi",
    updatedAt: "30/10/2026",
  },
];

export const UI07_VIDEO_JOBS: VideoJobSpecimen[] = [
  {
    id: "job-1",
    title: "Chuyến du hành vũ trụ",
    date: "30/10/2026",
    status: "Đang xếp hàng",
    badgeTone: "warn",
    description: "Chúng tôi sẽ bắt đầu tạo video sớm.",
  },
  {
    id: "job-2",
    title: "Khủng long phiêu lưu",
    date: "30/10/2026",
    status: "Đang tạo video",
    badgeTone: "info",
    description: "Video đang được tạo, vui lòng đợi trong giây lát.",
  },
  {
    id: "job-3",
    title: "Chú cá dưới biển",
    date: "30/10/2026",
    status: "Đang kiểm tra video",
    badgeTone: "info",
    description: "Video đang được kiểm tra để hiển thị.",
  },
  {
    id: "job-4",
    title: "Ngôi nhà mơ ước",
    date: "30/10/2026",
    status: "Video chưa thể hiển thị",
    badgeTone: "off",
    description: "Video không hiển thị do không phù hợp. Bạn có thể tạo video mới với tranh khác.",
  },
  {
    id: "job-5",
    title: "Chiếc xe màu đỏ",
    date: "30/10/2026",
    status: "Tạo video thất bại",
    badgeTone: "err",
    description: "Có lỗi trong quá trình tạo video. Lượt đã nhận vẫn được tính.",
    actionLabel: "Tạo lại",
  },
  {
    id: "job-6",
    title: "Chú sư tử dũng cảm",
    date: "30/10/2026",
    status: "Hoàn thành",
    badgeTone: "ok",
    description: "Video đã sẵn sàng để xem và chia sẻ.",
    actionLabel: "Xem video",
  },
];
