import type {
  AudioUploadInput,
  ParentActionIdentity,
  ParentApiPort,
  ParentDrawingMediaType,
  StoryRunCreateInput,
} from '../ports/ParentPorts';
import type {
  LessonDetail,
  ParentActiveStoryRunEnvelopeV1,
  ParentLessonVersionPinV1,
  ParentProfile,
  ParentStoryRunEnvelopeV1,
  ParentStoryRunV1,
} from '../../domain/types';
import { ParentApplicationError } from '../ParentApplicationError';

export class ParentLearningUseCases {
  constructor(private readonly api: ParentApiPort) {}

  getActiveRun() { return this.api.getActiveStoryRun(); }
  getRun(runId: string) { return this.api.getStoryRun(runId); }
  getActiveRunV1(): Promise<ParentActiveStoryRunEnvelopeV1> { return this.api.getActiveStoryRunV1(); }
  getRunV1(runId: string) { return this.api.getStoryRunV1(runId); }
  generateSketchGuide(topic: string) { return this.api.generateSketchGuide(topic); }
  async createRunBeforeDrawingV1(input: {
    profileId: string;
    topic: string;
    adultIdea: string;
    lessonPin: ParentLessonVersionPinV1;
    actionIdentity: ParentActionIdentity;
  }): Promise<ParentStoryRunEnvelopeV1> {
    const profileId = input.profileId.trim();
    const topic = input.topic.trim();
    const adultIdea = input.adultIdea.trim();
    const pin = input.lessonPin;
    if (!profileId || !topic || !adultIdea) {
      throw new ParentApplicationError('PARENT_CONTEXT_REQUIRED', 'Hãy chọn hồ sơ và nhập ý tưởng trước khi bắt đầu.');
    }
    if (!pin?.lesson_id.trim() || !pin.version_id.trim() || !pin.content_sha256.trim()) {
      throw new ParentApplicationError('PARENT_LESSON_PIN_REQUIRED', 'Hãy chọn bài học trước khi bắt đầu.');
    }
    try {
      return await this.api.createStoryRunV1({
        parent_profile_id: profileId,
        topic,
        adult_confirmed_idea: adultIdea,
        lesson_version: {
          lesson_id: pin.lesson_id,
          version_id: pin.version_id,
          content_sha256: pin.content_sha256,
        },
      }, input.actionIdentity);
    } catch (error) {
      if (!(error instanceof ParentApplicationError) || error.code !== 'ACTIVE_RUN_EXISTS') throw error;
      const active = await this.api.getActiveStoryRunV1();
      if (active.story_run) {
        return {
          ...(active.request_id === undefined ? {} : { request_id: active.request_id }),
          story_run: active.story_run,
        };
      }
      throw error;
    }
  }
  async createRunAfterPhotoV1(input: {
    profileId: string;
    topic: string;
    adultIdea: string;
    lessonPin: ParentLessonVersionPinV1 | null;
    actionIdentity: ParentActionIdentity;
  }): Promise<ParentStoryRunEnvelopeV1> {
    const profileId = input.profileId.trim();
    const pin = input.lessonPin;
    if (!profileId) {
      throw new ParentApplicationError('PARENT_CONTEXT_REQUIRED', 'Hãy chọn hồ sơ trước khi tiếp tục.');
    }
    if (!pin?.lesson_id.trim() || !pin.version_id.trim() || !/^[0-9a-f]{64}$/.test(pin.content_sha256)) {
      throw new ParentApplicationError('PARENT_LESSON_PIN_REQUIRED', 'Hãy chọn và ghim một phiên bản bài học trước khi bắt đầu.');
    }
    return this.api.createStoryRunV1({
      parent_profile_id: profileId,
      topic: input.topic.trim(),
      adult_confirmed_idea: input.adultIdea.trim(),
      lesson_version: {
        lesson_id: pin.lesson_id,
        version_id: pin.version_id,
        content_sha256: pin.content_sha256,
      },
    }, input.actionIdentity);
  }
  confirmRunContextV1(run: ParentStoryRunV1, actionIdentity: ParentActionIdentity) {
    if (!run.run_id.trim() || run.context_revision < 1 || !run.context_snapshot_sha256.trim()) {
      throw new ParentApplicationError('PARENT_CONTEXT_SNAPSHOT_INVALID', 'Chưa thể xác nhận ngữ cảnh của buổi học này.');
    }
    return this.api.confirmStoryRunContextV1(run.run_id, {
      expected_context_revision: run.context_revision,
      context_snapshot_sha256: run.context_snapshot_sha256,
      confirmed: true,
    }, actionIdentity);
  }
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
  confirmSubjectV1(runId: string, revision: number, subject: string, actionIdentity: ParentActionIdentity) {
    if (!subject.trim()) throw new ParentApplicationError('PARENT_SUBJECT_REQUIRED', 'Xác nhận chủ thể của bức vẽ trước.');
    return this.api.confirmStoryRunSubjectV1(runId, revision, subject, actionIdentity);
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
  confirmScriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity) {
    return this.api.confirmStoryRunScriptV1(runId, revision, sha256, actionIdentity);
  }
  createStoryRevisionV1(runId: string, revision: number, rewriteInstruction: string | undefined, actionIdentity: ParentActionIdentity) {
    return this.api.createStoryRevisionV1(runId, revision, rewriteInstruction, actionIdentity);
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
