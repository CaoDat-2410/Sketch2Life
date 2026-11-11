import type { AudioUploadInput, ParentApiPort, ParentDrawingMediaType, StoryRunCreateInput } from '../ports/ParentPorts';
import type { LessonDetail, ParentProfile } from '../../domain/types';
import { ParentApplicationError } from '../ParentApplicationError';

export class ParentLearningUseCases {
  constructor(private readonly api: ParentApiPort) {}

  getActiveRun() { return this.api.getActiveStoryRun(); }
  getRun(runId: string) { return this.api.getStoryRun(runId); }
  generateSketchGuide(topic: string) { return this.api.generateSketchGuide(topic); }
  createRunForDrawing(input: {
    profile: ParentProfile;
    policyVersion: string;
    topic: string;
    adultIdea: string;
    imageBase64: string;
    contextConfirmed: boolean;
    lesson?: LessonDetail | null;
  }) {
    if (!input.profile.authorization_current) {
      throw new ParentApplicationError('PARENT_PROFILE_NOT_AUTHORIZED', 'Cần quyền xử lý dữ liệu còn hiệu lực.');
    }
    if (!input.imageBase64.trim()) {
      throw new ParentApplicationError('PARENT_DRAWING_REQUIRED', 'Chụp hoặc chọn ảnh tranh trước khi tạo buổi học.');
    }
    if (!input.contextConfirmed) {
      throw new ParentApplicationError('PARENT_CONTEXT_NOT_CONFIRMED', 'Người lớn cần xác nhận hồ sơ và ngữ cảnh trước.');
    }
    const request: StoryRunCreateInput = {
      parent_profile_id: input.profile.parent_profile_id,
      expected_profile_revision_id: input.profile.current_revision.profile_revision_id,
      consent_policy_version: input.policyVersion,
      topic: input.topic.trim(),
      adult_confirmed_idea: input.adultIdea.trim(),
      context_confirmed: true,
      ...(input.lesson ? { lesson_id: input.lesson.lesson_id, lesson_version_id: input.lesson.version_id } : {}),
    };
    return this.api.createStoryRun(request);
  }
  understandDrawing(runId: string, imageBase64: string, mediaType: ParentDrawingMediaType) {
    return this.api.analyzeDrawing(runId, imageBase64, mediaType);
  }
  confirmSubject(runId: string, revision: number, subject: string) {
    if (!subject.trim()) throw new ParentApplicationError('PARENT_SUBJECT_REQUIRED', 'Xác nhận chủ thể của bức vẽ trước.');
    return this.api.confirmSubject(runId, revision, subject);
  }
  suggestActivities(runId: string, revision: number) { return this.api.suggestActivities(runId, revision); }
  generateStory(runId: string, revision: number, rewriteInstruction?: string, rewriteCount = 0) {
    if (rewriteInstruction?.trim() && rewriteCount >= 3) {
      throw new ParentApplicationError('PARENT_STORY_REWRITE_LIMIT', 'Đã dùng hết 3 lượt gợi ý viết lại.');
    }
    return this.api.generateStory(runId, revision, rewriteInstruction);
  }
  confirmStory(runId: string, revision: number, sha256: string) {
    return this.api.confirmStory(runId, revision, sha256);
  }

  transcribeAudio(runId: string, audio: AudioUploadInput) {
    if (!runId.trim() || !audio.uri.trim()) {
      throw new ParentApplicationError('PARENT_AUDIO_REQUIRED', 'Chưa có bản ghi âm để gửi.');
    }
    return this.api.transcribeAudio(runId, audio);
  }

  confirmTranscript(runId: string, revision: number, transcriptText: string) {
    const text = transcriptText.trim();
    if (!runId.trim() || revision < 1 || !text || text.length > 500) {
      throw new ParentApplicationError('PARENT_TRANSCRIPT_TEXT_INVALID', 'Kiểm tra lại nội dung đã nhận dạng.');
    }
    return this.api.confirmTranscript(runId, revision, text);
  }
}
