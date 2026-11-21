import { parentConfig } from '../config';
import { ParentApplicationError, type ParentApplicationErrorMetadata, type ParentSafeFieldError } from '../../application/ParentApplicationError';
import type { ParentCapabilityId } from '../../application/ports/ParentCapabilityPorts';
import type {
  AuthTokenPort,
  ActivitySuggestionResult,
  ParentActionIdentity,
  ParentApiPort,
  ParentDrawingMediaType,
} from '../../application/ports/ParentPorts';
import type {
  ConsentPolicy,
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentCandidate,
  ParentGroupInvitation,
  ParentLessonDeliveryPage,
  ParentNotification,
  ParentNotificationPage,
  ParentNotificationReadAllV1,
  ParentProfile,
  ParentProfileCreateV1,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfilePatchV1,
  ParentProfileRecordV1,
  ParentProfileReferenceV1,
  ParentProfileViewV1,
  ParentProfileShareGrant,
  ParentProfileSharePage,
  ParentRunLifecycleReceipt,
  ParentStoryRunLifecycleEnvelopeV1,
  ParentStoryRunResultV1,
  ParentActiveStoryRunEnvelopeV1,
  ParentStoryRunHistoryPage,
  ParentVideoQuota,
  ParentStoryContextConfirmationV1,
  ParentStoryRevisionResultV1,
  ParentStoryRunCreateV1,
  ParentStoryRunEnvelopeV1,
  ParentStoryRunV1,
  ParentStoryScriptConfirmationV1,
  ParentStorySubjectConfirmationAcceptedV1,
  ParentPlaybackSourceV1,
  ParentPlaybackTokenResponseV1,
  ParentRunAssetAcceptedV1,
  ParentRunIdeaAcceptedV1,
  ParentRunIdeaRequestV1,
  ParentRunTranscriptV1,
  ParentStoryRewriteAcceptedV1,
  ParentStoryRewriteRequestV1,
  ParentTranscriptConfirmedV1,
  ParentVideoGenerationAcceptedV1,
  ParentVideoRequestV1,
  ParentVideoUnsuitableRequestV1,
  StoryRun,
} from '../../domain/types';
import { buildPlaybackSource, isPlaybackGrantForRun } from '../../application/parentPhaseB';
import {
  readNotificationPageV1,
  readNotificationReadAllV1,
  readNotificationV1,
} from '../../application/parentNotifications';

export class ParentApiError extends ParentApplicationError {
  constructor(code: string, requestId: string, status?: number, metadata: ParentApplicationErrorMetadata = {}) {
    super(code, apiErrorMessage(code), requestId, status, metadata);
    this.name = 'ParentApiError';
  }
}

export class ParentApiUnavailableError extends ParentApiError {
  readonly state = 'unavailable' as const;
  readonly reason = 'route-not-in-be-handoff' as const;

  constructor(readonly capability: ParentCapabilityId) {
    super('CAPABILITY_UNAVAILABLE', 'local-unavailable');
    this.name = 'ParentApiUnavailableError';
  }
}

export class ParentApi implements ParentApiPort {
  constructor(
    private readonly auth: AuthTokenPort,
    private readonly fetcher: typeof fetch = fetch,
    private readonly apiBaseUrl: string = parentConfig.apiBaseUrl,
  ) {}

  getConsentPolicy() {
    return this.unavailable<{ request_id: string; policy: ConsentPolicy }>('consent');
  }

  listProfiles() {
    return this.unavailable<{ request_id: string; profiles: ParentProfile[] }>('profiles');
  }

  listProfilesV1(limit = 25, cursor?: string | null) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      return Promise.reject(new ParentApiError('INVALID_LIMIT', 'local-request'));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.request<ParentProfilePageV1>(`/v1/parent/profiles?${query.toString()}`, 'GET');
  }

  getProfileV1(profileId: string) {
    return this.request<ParentProfileRecordV1>(`/v1/parent/profiles/${encodeURIComponent(profileId)}`, 'GET');
  }

  createProfileV1(input: ParentProfileCreateV1, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 128, true);
    return this.request<ParentProfileReferenceV1>(
      '/v1/parent/profiles',
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  patchProfileV1(profileId: string, input: ParentProfilePatchV1, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 128, true);
    return this.request<ParentProfileViewV1>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}`,
      'PATCH',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  requestProfileDeletionV1(profileId: string, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 128, true);
    return this.request<ParentProfileDeletePendingV1>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}`,
      'DELETE',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  createProfile(input: {
    age_months: number;
    display_name: string;
    interests_summary: string;
    consent_accepted: true;
    consent_policy_version: string;
  }) {
    void input;
    return this.unavailable<{ request_id: string; profile: ParentProfile }>('profiles');
  }

  updateProfile(profileId: string, input: {
    expected_revision: number;
    age_months: number;
    display_name: string;
    interests_summary: string;
  }) {
    void profileId;
    void input;
    return this.unavailable<{ request_id: string; profile: ParentProfile }>('profiles');
  }

  grantAuthorization(profileId: string, policyVersion: string) {
    void profileId;
    void policyVersion;
    return this.unavailable<{ request_id: string; profile: ParentProfile }>('consent');
  }

  revokeAuthorization(profileId: string) {
    void profileId;
    return this.unavailable<{ request_id: string; profile: ParentProfile }>('consent');
  }

  archiveProfile(profileId: string) {
    void profileId;
    return this.unavailable<{ request_id: string; profile: ParentProfile }>('profiles');
  }

  getActiveStoryRun() {
    return this.unavailable<{ request_id: string; story_run: StoryRun | null }>('story-creation');
  }

  getStoryRun(runId: string) {
    void runId;
    return this.unavailable<{ request_id: string; story_run: StoryRun }>('story-creation');
  }

  getActiveStoryRunV1() {
    return this.request<ParentActiveStoryRunEnvelopeV1>('/v1/story-runs/active/current', 'GET');
  }

  getStoryRunV1(runId: string) {
    return this.request<ParentStoryRunResultV1>(`/v1/story-runs/${encodeURIComponent(runId)}`, 'GET');
  }

  createStoryRunV1(input: ParentStoryRunCreateV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunEnvelopeV1>(
      '/v1/story-runs',
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  confirmStoryRunContextV1(runId: string, input: ParentStoryContextConfirmationV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/context-confirmation`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  confirmStoryRunSubjectV1(runId: string, revision: number, subject: string, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStorySubjectConfirmationAcceptedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/subject-confirmation`,
      'POST',
      { expected_understanding_revision: revision, confirmed_subject: subject },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  confirmStoryRunScriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryScriptConfirmationV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/script-confirmation`,
      'POST',
      { expected_revision: revision, story_sha256: sha256 },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  createStoryRevisionV1(
    runId: string,
    revision: number,
    rewriteInstruction: string | undefined,
    actionIdentity: ParentActionIdentity,
  ) {
    assertIdempotencyKey(actionIdentity, 200);
    return this.request<ParentStoryRevisionResultV1>(
      `/api/parent/v1/ai/story-runs/${encodeURIComponent(runId)}/story-revisions`,
      'POST',
      {
        expected_understanding_revision: revision,
        ...(rewriteInstruction?.trim() ? { rewrite_instruction: rewriteInstruction.trim() } : {}),
      },
      1_850_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** FEAT-081 C3b: the caller's run history, 25 per page, newest first (summary only). */
  listStoryRuns(profileId?: string, cursor?: string | null) {
    const query = new URLSearchParams({ limit: '25' });
    if (cursor) query.set('cursor', cursor);
    if (profileId) query.set('parent_profile_id', profileId);
    return this.request<ParentStoryRunHistoryPage>(`/v1/story-runs?${query.toString()}`, 'GET', undefined, 30_000);
  }

  cancelStoryRun(runId: string) {
    void runId;
    return this.unavailable<ParentRunLifecycleReceipt>('run-history');
  }

  deleteStoryRun(runId: string) {
    void runId;
    return this.unavailable<ParentRunLifecycleReceipt>('run-history');
  }

  /** FR-C-08 cancel: 202 with the lifecycle projection. The key is 1 to 128 printable ASCII characters. */
  cancelStoryRunV1(runId: string, expectedRevision: number, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunLifecycleEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/cancel`,
      'POST',
      { expected_revision: expectedRevision },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  /** FR-C-08 delete of a COMPLETED, FAILED or ABANDONED run: 202 with the lifecycle projection; the request has no body. */
  deleteStoryRunV1(runId: string, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunLifecycleEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}`,
      'DELETE',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  /**
   * T-2b (SRS l.1664): attaches a completed `RUN_ARTWORK` upload to the run as its drawing. 202, no job
   * reference; the analysis is followed through `GET /v1/story-runs/{id}`. The key is 1 to 128 visible ASCII.
   */
  attachRunAssetV1(runId: string, assetRef: string, expectedRunRevision: number | null, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentRunAssetAcceptedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/assets`,
      'POST',
      { asset_ref: assetRef, ...(expectedRunRevision === null ? {} : { expected_run_revision: expectedRunRevision }) },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** T-2c (SRS l.1665): text and/or `audio_ref`, or one transcript correction. 202; the ASR job reference is parked (Q-J). */
  addRunIdeaV1(runId: string, input: ParentRunIdeaRequestV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentRunIdeaAcceptedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/idea`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** T-2c: the adult's read of the current transcript (a child's words: `no-store` on the server, never logged here). */
  getRunTranscriptV1(runId: string) {
    return this.request<ParentRunTranscriptV1>(`/v1/story-runs/${encodeURIComponent(runId)}/transcript`, 'GET');
  }

  /** T-2c (TD-04): confirms one exact transcript revision and hash. 200. */
  confirmRunTranscriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentTranscriptConfirmedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/transcript-confirmation`,
      'POST',
      { expected_transcript_revision: revision, transcript_sha256: sha256, confirmed: true },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** T-2d (SRS l.1668, FR-P-07): one more story revision, asynchronous. 202; 409 `STORY_REWRITE_LIMIT_REACHED` at the cap. */
  createStoryRewriteV1(runId: string, input: ParentStoryRewriteRequestV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRewriteAcceptedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/story-rewrites`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** T-1a (SRS l.1670): asks for a video of the confirmed script. 202 `ADMISSION_PENDING` or `ACCEPTED`. */
  requestVideoGenerationV1(runId: string, input: ParentVideoRequestV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentVideoGenerationAcceptedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/video-generations`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** T-1b (SRS l.1671): marks the current ready video unsuitable; the run returns to the script review. 200 run envelope. */
  markVideoUnsuitableV1(runId: string, input: ParentVideoUnsuitableRequestV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/video-unsuitable`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /** T-1b (SRS l.1672): finishes the run at `VIDEO_READY`; not a video approval. 200 run envelope. */
  completeRunV1(runId: string, expectedRevision: number, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/complete`,
      'POST',
      { expected_revision: expectedRevision },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  /**
   * T-1c (SRS l.1676, l.1691-1693): issues a short-lived grant and returns what a native player needs. The
   * grant is a bearer secret: it travels only in the `X-Playback-Token` header, never in a URL, a log or an
   * error. The address is rebuilt from the configured base URL and the run id; a `stream_path` that names
   * anything else is refused, so the Firebase bearer can never be sent to another host. One 1-byte ranged
   * read proves the grant works; a 401 means the grant (or the session) expired, and the grant is issued
   * once more before giving up. A 401 on the second issue is the session and surfaces as such.
   */
  async openPlaybackV1(runId: string): Promise<ParentPlaybackSourceV1> {
    const issued = await this.issuePlaybackTokenV1(runId);
    const first = await this.probePlayback(runId, issued);
    if (first.ok) return first.source;
    if (first.status !== 401) throw first.error;
    const reissued = await this.issuePlaybackTokenV1(runId);
    const second = await this.probePlayback(runId, reissued);
    if (second.ok) return second.source;
    // The session was valid (the grant was issued twice) but the stream still refuses the grant: not a sign-in problem.
    if (second.status === 401) throw new ParentApiError('PLAYBACK_TOKEN_REJECTED', second.error.requestId ?? 'local-request');
    throw second.error;
  }

  private issuePlaybackTokenV1(runId: string) {
    return this.request<ParentPlaybackTokenResponseV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/playback-token`,
      'POST',
      undefined,
      30_000,
    );
  }

  private async probePlayback(
    runId: string,
    response: ParentPlaybackTokenResponseV1,
  ): Promise<{ ok: true; source: ParentPlaybackSourceV1 } | { ok: false; status: number; error: ParentApiError }> {
    const requestId = createRequestId();
    const baseUrl = this.apiBaseUrl.replace(/\/+$/, '');
    if (!baseUrl) throw new ParentApiError('API_UNAVAILABLE', requestId);
    const grant = response?.playback;
    if (!isPlaybackGrantForRun(grant, runId)) throw new ParentApiError('INVALID_API_RESPONSE', requestId, 200);
    const source = buildPlaybackSource({ baseUrl, runId, grant, bearer: await this.auth.getIdToken(), nowMs: Date.now() });
    if (!source) throw new ParentApiError('INVALID_API_RESPONSE', requestId, 200);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30_000);
    try {
      const probe = await this.fetcher(source.uri, {
        method: 'GET',
        headers: { ...source.headers, 'X-Request-ID': requestId, Range: 'bytes=0-0' },
        signal: controller.signal,
      });
      if (probe.status === 200 || probe.status === 206) {
        await probe.body?.cancel?.().catch(() => undefined);
        return { ok: true, source };
      }
      const payload = await probe.json().catch(() => null) as Record<string, unknown> | null;
      return { ok: false, status: probe.status, error: apiErrorFromResponse(payload, probe.status, requestId, probe.headers) };
    } catch (error) {
      if (error instanceof ParentApiError) throw error;
      if (error instanceof Error && error.name === 'AbortError') throw new ParentApiError('REQUEST_TIMEOUT', requestId, 408);
      throw new ParentApiError('NETWORK_ERROR', requestId);
    } finally {
      clearTimeout(timeout);
    }
  }

  listLessons() {
    return this.request<{ contract: string; items: LessonSummary[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/lessons?source=ALL&limit=50', 'GET', undefined, 30_000,
    );
  }

  listLessonInvitations() {
    return this.request<{ contract: string; items: LessonInvitation[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/lesson-invitations?limit=50',
      'GET',
    );
  }

  acceptLessonInvitation(invitationId: string) {
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(invitationId)}/accept`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  declineLessonInvitation(invitationId: string) {
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(invitationId)}/decline`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  listParentGroupInvitations() {
    return this.request<{ contract: string; items: ParentGroupInvitation[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/parent-group-invitations?limit=50',
      'GET',
    );
  }

  acceptParentGroupInvitation(membershipId: string) {
    return this.request<unknown>(
      `/api/lesson-library/v1/me/parent-group-invitations/${encodeURIComponent(membershipId)}/accept`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  getLesson(lessonId: string) {
    return this.request<LessonDetail>(`/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}`, 'GET');
  }

  generateSketchGuide(topic: string) {
    return this.request<{
      request_id: string;
      modal_call_id?: string;
      status: string;
      review_required: true;
      model?: { id: string; revision: string };
      image_base64: string;
      asset?: Record<string, unknown>;
    }>('/api/parent/v1/ai/sketch-guides', 'POST', { topic, difficulty: 'beginner', step_count: 3 }, 910_000);
  }

  createStoryRun(input: {
    parent_profile_id: string;
    expected_profile_revision_id: string;
    consent_policy_version: string;
    topic: string;
    adult_confirmed_idea: string;
    context_confirmed: true;
    lesson_id?: string;
    lesson_version_id?: string;
  }) {
    void input;
    return this.unavailable<{ request_id: string; story_run: StoryRun }>('story-creation');
  }

  analyzeDrawing(storyRunId: string, imageBase64: string, mediaType: ParentDrawingMediaType) {
    return this.request<{
      request_id: string;
      modal_call_id?: string;
      candidate?: ParentCandidate;
      run_input_revision?: number;
      understanding_revision?: number;
    }>('/api/parent/v1/ai/drawing-understandings', 'POST', {
      story_run_id: storyRunId,
      image_base64: imageBase64,
      media_type: mediaType,
    }, 1_850_000);
  }

  confirmSubject(storyRunId: string, revision: number, subject: string) {
    void storyRunId;
    void revision;
    void subject;
    return this.unavailable<{ request_id: string; story_run_id: string; understanding_revision: number; decision: string }>('story-creation');
  }

  suggestActivities(storyRunId: string, revision: number) {
    void storyRunId;
    void revision;
    return this.unavailable<ActivitySuggestionResult>('story-creation');
  }

  generateStory(storyRunId: string, revision: number, rewriteInstruction?: string) {
    return this.request<{
      request_id: string;
      modal_call_id?: string;
      story?: unknown;
      story_sha256?: string;
      story_run?: StoryRun;
    }>(`/api/parent/v1/ai/story-runs/${encodeURIComponent(storyRunId)}/story-revisions`, 'POST', {
      expected_understanding_revision: revision,
      ...(rewriteInstruction?.trim() ? { rewrite_instruction: rewriteInstruction.trim() } : {}),
    }, 1_850_000);
  }

  confirmStory(storyRunId: string, revision: number, sha256: string) {
    void storyRunId;
    void revision;
    void sha256;
    return this.unavailable<{ request_id: string; story_run: StoryRun }>('story-creation');
  }

  listProfileShares(profileId: string) {
    void profileId;
    return this.unavailable<ParentProfileSharePage>('profile-sharing');
  }

  createProfileShare(profileId: string, teacherSubject: string) {
    void profileId;
    void teacherSubject;
    return this.unavailable<{ request_id: string; grant: ParentProfileShareGrant }>('profile-sharing');
  }

  revokeProfileShare(profileId: string, grantId: string) {
    void profileId;
    void grantId;
    return this.unavailable<{ request_id: string; grant: ParentProfileShareGrant }>('profile-sharing');
  }

  listLessonDeliveries(profileId: string, cursor?: string | null) {
    void profileId;
    void cursor;
    return this.unavailable<ParentLessonDeliveryPage>('lesson-history');
  }

  submitLessonFeedback(occurrenceId: string, profileId: string, feedbackText: string) {
    void occurrenceId;
    void profileId;
    void feedbackText;
    return this.unavailable<{
      contract: 'LessonDeliveryFeedbackV1';
      feedback_id: string;
      feedback_text: string;
      created_at: string;
      updated_at: string;
    }>('lesson-history');
  }

  listNotifications(cursor?: string | null, limit = 25): Promise<ParentNotificationPage> {
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      return Promise.reject(new ParentApiError('INVALID_LIMIT', 'local-request', 400));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.request<unknown>('/v1/notifications?' + query.toString(), 'GET', undefined, 30_000)
      .then((payload) => {
        const page = readNotificationPageV1(payload);
        if (!page) throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
        return page;
      });
  }

  markNotificationRead(notificationId: string, actionIdentity: ParentActionIdentity): Promise<ParentNotification> {
    assertVisibleAsciiKey(actionIdentity);
    if (!/^[A-Za-z0-9._:-]{1,64}$/.test(notificationId)) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    return this.request<unknown>(
      '/v1/notifications/' + encodeURIComponent(notificationId) + '/read',
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then((payload) => {
      const item = readNotificationV1(payload);
      if (!item || item.inbox_item_id !== notificationId || item.read_at === null) {
        throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
      }
      return item;
    });
  }

  markAllNotificationsRead(actionIdentity: ParentActionIdentity): Promise<ParentNotificationReadAllV1> {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<unknown>(
      '/v1/notifications/read-all',
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then((payload) => {
      const receipt = readNotificationReadAllV1(payload);
      if (!receipt) throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
      return receipt;
    });
  }

  getVideoQuota() {
    return this.unavailable<ParentVideoQuota>('quota');
  }

  private async request<T>(
    path: string,
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    body?: unknown,
    timeoutMs = 30_000,
    additionalHeaders: Record<string, string> = {},
  ): Promise<T> {
    const baseUrl = this.apiBaseUrl.replace(/\/+$/, '');
    if (!baseUrl) throw new Error('Thiếu SKETCH2LIFE_MOBILE_API_BASE_URL trong .env gốc.');
    const requestId = createRequestId();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await this.fetcher(`${baseUrl}${path}`, {
        method,
        headers: {
          Authorization: `Bearer ${await this.auth.getIdToken()}`,
          Accept: 'application/json',
          'X-Request-ID': requestId,
          ...additionalHeaders,
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
      if (!response.ok) {
        throw apiErrorFromResponse(payload, response.status, requestId, response.headers);
      }
      if (!payload || typeof payload !== 'object') throw new ParentApiError('INVALID_API_RESPONSE', requestId, response.status);
      return payload as T;
    } catch (error) {
      if (error instanceof ParentApiError) throw error;
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ParentApiError('REQUEST_TIMEOUT', requestId, 408);
      }
      throw new ParentApiError('NETWORK_ERROR', requestId);
    } finally {
      clearTimeout(timeout);
    }
  }

  private unavailable<T>(capability: ParentCapabilityId): Promise<T> {
    return Promise.reject(new ParentApiUnavailableError(capability));
  }
}

function apiErrorMessage(code: string): string {
  const messages: Record<string, string> = {
    REQUEST_TIMEOUT: 'Yêu cầu quá thời gian chờ. Trạng thái AI có thể chưa rõ; không tự gửi lại.',
    NETWORK_ERROR: 'Không kết nối được máy chủ.',
    REQUEST_CONFLICT: 'Dữ liệu đã thay đổi. Hãy tải lại trạng thái trước khi tiếp tục.',
    ACTION_NOT_ALLOWED: 'Tài khoản này chưa thể thực hiện thao tác vừa chọn.',
    PARENT_STORE_UNAVAILABLE: 'Hồ sơ đang tạm thời không khả dụng. Vui lòng thử lại sau.',
    ACTIVE_RUN_EXISTS: 'Hồ sơ đang có một buổi học chưa hoàn tất.',
    STALE_REVISION: 'Dữ liệu đã thay đổi. Hãy tải lại và kiểm tra trước khi tiếp tục.',
    INVALID_STATE_TRANSITION: 'Trạng thái hồ sơ đã thay đổi. Hãy tải lại hồ sơ.',
    INVALID_LIMIT: 'Không thể tải danh sách hồ sơ lúc này.',
    ROUTE_NOT_MOUNTED: 'Tính năng này chưa sẵn sàng.',
    CAPABILITY_UNAVAILABLE: 'Tính năng này chưa có tuyến dịch vụ được xác nhận.',
    IDEMPOTENCY_KEY_INVALID: 'Thao tác chưa thể gửi. Vui lòng bắt đầu lại thao tác.',
    PARENT_PROFILE_NOT_AUTHORIZED: 'Hồ sơ chưa có quyền xử lý dữ liệu còn hiệu lực.',
    PARENT_STORY_ACTIVE_RUN_EXISTS: 'Hồ sơ đang có một buổi học chưa hoàn tất.',
    MODAL_OUTCOME_UNKNOWN: 'Modal chưa xác nhận kết quả. Không tự gửi lại yêu cầu này.',
    MODAL_MODEL_OUTPUT_INVALID: 'AI đã phản hồi nhưng dữ liệu không đúng cấu trúc yêu cầu.',
    MODAL_MODEL_REVISION_MISMATCH: 'Phiên bản model trả về không khớp cấu hình.',
    MODAL_FUNCTION_UNAVAILABLE: 'Dịch vụ AI hiện chưa sẵn sàng.',
  };
  return messages[code] ?? 'Yêu cầu chưa hoàn tất. Vui lòng kiểm tra lại rồi thử lại sau.';
}

export function apiErrorFromResponse(
  payload: Record<string, unknown> | null,
  status: number,
  fallbackRequestId: string,
  headers?: Headers,
): ParentApiError {
  const detail = isRecord(payload?.detail) ? payload.detail : null;
  const code = safeErrorCode(payload?.code) ?? safeErrorCode(detail?.code) ?? `HTTP_${status}`;
  const requestId = safeIdentifier(payload?.request_id)
    ?? safeIdentifier(detail?.request_id)
    ?? safeIdentifier(headers?.get('X-Request-ID'))
    ?? fallbackRequestId;
  const correlationId = safeIdentifier(payload?.correlation_id) ?? safeIdentifier(detail?.correlation_id) ?? undefined;
  const retryableValue = typeof payload?.retryable === 'boolean'
    ? payload.retryable
    : typeof detail?.retryable === 'boolean' ? detail.retryable : undefined;
  const retryAfterValue = finiteNumber(payload?.retry_after_seconds)
    ?? finiteNumber(detail?.retry_after_seconds);
  const currentVersion = primitiveVersion(payload?.current_version) ?? primitiveVersion(detail?.current_version);
  const fieldErrors = safeFieldErrors(payload?.field_errors) ?? safeFieldErrors(detail?.field_errors);
  const metadata: ParentApplicationErrorMetadata = {
    ...(correlationId ? { correlationId } : {}),
    ...(retryableValue === undefined ? {} : { retryable: retryableValue }),
    ...(retryAfterValue === undefined ? {} : { retryAfterSeconds: retryAfterValue }),
    ...(currentVersion === undefined ? {} : { currentVersion }),
    ...(fieldErrors ? { fieldErrors } : {}),
  };
  return new ParentApiError(code, requestId, status, metadata);
}

function safeFieldErrors(value: unknown): ParentSafeFieldError[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const fields: Record<string, string> = {
    display_name: 'display_name',
    age_months: 'age_months',
    interests_summary: 'interests_summary',
    expected_revision: 'expected_revision',
    cursor: 'cursor',
    limit: 'limit',
    profile_id: 'profile_id',
    'idempotency-key': 'idempotency_key',
    idempotency_key: 'idempotency_key',
    lesson_version: 'lesson_version',
    topic: 'topic',
    adult_confirmed_idea: 'adult_confirmed_idea',
    // Generic upload sessions (T-2a): request fields and the two headers the server names.
    purpose: 'purpose',
    target_ref: 'target_ref',
    media_type: 'media_type',
    expected_size_bytes: 'expected_size_bytes',
    expected_sha256: 'expected_sha256',
    part_no: 'part_no',
    body: 'body',
    'if-match': 'if_match',
    'x-part-sha256': 'part_sha256',
    // Phase B story-run commands (T-2b to T-1b).
    asset_ref: 'asset_ref',
    audio_ref: 'audio_ref',
    text: 'text',
    transcript: 'transcript',
    hint: 'hint',
    quality_reason_code: 'quality_reason_code',
    reason_code: 'reason_code',
    expected_story_revision: 'expected_story_revision',
  };
  const codes = new Set([
    'REQUIRED', 'EMPTY', 'TOO_LONG', 'OUT_OF_RANGE', 'INVALID_TYPE', 'INVALID_FORMAT',
    'UNKNOWN_FIELD', 'INVALID_CURSOR', 'INVALID_LIMIT', 'STALE_REVISION', 'NOT_ALLOWED', 'INVALID_VALUE',
  ]);
  const result: ParentSafeFieldError[] = [];
  for (const item of value) {
    if (!isRecord(item) || typeof item.field !== 'string' || typeof item.code !== 'string') continue;
    const field = fields[item.field.toLowerCase()];
    const code = item.code.toUpperCase();
    if (field && codes.has(code)) result.push({ field, code });
  }
  return result;
}

function safeErrorCode(value: unknown): string | null {
  if (typeof value !== 'string' || value.length > 80 || !/^[A-Za-z0-9_]+$/.test(value)) return null;
  return value;
}

function safeIdentifier(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 && value.length <= 200 ? value : null;
}

function finiteNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : undefined;
}

function primitiveVersion(value: unknown): string | number | undefined {
  return typeof value === 'string' || (typeof value === 'number' && Number.isFinite(value)) ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** The server accepts 1 to 128 visible ASCII characters (0x21 to 0x7E); a space is refused. */
export function assertVisibleAsciiKey(key: ParentActionIdentity): void {
  if (!/^[\x21-\x7E]{1,128}$/.test(key)) {
    throw new ParentApiError('IDEMPOTENCY_KEY_INVALID', 'local-request', 400);
  }
}

/** A lifecycle answer where a live run is expected (the run was cancelled or deleted meanwhile). */
function liveRunOrLifecycleError<T extends object>(payload: T): T {
  const lifecycle = (payload as { lifecycle?: unknown }).lifecycle;
  if (typeof lifecycle === 'object' && lifecycle !== null) {
    const state = (lifecycle as { run_state?: unknown }).run_state;
    const requestId = (payload as { request_id?: unknown }).request_id;
    throw new ParentApiError(
      state === 'DELETED' ? 'DELETED' : 'DELETE_PENDING',
      typeof requestId === 'string' ? requestId : 'local-request',
      200,
    );
  }
  return payload;
}

function assertIdempotencyKey(key: ParentActionIdentity, maxLength: number, printableAscii = false): void {
  const validLength = key.length >= 1 && key.length <= maxLength;
  const validCharacters = !printableAscii || /^[\x20-\x7E]+$/.test(key);
  if (!validLength || !validCharacters) {
    throw new ParentApiError('IDEMPOTENCY_KEY_INVALID', 'local-request', 400);
  }
}

export function createRequestId(): string {
  const randomSuffix = Array.from({ length: 12 }, () => Math.floor(Math.random() * 36).toString(36)).join('');
  return `parent-${Date.now().toString(36)}-${randomSuffix}`;
}

function createIdempotencyKey(): string {
  return `parent-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 14)}`;
}
