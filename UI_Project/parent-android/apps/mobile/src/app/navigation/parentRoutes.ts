import type {Dispatch} from 'react';

export type ParentRoute =
  | 'login'
  | 'register'
  | 'recovery'
  | 'home'
  | 'profiles'
  | 'lesson-library'
  | 'lesson-detail'
  | 'run-setup'
  | 'capture'
  | 'voice'
  | 'understanding'
  | 'context'
  | 'activity-suggestions'
  | 'story-review'
  | 'generation'
  | 'video-player'
  | 'video-review'
  | 'activities'
  | 'completion'
  | 'session-feedback'
  | 'history'
  | 'sharing'
  | 'quota'
  | 'feedback'
  | 'notifications'
  | 'settings'
  | 'fixture';

export type GenerationPreviewState =
  | 'not-requested'
  | 'waiting'
  | 'failed'
  | 'admission-rejected'
  | 'quota-blocked'
  | 'rate-limited'
  | 'provider-unavailable'
  | 'reconciling'
  | 'ready-preview';

export type ParentProfileContext = Readonly<{
  interests: string;
  observations: string;
  achievements: string;
  outsideAppExperiences: string;
}>;

export type ParentChildProfile = Readonly<{
  id: string;
  name: string;
  age: string;
  color: string;
  lifecycle: 'active' | 'archived' | 'delete-pending';
  context: ParentProfileContext;
}>;

export type ParentAppState = Readonly<{
  route: ParentRoute;
  history: readonly ParentRoute[];
  previewMode: boolean;
  childId: string;
  childName: string;
  childAge: string;
  childProfiles: readonly ParentChildProfile[];
  activeRunChild: Readonly<{id: string; name: string; age: string}> | null;
  activeRunLesson: Readonly<{id: string; title: string; version: string; scriptFollowingChoice: 'follow-lesson' | 'free-story' | 'unset'}> | null;
  lessonId: string | null;
  lessonTitle: string | null;
  lessonVersion: string | null;
  scriptFollowingChoice: 'unset' | 'follow-lesson' | 'free-story';
  suggestedActivityId: string | null;
  lineSketchEnabled: boolean;
  idea: string;
  transcript: string;
  subject: string;
  contextApproved: boolean;
  contextIncludedFields: readonly (keyof ParentProfileContext)[];
  rewritePrompt: string;
  rewriteCount: number;
  storyConfirmed: boolean;
  generationState: GenerationPreviewState;
  runCancelPending: boolean;
  videoReviewReason: string;
  videoRegenerationCount: number;
  videoRegenerationPending: boolean;
  previousVideoHidden: boolean;
  pushPreference: 'not-enabled' | 'enabled-preview' | 'revoked-preview';
  feedbackRating: number;
  feedbackNote: string;
  notice: string | null;
}>;

export type ParentNavigationAction =
  | Readonly<{type: 'NAVIGATE'; route: ParentRoute}>
  | Readonly<{type: 'BACK'}>
  | Readonly<{type: 'ENTER_PREVIEW'}>
  | Readonly<{type: 'EXIT_PREVIEW'}>
  | Readonly<{type: 'SELECT_CHILD'; id: string; name: string; age: string}>
  | Readonly<{type: 'SAVE_CHILD_PROFILE'; profile: ParentChildProfile}>
  | Readonly<{type: 'ARCHIVE_CHILD_PROFILE'; id: string}>
  | Readonly<{type: 'RESTORE_CHILD_PROFILE'; id: string}>
  | Readonly<{type: 'REQUEST_CHILD_PROFILE_DELETE'; id: string}>
  | Readonly<{type: 'SELECT_LESSON'; id: string; title: string; version: string}>
  | Readonly<{type: 'SET_SCRIPT_FOLLOWING'; value: 'follow-lesson' | 'free-story'}>
  | Readonly<{type: 'SET_ACTIVITY_SUGGESTION'; value: string | null}>
  | Readonly<{type: 'BEGIN_RUN_PREVIEW'}>
  | Readonly<{type: 'SET_LINE_SKETCH'; enabled: boolean}>
  | Readonly<{type: 'SET_IDEA'; value: string}>
  | Readonly<{type: 'SET_TRANSCRIPT'; value: string}>
  | Readonly<{type: 'SET_SUBJECT'; value: string}>
  | Readonly<{type: 'APPROVE_CONTEXT'}>
  | Readonly<{type: 'SET_CONTEXT_FIELD_INCLUDED'; field: keyof ParentProfileContext; included: boolean}>
  | Readonly<{type: 'SET_REWRITE_PROMPT'; value: string}>
  | Readonly<{type: 'REQUEST_REWRITE_PREVIEW'}>
  | Readonly<{type: 'CONFIRM_STORY'}>
  | Readonly<{type: 'PREVIEW_GENERATION_STATE'; value: GenerationPreviewState}>
  | Readonly<{type: 'PREVIEW_VIDEO_READY'}>
  | Readonly<{type: 'SET_VIDEO_REVIEW_REASON'; value: string}>
  | Readonly<{type: 'ACCEPT_VIDEO_REGEN_PREVIEW'}>
  | Readonly<{type: 'RETURN_TO_STORY_AFTER_LIMIT'}>
  | Readonly<{type: 'SET_RUN_CANCEL_PENDING'; value: boolean}>
  | Readonly<{type: 'SET_PUSH_PREFERENCE'; value: ParentAppState['pushPreference']}>
  | Readonly<{type: 'SET_FEEDBACK_RATING'; value: number}>
  | Readonly<{type: 'SET_FEEDBACK_NOTE'; value: string}>
  | Readonly<{type: 'SHOW_NOTICE'; value: string}>
  | Readonly<{type: 'CLEAR_NOTICE'}>
  | Readonly<{type: 'RESET_RUN'}>;

export type ParentFlowProps = Readonly<{
  state: ParentAppState;
  dispatch: Dispatch<ParentNavigationAction>;
  onNavigate: (route: ParentRoute) => void;
  onNotice: (message: string) => void;
}>;

export const parentMainRoutes: readonly ParentRoute[] = [
  'home',
  'history',
  'notifications',
  'settings',
];

export {createInitialParentState, reduceParentNavigation} from './parentNavigationReducer';
