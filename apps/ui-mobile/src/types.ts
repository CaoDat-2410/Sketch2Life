export type ScreenId =
  // Active Parent flow (SRS V2.2)
  | 'login'
  | 'profile_list'
  | 'profile_detail'
  | 'parent_home'
  | 'topic_selection'
  | 'activity_selection'
  | 'profile'
  | 'sketch_guide'
  | 'capture'
  | 'voice'
  | 'transcript_review'
  | 'story_review'
  | 'ai_processing'
  | 'scene_understanding'
  | 'activity_context_review'
  | 'storyboard'
  | 'script_confirm'
  | 'video_processing'
  | 'safety_gate'
  | 'playback'
  | 'completion'
  | 'history'
  | 'quota'
  | 'notifications_settings'

  // Legacy/reference screens kept temporarily for migration compatibility.
  | 'splash'
  | 'onboarding'
  | 'dashboard'
  | 'choose_story_method'   // Chọn cách kể (giọng nói vs nhập chữ)
  | 'preview_result'        // Xem trước kết quả
  | 'story_preview'         // Pixl / Animation intro (cho bé)
  | 'video_player'
  | 'activity_recommend'    // Gợi ý hoạt động (Gate B)
  | 'experience_review'     // Người lớn duyệt Gate B
  | 'pixi_intro'            // Pixi story intro
  | 'video_placeholder'
  | 'activity_detail'       // Hoạt động ngoài đời
  | 'adult_confirm'         // Người lớn xác nhận & đưa máy cho bé
  | 'child_transition'      // Chuyển sang chế độ của bé
  | 'child_guide'           // Hướng dẫn ngắn cho bé
  | 'child_steps'           // Các bước thực hiện cho bé
  // Workflow Step 8 (Feedback)
  | 'feedback'
  // Error fallback screens
  | 'pixl_error'
  | 'ai_error'
  | 'missing_step'
  | 'no_results'
  | 'settings';             // Đánh giá & quan sát

/** Screens currently exposed by the Parent SRS V2.2 flow. */
export const PARENT_FLOW_SCREENS: ScreenId[] = [
  'login',
  'profile_list',
  'profile_detail',
  'parent_home',
  'topic_selection',
  'sketch_guide',
  'capture',
  'voice',
  'transcript_review',
  'activity_selection',
  'ai_processing',
  'scene_understanding',
  'activity_context_review',
  'story_review',
  'storyboard',
  'script_confirm',
  'video_processing',
  'safety_gate',
  'playback',
  'completion',
  'history',
  'quota',
  'notifications_settings',
];

export interface ScreenMeta {
  id: ScreenId;
  title: string;
  subtitle: string;
  flow: 'flow1' | 'flow2';
  workflowStep: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
  stepName?: string;
}
