import { createParentActionIdentity } from '../ports/ParentPorts';
import type {
  ParentActionIdentity,
  ParentApiPort,
  ParentDrawingMediaType,
  StoryRunCreateInput,
} from '../ports/ParentPorts';
import type {
  LessonDetail,
  ParentActiveStoryRunEnvelopeV1,
  ParentActivitySelectionRequestV1,
  ParentLessonVersionPinV1,
  ParentProfile,
  ParentTopicSuggestionSetV1,
  ParentDrawingSubjectSuggestionSetV1,
  ParentCustomSubjectValidationV1,
  ParentStoryRunEnvelopeV1,
  ParentStoryRunV1,
  ParentSubjectRoleV1,
} from '../../domain/types';
import { ParentApplicationError } from '../ParentApplicationError';
import {
  readIdeaAccepted,
  readRewriteAccepted,
  readRunAssetAccepted,
  readTranscript,
  readTranscriptConfirmed,
  readVideoGenerationAccepted,
  STORY_REWRITE_REVISION_LIMIT,
} from '../parentPhaseB';
import { base64ToBytes, uploadRunMedia, type BinaryDigestPort, type RunUploadKeys, type UploadSessionsPort } from '../parentRunUploads';
import type { ParentVideoReasonCodeV1 } from '../../domain/types';

/** Phone side of the uploads: generic upload sessions, SHA-256 and the bytes of a recorded file. */
export interface ParentUploadPort {
  sessions: UploadSessionsPort;
  digest: BinaryDigestPort;
  readFileBytes(uri: string): Promise<Uint8Array>;
}

export class ParentLearningUseCases {
  constructor(private readonly api: ParentApiPort, private readonly uploads: ParentUploadPort | null = null) {}

  getActiveRun() { return this.api.getActiveStoryRun(); }
  getRun(runId: string) { return this.api.getStoryRun(runId); }
  getActiveRunV1(): Promise<ParentActiveStoryRunEnvelopeV1> { return this.api.getActiveStoryRunV1(); }
  getRunV1(runId: string) { return this.api.getStoryRunV1(runId); }
  listTopicSuggestions(draftId: string, excludedSetIds: string[], requestId: string): Promise<ParentTopicSuggestionSetV1> {
    return this.api.listTopicSuggestions(draftId, excludedSetIds, requestId);
  }
  listDrawingSubjectSuggestions(input: {
    draftId: string; topicId: string; topic: string; excludedSetIds: string[]; excludedSubjects?: string[]; requestId: string;
  }): Promise<ParentDrawingSubjectSuggestionSetV1> {
    return this.api.listDrawingSubjectSuggestions(input);
  }
  validateCustomSubject(input: { topicId: string; topic: string; subject: string }): Promise<ParentCustomSubjectValidationV1> {
    return this.api.validateCustomSubject(input);
  }
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
          request_id: active.request_id,
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
    if (pin && (!pin.lesson_id.trim() || !pin.version_id.trim() || !/^[0-9a-f]{64}$/.test(pin.content_sha256))) {
      throw new ParentApplicationError('PARENT_LESSON_PIN_REQUIRED', 'Phiên bản bài học đã chọn không hợp lệ. Hãy mở lại thư viện bài học.');
    }
    return this.api.createStoryRunV1({
      parent_profile_id: profileId,
      topic: input.topic.trim(),
      adult_confirmed_idea: input.adultIdea.trim(),
      ...(pin ? { lesson_version: {
        lesson_id: pin.lesson_id,
        version_id: pin.version_id,
        content_sha256: pin.content_sha256,
      } } : {}),
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
  confirmSubjectV1(
    runId: string,
    revision: number,
    subject: string,
    actionIdentity: ParentActionIdentity,
    subjectRoles?: ParentSubjectRoleV1[],
  ) {
    if (!subject.trim()) throw new ParentApplicationError('PARENT_SUBJECT_REQUIRED', 'Xác nhận chủ thể của bức vẽ trước.');
    return this.api.confirmStoryRunSubjectV1(runId, revision, subject, actionIdentity, subjectRoles);
  }
  listActivitiesV1(runId: string) {
    if (!runId.trim()) throw new ParentApplicationError('PARENT_ACTIVITY_RUN_INVALID', 'Chưa chọn được buổi học để tải hoạt động.');
    return this.api.listActivitiesV1(runId);
  }
  selectActivityV1(runId: string, input: ParentActivitySelectionRequestV1, actionIdentity: ParentActionIdentity) {
    if (!runId.trim() || !Number.isInteger(input.expected_revision) || input.expected_revision < 1) {
      throw new ParentApplicationError('PARENT_ACTIVITY_SELECTION_INVALID', 'Chưa xác nhận được hoạt động đã chọn.');
    }
    if ('activity' in input && (!input.activity.lesson_id.trim() || !input.activity.version_id.trim()
      || !/^[0-9a-f]{64}$/i.test(input.activity.content_sha256)
      || !Number.isInteger(input.activity.activity_index) || input.activity.activity_index < 0 || input.activity.activity_index > 23)) {
      throw new ParentApplicationError('PARENT_ACTIVITY_SELECTION_INVALID', 'Chưa xác nhận được hoạt động đã chọn.');
    }
    if ('round_id' in input && (!input.round_id.trim() || !Number.isInteger(input.draft_index) || input.draft_index < 0)) {
      throw new ParentApplicationError('PARENT_ACTIVITY_SELECTION_INVALID', 'Chưa xác nhận được hoạt động đã chọn.');
    }
    return this.api.selectActivityV1(runId, input, actionIdentity);
  }
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

  // ----------------------------------------------------------------------- Phase B (goal v3)

  /** T-2b: upload the drawing through an upload session, then attach it to the run (202, analysis follows). */
  async attachDrawingV1(input: {
    runId: string;
    runRevision: number;
    photo: { base64: string; mediaType: 'image/jpeg' | 'image/png' };
    keys: RunUploadKeys & { attach: ParentActionIdentity };
    signal?: AbortSignal;
  }) {
    const uploads = this.requireUploads();
    if (!input.photo.base64.trim()) {
      throw new ParentApplicationError('PARENT_DRAWING_REQUIRED', 'Chụp hoặc chọn ảnh tranh trước khi tiếp tục.');
    }
    const { assetRef } = await uploadRunMedia({
      uploads: uploads.sessions,
      digest: uploads.digest,
      purpose: 'RUN_ARTWORK',
      runId: input.runId,
      mediaType: input.photo.mediaType,
      bytes: base64ToBytes(input.photo.base64),
      keys: input.keys,
      signal: input.signal,
    });
    const answer = await this.api.attachRunAssetV1(input.runId, assetRef, input.runRevision, input.keys.attach);
    const accepted = readRunAssetAccepted(answer, { runId: input.runId, assetRef });
    if (!accepted) throw new ParentApplicationError('PARENT_DRAWING_RESULT_INVALID', 'Câu trả lời gắn ảnh không khớp buổi học.');
    return accepted;
  }

  /**
   * T-2c: upload the recording (`RUN_AUDIO`) and submit it as the voice idea (202, transcript follows).
   * The upload takes time and the analysis worker moves the run revision meanwhile, and `/idea` compares the
   * revision for equality: it is read again right before the command, and once more after a 409 STALE_REVISION.
   */
  async submitVoiceIdeaV1(input: {
    runId: string;
    currentRunRevision: () => Promise<number>;
    audio: { uri: string; mediaType: string };
    keys: RunUploadKeys & { idea: ParentActionIdentity };
    signal?: AbortSignal;
  }) {
    const uploads = this.requireUploads();
    if (!input.audio.uri.trim()) throw new ParentApplicationError('PARENT_AUDIO_REQUIRED', 'Chưa có bản ghi âm để gửi.');
    const { assetRef } = await uploadRunMedia({
      uploads: uploads.sessions,
      digest: uploads.digest,
      purpose: 'RUN_AUDIO',
      runId: input.runId,
      mediaType: input.audio.mediaType,
      bytes: await uploads.readFileBytes(input.audio.uri),
      keys: input.keys,
      signal: input.signal,
    });
    const send = async (key: ParentActionIdentity) => this.api.addRunIdeaV1(
      input.runId,
      { expected_run_revision: await input.currentRunRevision(), audio_ref: assetRef },
      key,
    );
    let answer;
    try {
      answer = await send(input.keys.idea);
    } catch (error) {
      if (!(error instanceof ParentApplicationError) || error.code !== 'STALE_REVISION') throw error;
      // The refused command wrote nothing; the body changes with the revision, so the retry is a new command.
      answer = await send(createParentActionIdentity());
    }
    const accepted = readIdeaAccepted(answer, input.runId);
    if (!accepted) throw new ParentApplicationError('PARENT_IDEA_RESULT_INVALID', 'Câu trả lời ý tưởng không khớp buổi học.');
    return accepted;
  }

  /** T-2c: a typed idea (1 to 500 characters), alone or beside a recording. */
  async submitTextIdeaV1(runId: string, runRevision: number, text: string, actionIdentity: ParentActionIdentity) {
    const value = text.trim();
    if (!value || value.length > 500) {
      throw new ParentApplicationError('PARENT_IDEA_TEXT_INVALID', 'Ý tưởng cần có nội dung, tối đa 500 ký tự.');
    }
    const answer = await this.api.addRunIdeaV1(runId, { expected_run_revision: runRevision, text: value }, actionIdentity);
    const accepted = readIdeaAccepted(answer, runId);
    if (!accepted) throw new ParentApplicationError('PARENT_IDEA_RESULT_INVALID', 'Câu trả lời ý tưởng không khớp buổi học.');
    return accepted;
  }

  async getTranscriptV1(runId: string) {
    const transcript = readTranscript(await this.api.getRunTranscriptV1(runId), runId);
    if (!transcript) throw new ParentApplicationError('PARENT_TRANSCRIPT_RESULT_INVALID', 'Chưa đọc được bản chép lời.');
    return transcript;
  }

  /** T-2c (TD-04): the adult's corrected text, based on one exact transcript revision. */
  async correctTranscriptV1(input: {
    runId: string;
    runRevision: number;
    baseRevision: number;
    text: string;
    actionIdentity: ParentActionIdentity;
  }) {
    const text = input.text.trim();
    if (!text || text.length > 500 || input.baseRevision < 1) {
      throw new ParentApplicationError('PARENT_TRANSCRIPT_TEXT_INVALID', 'Kiểm tra lại nội dung đã nhận dạng.');
    }
    const answer = await this.api.addRunIdeaV1(input.runId, {
      expected_run_revision: input.runRevision,
      transcript_correction: { base_revision: input.baseRevision, text },
    }, input.actionIdentity);
    const accepted = readIdeaAccepted(answer, input.runId);
    if (!accepted) throw new ParentApplicationError('PARENT_IDEA_RESULT_INVALID', 'Câu trả lời ý tưởng không khớp buổi học.');
    return accepted;
  }

  /** T-2c (TD-04): confirms one exact transcript revision and its hash. */
  async confirmTranscriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity) {
    if (!runId.trim() || revision < 1 || !/^[0-9a-f]{64}$/.test(sha256)) {
      throw new ParentApplicationError('PARENT_TRANSCRIPT_TEXT_INVALID', 'Kiểm tra lại nội dung đã nhận dạng.');
    }
    const answer = await this.api.confirmRunTranscriptV1(runId, revision, sha256, actionIdentity);
    const confirmed = readTranscriptConfirmed(answer, { runId, revision });
    if (!confirmed) throw new ParentApplicationError('PARENT_TRANSCRIPT_RESULT_INVALID', 'Chưa xác nhận được bản chép lời.');
    return confirmed;
  }

  /** T-2d (FR-P-07): one more story revision. At most three rewrites; the server refuses the fourth with a 409. */
  async rewriteStoryV1(run: ParentStoryRunV1, hint: string | undefined, actionIdentity: ParentActionIdentity) {
    const revisionNo = run.story_revision_no;
    if (typeof revisionNo !== 'number' || !Number.isInteger(revisionNo) || revisionNo < 1) {
      throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Chưa có kịch bản để viết lại.');
    }
    if (revisionNo >= STORY_REWRITE_REVISION_LIMIT) {
      throw new ParentApplicationError('STORY_REWRITE_LIMIT_REACHED', 'Đã dùng hết lượt viết lại.');
    }
    const text = hint?.trim() ?? '';
    if (text.length > 400 || /[\u0000-\u001f\u007f]/.test(text)) {
      throw new ParentApplicationError('PARENT_REWRITE_HINT_INVALID', 'Gợi ý viết lại tối đa 400 ký tự, không xuống dòng.');
    }
    const answer = await this.api.createStoryRewriteV1(run.run_id, {
      expected_story_revision: revisionNo,
      ...(run.story_sha256 && /^[0-9a-f]{64}$/.test(run.story_sha256) ? { expected_story_sha256: run.story_sha256 } : {}),
      ...(text ? { hint: text } : {}),
    }, actionIdentity);
    const accepted = readRewriteAccepted(answer, { runId: run.run_id, fromRevisionNo: revisionNo });
    if (!accepted) throw new ParentApplicationError('PARENT_REWRITE_RESULT_INVALID', 'Câu trả lời viết lại không khớp buổi học.');
    return accepted;
  }

  /** T-1a: ask for a video of the confirmed script. A reason is required from the second accepted request on. */
  async requestVideoV1(run: ParentStoryRunV1, reason: ParentVideoReasonCodeV1 | null, actionIdentity: ParentActionIdentity) {
    if (run.run_state !== 'SCRIPT_REVIEW' || run.story_status !== 'CONFIRMED' || !run.story_sha256 || !/^[0-9a-f]{64}$/.test(run.story_sha256)) {
      throw new ParentApplicationError('PARENT_STORY_NOT_CONFIRMABLE', 'Hãy xác nhận kịch bản trước khi tạo video.');
    }
    const needsReason = (run.video?.video_requests_used ?? 0) > 0;
    if (needsReason !== (reason !== null)) {
      throw new ParentApplicationError('PARENT_VIDEO_REASON_INVALID', 'Hãy chọn lý do khi tạo lại video.');
    }
    const answer = await this.api.requestVideoGenerationV1(run.run_id, {
      expected_revision: run.run_revision,
      story_sha256: run.story_sha256,
      ...(reason ? { quality_reason_code: reason } : {}),
    }, actionIdentity);
    const accepted = readVideoGenerationAccepted(answer, run.run_id);
    if (!accepted) throw new ParentApplicationError('PARENT_VIDEO_RESULT_INVALID', 'Câu trả lời tạo video không khớp buổi học.');
    return accepted;
  }

  /** T-1b: the current ready video is not suitable; the run returns to the script review. */
  markVideoUnsuitableV1(run: ParentStoryRunV1, reason: ParentVideoReasonCodeV1, actionIdentity: ParentActionIdentity) {
    const generationId = run.video?.current_generation_id;
    if (run.run_state !== 'VIDEO_READY' || !generationId) {
      throw new ParentApplicationError('INVALID_STATE_TRANSITION', 'Chưa có video sẵn sàng để đánh dấu.');
    }
    return this.api.markVideoUnsuitableV1(run.run_id, {
      expected_revision: run.run_revision,
      generation_id: generationId,
      reason_code: reason,
    }, actionIdentity);
  }

  /** T-1b: finishes the run at `VIDEO_READY`; not a video approval. */
  completeRunV1(run: ParentStoryRunV1, actionIdentity: ParentActionIdentity) {
    if (run.run_state !== 'VIDEO_READY') {
      throw new ParentApplicationError('INVALID_STATE_TRANSITION', 'Chỉ hoàn tất được khi video đã sẵn sàng.');
    }
    return this.api.completeRunV1(run.run_id, run.run_revision, actionIdentity);
  }

  /** T-1c: the stream address and headers for a native player; the grant is a secret and is never stored. */
  openPlaybackV1(runId: string) { return this.api.openPlaybackV1(runId); }

  private requireUploads(): ParentUploadPort {
    if (!this.uploads) throw new ParentApplicationError('CAPABILITY_UNAVAILABLE', 'Tải tệp lên chưa sẵn sàng.');
    return this.uploads;
  }
}
