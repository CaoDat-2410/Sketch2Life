import type {ParentProfile, ParentRun, StoryScene} from '../../features/parent-flow/parentWorkflowPort';

export const DEMO_PROFILES: readonly ParentProfile[] = [
  {id: 'demo-profile-01', label: 'Bé Minh', ageMonths: 60, gender: 'male'},
  {id: 'demo-profile-02', label: 'Bé An', ageMonths: 48, gender: 'female'},
];

export const DEMO_STORY_TITLES = [
  'Khu vườn trong tranh',
  'Một chuyến đi quanh khu vườn',
  'Người bạn nhỏ tìm đường về',
  'Ngày nắng bên vườn cây',
] as const;

export const DEMO_STORY_SCENES: readonly StoryScene[] = [
  {id: 'demo-scene-01', title: 'Bức tranh mở ra', narration: 'Một buổi sáng yên lành bắt đầu từ nét vẽ của bạn.'},
  {id: 'demo-scene-02', title: 'Gặp người bạn mới', narration: 'Nhân vật trong tranh khám phá khu vườn đầy màu sắc.'},
  {id: 'demo-scene-03', title: 'Cùng tìm lối đi', narration: 'Những dấu hiệu quen thuộc giúp bạn nhỏ chọn đúng con đường.'},
  {id: 'demo-scene-04', title: 'Một việc tốt', narration: 'Bạn nhỏ dừng lại giúp người bạn đang cần hỗ trợ.'},
  {id: 'demo-scene-05', title: 'Trở về nhà', narration: 'Câu chuyện khép lại bằng một khoảnh khắc ấm áp.'},
];

export const DEMO_DEFAULT_TRANSCRIPT = 'Bạn nhỏ muốn khám phá khu vườn nhiều màu sắc.';
export const DEMO_DEFAULT_SUBJECT = 'Một khu vườn và người bạn nhỏ';

export const DEMO_CONTEXT = Object.freeze({
  lessonLabel: 'Lesson demo · Khu vườn',
  storyDirection: 'Khu vườn',
});

export const DEMO_GUIDE_STEPS = [
  'Nhìn hình lớn',
  'Thêm một chi tiết',
  'Chọn màu yêu thích',
] as const;
export const DEMO_OUTDOOR_ACTIVITY = Object.freeze({
  title: 'Săn tìm màu sắc ngoài sân',
  materials: 'Không cần chuẩn bị vật liệu đặc biệt.',
  instructions: [
    'Cùng người lớn chọn một màu trong câu chuyện.',
    'Tìm ba vật an toàn có màu đó ở ngoài sân hoặc ban công.',
    'Kể một điều thú vị về mỗi vật vừa tìm thấy.',
  ] as const,
  note: 'Người lớn ở cạnh trẻ trong suốt hoạt động.',
});

export const DEMO_REMINDER = Object.freeze({
  title: 'Run demo đang chờ bạn',
  description: 'Mẫu reminder sau 144 giờ chờ người lớn; bản demo không chạy timer hoặc gửi push/email.',
  lifecycleNote: 'Trong SRS, VIDEO_READY tự hoàn tất ở 168 giờ; demo không tự đóng run.',
});
export const DEMO_QUOTA = Object.freeze({remaining: 3, periodLabel: 'tháng demo này', total: 5});

export function createDemoRun(id: string, childProfileId: string): ParentRun {
  return {
    id,
    childProfileId,
    title: DEMO_STORY_TITLES[0],
    createdLabel: 'Vừa tạo',
    status: 'active',
    stage: 'drawing',
    drawingSource: null,
    uploadInterrupted: false,
    uploadResumeCount: 0,
    ideaText: '',
    hasVoiceIdea: false,
    transcript: DEMO_DEFAULT_TRANSCRIPT,
    transcriptConfirmed: false,
    subject: DEMO_DEFAULT_SUBJECT,
    subjectRevision: 1,
    subjectConfirmed: false,
    contextApproved: false,
    storyTitle: DEMO_STORY_TITLES[0],
    storyScenes: DEMO_STORY_SCENES,
    storyRevision: 1,
    rewriteCount: 0,
    scriptConfirmed: false,
    videoRequested: false,
    videoReady: false,
    videoError: false,
    videoVisible: false,
    regenerationCount: 0,
    replacementRequested: false,
  };
}
