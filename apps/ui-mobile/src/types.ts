export type ScreenId =
  // Flow 1 (Image 2)
  | 'splash'
  | 'onboarding'
  | 'dashboard'
  | 'profile'
  | 'capture'
  | 'voice'
  // Flow 2 (Image 1)
  | 'ai_processing'
  | 'scene_understanding'
  | 'story_preview'
  | 'video_player'
  | 'activity_recommend'
  | 'activity_detail'
  // Workflow Step 8 (Image 3)
  | 'feedback';

export interface ScreenMeta {
  id: ScreenId;
  title: string;
  subtitle: string;
  flow: 'flow1' | 'flow2';
  workflowStep: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
  stepName?: string;
}
