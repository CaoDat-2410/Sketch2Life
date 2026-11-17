/**
 * TypeScript API Data Contracts for Sketch2Life
 * Matching Workflow (Image 3) Steps 1 to 8
 */

export interface ChildProfile {
  id: string;
  name: string;
  age: number;
  ageGroup: '3-4' | '5-6' | '7-8' | '9+';
  avatar: string;
  recentStoriesCount?: number;
}

export interface DrawingUploadRequest {
  childId: string;
  imageBase64?: string;
  imageUri?: string;
  title?: string;
}

export interface DrawingUploadResponse {
  drawingId: string;
  imageUrl: string;
  uploadedAt: string;
  detectedLabels: string[];
}

export interface VoiceTranscribeRequest {
  drawingId: string;
  audioUri?: string;
  durationSeconds: number;
}

export interface VoiceTranscriptResponse {
  audioId: string;
  transcript: string;
  durationSeconds: number;
  confidence: number;
}

export interface SceneEntity {
  id: string;
  name: string;
  count: number;
  icon: string;
  category?: 'animal' | 'plant' | 'nature' | 'object';
}

export interface SceneUnderstandingResponse {
  storyId: string;
  entities: SceneEntity[];
  voiceTranscript: string;
  complimentTitle: string;
  complimentSub: string;
  storyTitle: string;
  storySubtitle: string;
}

export interface StoryScene {
  sceneNumber: number;
  title: string;
  duration: string;
  icon: string;
}

export interface StoryVideoResponse {
  storyId: string;
  title: string;
  subtitle: string;
  totalDurationSeconds: number;
  videoUrl?: string;
  scenes: StoryScene[];
}

export interface ActivityMaterial {
  id: string;
  name: string;
  type: 'paper' | 'scissors' | 'crayon' | 'glue' | 'general';
  isReady?: boolean;
}

export interface ActivityStep {
  stepNumber: number;
  title: string;
  description?: string;
  isDone?: boolean;
}

export interface MontessoriActivity {
  id: string;
  title: string;
  subtitle: string;
  ageGroup: string;
  durationMinutes: number;
  category: string;
  materials: ActivityMaterial[];
  steps: ActivityStep[];
  safetyNotes: string[];
  parentTips: string;
}

export interface FeedbackPayload {
  activityId: string;
  childId: string;
  completionStatus: 'completed' | 'partial' | 'not_attempted';
  interestScore?: number; // 1 to 5
  interestRating?: number; // 1 to 5
  independenceScore?: number; // 1 to 5
  independenceRating?: number; // 1 to 5
  selectedObservationTags: string[];
  parentNotes: string;
}

export interface FeedbackResponse {
  success: boolean;
  message: string;
  feedbackId: string;
  savedAt: string;
  updatedProfile?: ChildProfile;
}
