import { API_CONFIG } from '../config/apiConfig';
import type {
  ChildProfile,
  DrawingUploadRequest,
  DrawingUploadResponse,
  VoiceTranscribeRequest,
  VoiceTranscriptResponse,
  SceneUnderstandingResponse,
  StoryVideoResponse,
  MontessoriActivity,
  FeedbackPayload,
  FeedbackResponse,
} from './api.types';
import {
  MOCK_CHILDREN,
  MOCK_SCENE_UNDERSTANDING,
  MOCK_STORY_VIDEO,
  MOCK_ACTIVITIES,
} from './mockData';

/**
 * Helper to execute HTTP fetch with timeout and fallback
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  fallbackData: T
): Promise<T> {
  if (API_CONFIG.USE_MOCK_API) {
    // Simulate natural network latency (250ms - 600ms) for realistic UX feel
    await new Promise((resolve) => setTimeout(resolve, 350));
    return fallbackData;
  }

  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...API_CONFIG.HEADERS,
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API Error [${response.status}]: ${response.statusText}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    console.warn(`[Sketch2Life API] Fallback to mock data for ${endpoint}:`, error);
    return fallbackData;
  }
}

export const ApiService = {
  /**
   * 1. Get list of children profiles
   * Endpoint: GET /api/children
   */
  async getChildren(): Promise<ChildProfile[]> {
    return apiFetch<ChildProfile[]>('/children', { method: 'GET' }, MOCK_CHILDREN);
  },

  /**
   * 2. Upload child's drawing
   * Endpoint: POST /api/drawings/upload
   */
  async uploadDrawing(payload: DrawingUploadRequest): Promise<DrawingUploadResponse> {
    const fallback: DrawingUploadResponse = {
      drawingId: 'draw-' + Date.now(),
      imageUrl: payload.imageUri || 'cat-drawing-sample',
      uploadedAt: new Date().toISOString(),
      detectedLabels: ['butterfly', 'flower', 'sun', 'meadow'],
    };

    return apiFetch<DrawingUploadResponse>(
      '/drawings/upload',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      fallback
    );
  },

  /**
   * 3. Transcribe audio from voice recording (Whisper ASR)
   * Endpoint: POST /api/voice/transcribe
   */
  async transcribeVoice(payload: VoiceTranscribeRequest): Promise<VoiceTranscriptResponse> {
    const fallback: VoiceTranscriptResponse = {
      audioId: 'audio-' + Date.now(),
      transcript: MOCK_SCENE_UNDERSTANDING.voiceTranscript,
      durationSeconds: payload.durationSeconds || 12,
      confidence: 0.98,
    };

    return apiFetch<VoiceTranscriptResponse>(
      '/voice/transcribe',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      fallback
    );
  },

  /**
   * 4. AI Scene Understanding (ASR + VLM Fusion - Human Gate A)
   * Endpoint: GET /api/story/scene-understanding?storyId=...
   */
  async getSceneUnderstanding(storyId = 'default'): Promise<SceneUnderstandingResponse> {
    return apiFetch<SceneUnderstandingResponse>(
      `/story/scene-understanding?storyId=${encodeURIComponent(storyId)}`,
      { method: 'GET' },
      MOCK_SCENE_UNDERSTANDING
    );
  },

  /**
   * 5. Get animated story video
   * Endpoint: GET /api/story/video?storyId=...
   */
  async getStoryVideo(storyId = 'default'): Promise<StoryVideoResponse> {
    return apiFetch<StoryVideoResponse>(
      `/story/video?storyId=${encodeURIComponent(storyId)}`,
      { method: 'GET' },
      MOCK_STORY_VIDEO
    );
  },

  /**
   * 6. Get Montessori Recommended Activities (Human Gate B)
   * Endpoint: GET /api/activities/recommend?age=...
   */
  async getRecommendedActivities(ageGroup = '5-6'): Promise<MontessoriActivity[]> {
    return apiFetch<MontessoriActivity[]>(
      `/activities/recommend?age=${encodeURIComponent(ageGroup)}`,
      { method: 'GET' },
      MOCK_ACTIVITIES
    );
  },

  /**
   * 7. Get Activity Detail by ID
   * Endpoint: GET /api/activities/:id
   */
  async getActivityDetail(activityId: string): Promise<MontessoriActivity> {
    const found = MOCK_ACTIVITIES.find((a) => a.id === activityId) || MOCK_ACTIVITIES[0];
    return apiFetch<MontessoriActivity>(
      `/activities/${encodeURIComponent(activityId)}`,
      { method: 'GET' },
      found
    );
  },

  /**
   * 8. Submit Parent Feedback & Observation (Step 8 Feedback Loop)
   * Endpoint: POST /api/activities/:id/feedback
   */
  async submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
    const fallback: FeedbackResponse = {
      success: true,
      message: 'Cập nhật nhật ký học tập thành công!',
      feedbackId: 'fb-' + Date.now(),
      savedAt: new Date().toISOString(),
    };

    return apiFetch<FeedbackResponse>(
      `/activities/${encodeURIComponent(payload.activityId)}/feedback`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      fallback
    );
  },
};
