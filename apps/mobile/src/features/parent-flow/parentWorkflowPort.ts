export type ParentScreen =
  | 'sign-in'
  | 'register'
  | 'recover'
  | 'profiles'
  | 'profile-create'
  | 'home'
  | 'drawing'
  | 'upload'
  | 'transcript-review'
  | 'subject-review'
  | 'context-review'
  | 'story-review'
  | 'video-status'
  | 'video-playback'
  | 'activities'
  | 'history'
  | 'notifications'
  | 'quota'
  | 'settings';

export type ParentRunStage =
  | 'drawing'
  | 'upload'
  | 'transcript-review'
  | 'subject-review'
  | 'context-review'
  | 'story-review'
  | 'video-status'
  | 'video-playback'
  | 'activities'
  | 'completed'
  | 'cancelled';

export type ParentRunStatus = 'active' | 'completed' | 'cancelled';
export type DrawingSource = 'camera-demo' | 'gallery-demo';
export type ChildGender = 'male' | 'female';

export type ParentProfile = Readonly<{
  id: string;
  label: string;
  ageMonths: number;
  gender: ChildGender;
}>;

export type StoryScene = Readonly<{
  id: string;
  title: string;
  narration: string;
}>;

export type ParentRun = Readonly<{
  id: string;
  childProfileId: string;
  title: string;
  createdLabel: string;
  status: ParentRunStatus;
  stage: ParentRunStage;
  drawingSource: DrawingSource | null;
  uploadInterrupted: boolean;
  uploadResumeCount: number;
  ideaText: string;
  hasVoiceIdea: boolean;
  transcript: string;
  transcriptConfirmed: boolean;
  subject: string;
  subjectRevision: number;
  subjectConfirmed: boolean;
  contextApproved: boolean;
  storyTitle: string;
  storyScenes: readonly StoryScene[];
  storyRevision: number;
  rewriteCount: number;
  scriptConfirmed: boolean;
  videoRequested: boolean;
  videoReady: boolean;
  videoError: boolean;
  videoVisible: boolean;
  regenerationCount: number;
  replacementRequested: boolean;
}>;

export type ParentWorkflowContent = Readonly<{
  pinnedContext: Readonly<{lessonLabel: string; storyDirection: string}>;
  guideSteps: readonly string[];
  postVideoActivity: Readonly<{title: string; materials: string; instructions: readonly string[]; note: string}>;
  quotaPeriodLabel: string;
  reminder: Readonly<{title: string; description: string; lifecycleNote: string}>;
}>;

export type ParentWorkflowSnapshot = Readonly<{
  screen: ParentScreen;
  signedIn: boolean;
  parentEmail: string | null;
  parentDisplayName: string | null;
  workflowContent: ParentWorkflowContent;
  profiles: readonly ParentProfile[];
  selectedProfileId: string | null;
  runs: readonly ParentRun[];
  activeRunId: string | null;
  selectedRunId: string | null;
  guideRequested: boolean;
  cameraDenied: boolean;
  microphoneDenied: boolean;
  quotaRemaining: number;
  quotaTotal: number;
  message: string | null;
}>;

export type ParentWorkflowCommand =
  | Readonly<{type: 'NAVIGATE'; screen: ParentScreen}>
  | Readonly<{type: 'BACK'}>
  | Readonly<{type: 'SIGN_IN'; email: string}>
  | Readonly<{type: 'REGISTER_DEMO'; email: string; displayName: string}>
  | Readonly<{type: 'RECOVER_PASSWORD_DEMO'; email: string}>
  | Readonly<{type: 'UPDATE_PARENT_ACCOUNT'; displayName: string; email: string}>
  | Readonly<{type: 'SIGN_OUT'}>
  | Readonly<{type: 'SELECT_PROFILE'; profileId: string}>
  | Readonly<{type: 'CREATE_PROFILE'; label: string; ageMonths: number; gender: ChildGender}>
  | Readonly<{type: 'START_RUN'}>
  | Readonly<{type: 'CONTINUE_RUN'}>
  | Readonly<{type: 'TOGGLE_GUIDE'; enabled: boolean}>
  | Readonly<{type: 'SAVE_IDEA'; text: string; hasVoiceIdea: boolean}>
  | Readonly<{type: 'CAPTURE_DRAWING'; source: DrawingSource}>
  | Readonly<{type: 'SIMULATE_CAMERA_DENIAL'; denied: boolean}>
  | Readonly<{type: 'SIMULATE_MICROPHONE_DENIAL'; denied: boolean}>
  | Readonly<{type: 'SIMULATE_UPLOAD_INTERRUPTION'}>
  | Readonly<{type: 'RESUME_UPLOAD'}>
  | Readonly<{type: 'COMPLETE_UPLOAD'}>
  | Readonly<{type: 'CONFIRM_TRANSCRIPT'; transcript: string}>
  | Readonly<{type: 'CONFIRM_SUBJECT'; subject: string}>
  | Readonly<{type: 'CONFIRM_CONTEXT'}>
  | Readonly<{type: 'REWRITE_STORY'}>
  | Readonly<{type: 'APPROVE_AND_REQUEST_VIDEO'}>
  | Readonly<{type: 'REQUEST_VIDEO'}>
  | Readonly<{type: 'COMPLETE_VIDEO_DEMO'}>
  | Readonly<{type: 'SIMULATE_VIDEO_ERROR'}>
  | Readonly<{type: 'SIMULATE_TOP_UP'; units: 3 | 5 | 10}>
  | Readonly<{type: 'PLAY_VIDEO'}>
  | Readonly<{type: 'CONTINUE_AFTER_VIDEO'}>
  | Readonly<{type: 'MARK_UNSUITABLE'}>
  | Readonly<{type: 'COMPLETE_RUN'}>
  | Readonly<{type: 'CANCEL_RUN'}>
  | Readonly<{type: 'OPEN_RUN'; runId: string}>
  | Readonly<{type: 'DELETE_RUN'; runId: string}>
  | Readonly<{type: 'CLEAR_MESSAGE'}>;

export interface ParentWorkflowPort {
  getSnapshot(): ParentWorkflowSnapshot;
  subscribe(listener: () => void): () => void;
  dispatch(command: ParentWorkflowCommand): Promise<void>;
}
