export type ScreenId =
  // Flow 1 – Onboarding & Setup
  | 'splash'
  | 'onboarding'
  | 'dashboard'
  | 'profile'
  | 'capture'
  | 'choose_story_method'   // Chọn cách kể (giọng nói vs nhập chữ)
  | 'voice'
  // Flow 2 – AI Processing & Confirmation
  | 'ai_processing'
  | 'scene_understanding'   // Xác nhận chủ đề (Gate A - Người lớn)
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
  | 'completion'            // Hoàn thành
  // Workflow Step 8 (Feedback)
  | 'feedback'
  // Error fallback screens
  | 'pixl_error'
  | 'ai_error';             // Đánh giá & quan sát

export interface ScreenMeta {
  id: ScreenId;
  title: string;
  subtitle: string;
  flow: 'flow1' | 'flow2';
  workflowStep: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
  stepName?: string;
}
