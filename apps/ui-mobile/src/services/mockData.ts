import type {
  ChildProfile,
  SceneUnderstandingResponse,
  StoryVideoResponse,
  MontessoriActivity,
} from './api.types';

export const MOCK_CHILDREN: ChildProfile[] = [
  {
    id: 'child-1',
    name: 'An',
    age: 5,
    ageGroup: '5-6',
    avatar: '👧',
    recentStoriesCount: 4,
  },
  {
    id: 'child-2',
    name: 'Bảo',
    age: 7,
    ageGroup: '7-8',
    avatar: '👦',
    recentStoriesCount: 2,
  },
];

export const MOCK_SCENE_UNDERSTANDING: SceneUnderstandingResponse = {
  storyId: 'story-butterfly-01',
  storyTitle: 'Giấc mơ của chú bướm',
  storySubtitle: 'Một câu chuyện từ bức vẽ của bé An',
  entities: [
    { id: 'e1', name: 'Con bướm', count: 1, icon: '🦋', category: 'animal' },
    { id: 'e2', name: 'Bông hoa', count: 2, icon: '🌷', category: 'plant' },
    { id: 'e3', name: 'Mặt trời', count: 1, icon: '☀️', category: 'nature' },
    { id: 'e4', name: 'Bãi cỏ', count: 1, icon: '🌿', category: 'nature' },
  ],
  voiceTranscript:
    'Chú bướm bay đến bông hoa, ở một khu vườn đầy nắng. Chúng mình cùng chơi và khám phá thế giới xung quanh nhé!',
  complimentTitle: 'Thật tuyệt vời!',
  complimentSub: 'Con có một câu chuyện rất sống động và đầy cảm xúc! ♡',
};

export const MOCK_STORY_VIDEO: StoryVideoResponse = {
  storyId: 'story-butterfly-01',
  title: 'Giấc mơ của chú bướm',
  subtitle: 'Một câu chuyện từ bức vẽ của Lan',
  totalDurationSeconds: 48,
  scenes: [
    { sceneNumber: 1, title: 'Cảnh 1: Thức dậy', duration: '00:15', icon: '🦋' },
    { sceneNumber: 2, title: 'Cảnh 2: Bay lượn', duration: '00:18', icon: '🌷' },
    { sceneNumber: 3, title: 'Cảnh 3: Hút mật', duration: '00:15', icon: '☀️' },
  ],
};

export const MOCK_ACTIVITIES: MontessoriActivity[] = [
  {
    id: 'act-butterfly-craft',
    title: 'Tự làm bướm sắc màu',
    subtitle: 'Khéo tay tạo nên những cánh bướm đầy sắc màu như trong câu chuyện!',
    ageGroup: '5–6 tuổi',
    durationMinutes: 30,
    category: 'Sáng tạo & Khéo léo',
    materials: [
      { id: 'm1', name: 'Giấy màu', type: 'paper', isReady: true },
      { id: 'm2', name: 'Kéo an toàn', type: 'scissors', isReady: true },
      { id: 'm3', name: 'Bút màu', type: 'crayon', isReady: true },
      { id: 'm4', name: 'Keo dán', type: 'glue', isReady: true },
    ],
    steps: [
      { stepNumber: 1, title: 'Cắt cánh bướm theo mẫu hoặc tự vẽ', isDone: true },
      { stepNumber: 2, title: 'Trang trí cánh bướm bằng màu sắc yêu thích', isDone: true },
      { stepNumber: 3, title: 'Gắn thân bướm và râu', isDone: false },
      { stepNumber: 4, title: 'Hoàn thiện và cùng nhau trưng bày!', isDone: false },
    ],
    safetyNotes: [
      'Nên có sự đồng hành của người lớn',
      'Sử dụng kéo an toàn, góc tròn cho trẻ mầm non',
    ],
    parentTips:
      'Hãy cùng con trò chuyện về màu sắc, thiên nhiên và những loài côn trùng xung quanh nhé! ♡',
  },
  {
    id: 'act-plant-sprout',
    title: 'Trồng hoa nhỏ cùng con',
    subtitle: 'Khám phá sự nảy mầm và vòng đời của cây hoa',
    ageGroup: '4 – 6 tuổi',
    durationMinutes: 25,
    category: 'Khám phá thiên nhiên',
    materials: [
      { id: 'p1', name: 'Chậu đất nhỏ', type: 'general' },
      { id: 'p2', name: 'Hạt giống hoa', type: 'general' },
      { id: 'p3', name: 'Bình tưới nước', type: 'general' },
    ],
    steps: [
      { stepNumber: 1, title: 'Cho đất vào chậu' },
      { stepNumber: 2, title: 'Gieo hạt và tưới nước' },
    ],
    safetyNotes: ['Rửa tay sạch sau khi chạm vào đất'],
    parentTips: 'Đặt chậu hoa ở nơi có nắng sáng để bé quan sát mỗi ngày.',
  },
];
