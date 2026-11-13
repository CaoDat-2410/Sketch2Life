export type SelectedPhoto = {
  uri: string;
  base64: string;
  mediaType: 'image/jpeg' | 'image/png';
};

export type SelectedAudio = {
  uri: string;
  fileName: string;
  mediaType: 'audio/mp4' | 'audio/wav' | 'audio/webm' | 'audio/ogg';
};

export type TimedEvent = {
  stage: string;
  status: 'PASS' | 'FAIL';
  durationMs: number;
  requestId?: string;
  code?: string;
};

export type AppStep =
  | 'auth'
  | 'home'
  | 'profile'
  | 'profile-create'
  | 'profile-edit'
  | 'account'
  | 'settings'
  | 'notifications'
  | 'quota'
  | 'history'
  | 'profile-sharing'
  | 'lesson-history'
  | 'lesson-library'
  | 'topic'
  | 'drawing-guide'
  | 'lessons'
  | 'capture'
  | 'context'
  | 'understanding'
  | 'activity'
  | 'story'
  | 'handoff';
