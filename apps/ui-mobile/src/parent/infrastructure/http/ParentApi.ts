import { parentConfig } from '../config';
import { ParentApplicationError, type ParentApplicationErrorMetadata, type ParentSafeFieldError } from '../../application/ParentApplicationError';
import type { ParentCapabilityId } from '../../application/ports/ParentCapabilityPorts';
import type {
  AuthTokenPort,
  ActivitySelectionReceipt,
  ActivitySuggestionResult,
  ParentActionIdentity,
  ParentApiPort,
  ParentDrawingMediaType,
} from '../../application/ports/ParentPorts';
import type {
  ConsentPolicy,
  ParentConsentPolicyV1,
  LessonDetail,
  LessonExportV1,
  LessonInvitation,
  ParentLessonListOptions,
  ParentLessonPage,
  CreateParentContextEntryRequest,
  ParentContextEntryEnvelope,
  ParentContextEntryListView,
  ParentCandidate,
  ParentActivityListV1,
  ParentActivitySuggestionSetV1,
  ParentActivitySelectionRequestV1,
  ParentCustomSubjectValidationV1,
  ParentDrawingSubjectSuggestionSetV1,
  ParentSubjectRoleV1,
  ParentTopicSuggestionSetV1,
  ParentGroupInvitation,
  ParentGroupMembershipPage,
  ParentGroupMembershipV1,
  ParentLessonDeliveryPage,
  ParentNotification,
  ParentNotificationPage,
  ParentNotificationReadAllV1,
  PushEndpointRegistrationResultV1,
  PushEndpointRegistrationV1,
  ParentProfile,
  ParentProfileCreateV1,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfilePatchV1,
  ParentProfileRecordV1,
  ParentProfileReferenceV1,
  ParentProfileViewV1,
  ParentSupportNeedsV1,
  ParentSupportNeedsWriteV1,
  ParentProfileShareGrant,
  ParentProfileSharePage,
  ParentShareField,
  ParentShareGrantV1,
  ParentShareGrantCreatedV1,
  ParentShareGrantPageV1,
  ParentShareDeliveryPageV1,
  ParentLessonFeedbackV1,
  ParentLessonFeedbackStateV1,
  ParentLessonFeedbackReplyPageV1,
  ParentRunLifecycleReceipt,
  ParentStoryRunLifecycleEnvelopeV1,
  ParentStoryRunResultV1,
  ParentActiveStoryRunEnvelopeV1,
  ParentStoryRunHistoryPage,
  ParentVideoQuota,
  ParentQuotaProduct,
  ParentQuotaInvoicePage,
  ParentQuotaPaymentSettings,
  ParentQuotaCheckoutResult,
  ParentQuotaReconcileResult,
  ParentQuotaCancelResult,
  ParentStoryContextConfirmationV1,
  ParentStoryRevisionResultV1,
  ParentStoryRunCreateV1,
  ParentStoryRunEnvelopeV1,
  ParentDrawingAnalysisResumeV1,
  ParentStoryRunV1,
  SupportNeedsPutV1,
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
import type { SvgTopicStrokeGuideDraftV1 } from '../../domain/svgGuide';
import type { ParentPaymentProvider } from '../../application/parentQuota';
import {
  readParentQuotaCancelResult,
  readParentQuotaCheckoutResult,
  readParentQuotaInvoices,
  readParentQuotaPaymentSettings,
  readParentQuotaProducts,
  readParentQuotaReconcileResult,
  readParentVideoQuota,
} from '../../application/parentQuota';
import {
  filterSafeSvgGuideCatalogItems,
  type SvgGuideCatalogPageV1,
  type SvgTopicStrokeGuideSourceDraftV1,
} from '../../domain/svgGuide';
import { buildPlaybackSource, isPlaybackGrantForRun, readMainActivityV1 } from '../../application/parentPhaseB';
import {
  readNotificationPageV1,
  readNotificationReadAllV1,
  readNotificationV1,
} from '../../application/parentNotifications';

const PHASE_A_ACTIVITY_ERROR_CODES = new Set([
  'AUTH_REQUIRED', 'INVALID_TOKEN', 'INVALID_REQUEST', 'INVALID_IDEMPOTENCY_KEY',
  'RESOURCE_NOT_FOUND', 'INVALID_STATE_TRANSITION', 'STALE_REVISION', 'SUBJECT_NOT_CONFIRMED',
  'PARENT_ACTIVITY_SELECTION_REQUIRED', 'PARENT_STORY_RUN_STORE_UNAVAILABLE', 'DEPENDENCY_UNAVAILABLE',
]);

const PHASE_B_PARENT_PROFILE_ERROR_CODES = new Set([
  'AUTH_REQUIRED', 'INVALID_TOKEN', 'INVALID_REQUEST', 'INVALID_IDEMPOTENCY_KEY',
  'PROFILE_NOT_FOUND', 'RESOURCE_NOT_FOUND', 'INVALID_STATE_TRANSITION', 'STALE_REVISION',
  'SUPPORT_NEEDS_UNAVAILABLE', 'PARENT_STORY_RUN_STORE_UNAVAILABLE', 'PARENT_PROFILE_STORE_UNAVAILABLE',
]);

const PHASE_B_PARENT_CONTEXT_CONFIRMATION_ERROR_CODES = new Set([
  ...PHASE_A_ACTIVITY_ERROR_CODES,
  'PROFILE_NOT_FOUND', 'PARENT_STORY_RUN_STORE_UNAVAILABLE',
]);

// FEAT-083 parent_topic_suggestions.py enforces 2–80 characters per exclude_subject and Query(max_length=24).
const EXCLUDED_SUBJECT_MIN_CHARS = 2;
const EXCLUDED_SUBJECT_MAX_CHARS = 80;
const EXCLUDED_SUBJECT_MAX_ITEMS = 24;

function normalizeExcludedSubjects(values: readonly string[] | undefined): string[] {
  return (values ?? [])
    .map((value) => value.trim().replace(/\s+/gu, ' '))
    .filter((value) => {
      const characterCount = Array.from(value).length;
      return characterCount >= EXCLUDED_SUBJECT_MIN_CHARS && characterCount <= EXCLUDED_SUBJECT_MAX_CHARS;
    })
    .slice(-EXCLUDED_SUBJECT_MAX_ITEMS);
}

function invalidLessonListRequest(): ParentApiError {
  return new ParentApiError('INVALID_REQUEST', 'local-request', 400);
}

function lessonListQuery(options: ParentLessonListOptions): URLSearchParams {
  const source = options.source ?? 'ALL';
  const limit = options.limit ?? 25;
  if (!['ALL', 'PUBLIC', 'SHARED'].includes(source) || !Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw invalidLessonListRequest();
  }
  const query = new URLSearchParams({ source, limit: String(limit) });
  if (options.cursor !== undefined && options.cursor !== null) {
    if (typeof options.cursor !== 'string' || options.cursor.length > 1024 || /\p{Cc}/u.test(options.cursor)) {
      throw invalidLessonListRequest();
    }
    query.set('cursor', options.cursor);
  }
  for (const [field, value, maxLength] of [
    ['q', options.q, 100],
    ['topic', options.topic, 120],
  ] as const) {
    if (value === undefined) continue;
    if (typeof value !== 'string' || /\p{Cc}/u.test(value)) throw invalidLessonListRequest();
    const trimmed = value.trim();
    if (!trimmed) continue;
    if (Array.from(trimmed).length > maxLength) throw invalidLessonListRequest();
    query.set(field, trimmed);
  }
  if (options.ageBand !== undefined) {
    const ageBand = options.ageBand as { ref?: unknown; version?: unknown } | null;
    if (!ageBand || typeof ageBand.ref !== 'string' || typeof ageBand.version !== 'number') {
      throw invalidLessonListRequest();
    }
    const ref = ageBand.ref.trim();
    if (Array.from(ref).length < 1 || Array.from(ref).length > 256
      || /\p{Cc}/u.test(ageBand.ref) || !/^[A-Za-z0-9._:-]+$/.test(ref)
      || !Number.isInteger(ageBand.version) || ageBand.version < 1) {
      throw invalidLessonListRequest();
    }
    query.set('target_age_band_ref', ref);
    query.set('target_age_band_version', String(ageBand.version));
  }
  return query;
}

function readParentGroupMembershipV1(value: unknown): ParentGroupMembershipV1 | null {
  if (!isRecord(value)
    || value.contract !== 'ParentGroupMembershipV1'
    || typeof value.membership_id !== 'string'
    || typeof value.parent_group_id !== 'string'
    || (value.organization_id !== undefined && typeof value.organization_id !== 'string')
    || !['INVITED', 'ACTIVE', 'REVOKED', 'EXPIRED', 'DECLINED'].includes(String(value.state))
    || typeof value.invited_at !== 'string'
    || !(typeof value.expires_at === 'string' || value.expires_at === null)
    || !(typeof value.accepted_at === 'string' || value.accepted_at === null)
    || typeof value.revision !== 'number'
    || !Number.isInteger(value.revision)
    || typeof value.revision_source !== 'string') return null;
  return value as unknown as ParentGroupMembershipV1;
}

function readParentGroupMembershipPage(value: unknown): ParentGroupMembershipPage | null {
  if (!isRecord(value) || typeof value.contract !== 'string' || !Array.isArray(value.items)
    || !(typeof value.next_cursor === 'string' || value.next_cursor === null)) return null;
  const items = value.items.map(readParentGroupMembershipV1);
  if (items.some((item) => !item || item.state !== 'ACTIVE')) return null;
  return { contract: value.contract, items: items as ParentGroupMembershipV1[], next_cursor: value.next_cursor };
}

function readParentConsentPolicyV1(value: unknown): ParentConsentPolicyV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentConsentPolicyV1'
    || typeof value.request_id !== 'string' || !value.request_id || !isRecord(value.policy)) return null;
  const policy = value.policy;
  if (policy.purpose_code !== 'SYNTHETIC_TEST_ONLY'
    || policy.policy_version !== 'parent-consent-placeholder-v0'
    || typeof policy.consent_text !== 'string' || !policy.consent_text.trim()
    || typeof policy.consent_text_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(policy.consent_text_sha256)
    || policy.policy_state !== 'PLACEHOLDER_NOT_APPROVED'
    || policy.data_origin_scope !== 'SYNTHETIC_TEST'
    || policy.effective_from !== null
    || !Array.isArray(policy.purposes)
    || policy.purposes.length !== 1
    || !isRecord(policy.purposes[0])
    || policy.purposes[0].purpose_code !== 'SYNTHETIC_TEST_ONLY'
    || policy.purposes[0].text_key !== 'parent.consent.placeholder.synthetic_test_only'
    || !Array.isArray(policy.links) || policy.links.length !== 0
    || policy.acceptance_recording !== 'NOT_AVAILABLE') return null;
  return value as unknown as ParentConsentPolicyV1;
}

const PARENT_SHARE_FIELDS = ['DISPLAY_NAME', 'AGE_BAND', 'INTERESTS_SUMMARY'] as const;

function isUuid(value: unknown): value is string {
  return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function isTimestamp(value: unknown): value is string {
  return typeof value === 'string' && Number.isFinite(Date.parse(value));
}

function readParentShareGrantV1(value: unknown): ParentShareGrantV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentShareGrantV1'
    || !isUuid(value.share_grant_id) || !isUuid(value.profile_id)
    || !['INVITED', 'ACTIVE', 'REVOKED', 'EXPIRED'].includes(String(value.state))
    || !Array.isArray(value.granted_fields)
    || !value.granted_fields.every((field) => PARENT_SHARE_FIELDS.includes(field as ParentShareField))
    || new Set(value.granted_fields).size !== value.granted_fields.length
    || JSON.stringify(value.granted_fields) !== JSON.stringify([...value.granted_fields].sort())
    || !isTimestamp(value.created_at) || !isTimestamp(value.invitation_expires_at)
    || !(typeof value.accepted_at === 'string' || value.accepted_at === null)
    || !(typeof value.expires_at === 'string' || value.expires_at === null)
    || !(typeof value.revoked_at === 'string' || value.revoked_at === null)
    || typeof value.revision !== 'number' || !Number.isInteger(value.revision) || value.revision < 1) return null;
  if ((typeof value.accepted_at === 'string' && !isTimestamp(value.accepted_at))
    || (typeof value.expires_at === 'string' && !isTimestamp(value.expires_at))
    || (typeof value.revoked_at === 'string' && !isTimestamp(value.revoked_at))) return null;
  return value as unknown as ParentShareGrantV1;
}

function readParentShareGrantCreatedV1(value: unknown): ParentShareGrantCreatedV1 | null {
  const grant = readParentShareGrantV1(value);
  if (!grant || !isRecord(value)
    || !(value.invitation_code === null
      || (typeof value.invitation_code === 'string' && /^[A-Za-z0-9_-]{22}$/.test(value.invitation_code)))) return null;
  return value as ParentShareGrantCreatedV1;
}

function readParentShareGrantPageV1(value: unknown): ParentShareGrantPageV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentShareGrantListV1' || !Array.isArray(value.items)
    || !(typeof value.next_cursor === 'string' || value.next_cursor === null)) return null;
  const items = value.items.map(readParentShareGrantV1);
  if (items.some((item) => !item)) return null;
  return value as unknown as ParentShareGrantPageV1;
}

function readParentShareDeliveryPageV1(value: unknown): ParentShareDeliveryPageV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentShareDeliveryListV1'
    || typeof value.share_grant_id !== 'string'
    || !['AVAILABLE', 'ENDED'].includes(String(value.content_access))
    || !Array.isArray(value.items)
    || !(typeof value.next_cursor === 'string' || value.next_cursor === null)) return null;
  const validItems = value.items.every((item) => isRecord(item)
    && isTimestamp(item.delivered_at)
    && (typeof item.title === 'string' || item.title === null)
    && (value.content_access !== 'ENDED' || item.title === null));
  return validItems ? value as unknown as ParentShareDeliveryPageV1 : null;
}

function readParentLessonFeedbackV1(value: unknown): ParentLessonFeedbackV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentLessonFeedbackV1'
    || typeof value.feedback_id !== 'string' || typeof value.lesson_id !== 'string'
    || typeof value.version_id !== 'string' || typeof value.revision !== 'number'
    || !Number.isInteger(value.revision) || value.revision < 1
    || typeof value.feedback_text !== 'string'
    || Array.from(value.feedback_text.trim()).length < 1 || Array.from(value.feedback_text.trim()).length > 1200
    || !isTimestamp(value.created_at) || !isTimestamp(value.updated_at) || typeof value.reply_count !== 'number'
    || !Number.isInteger(value.reply_count) || value.reply_count < 0) return null;
  return value as unknown as ParentLessonFeedbackV1;
}

function readParentLessonFeedbackStateV1(value: unknown): ParentLessonFeedbackStateV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentLessonFeedbackStateV1'
    || typeof value.lesson_id !== 'string') return null;
  if (value.feedback === null) return value as unknown as ParentLessonFeedbackStateV1;
  const feedback = readParentLessonFeedbackV1(value.feedback);
  return feedback && feedback.lesson_id === value.lesson_id
    ? value as unknown as ParentLessonFeedbackStateV1 : null;
}

function readParentLessonFeedbackReplyPageV1(value: unknown): ParentLessonFeedbackReplyPageV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentLessonFeedbackReplyPageV1'
    || !(typeof value.feedback_id === 'string' || value.feedback_id === null)
    || !Array.isArray(value.items)
    || !(typeof value.next_cursor === 'string' || value.next_cursor === null)) return null;
  const validItems = value.items.every((item) => isRecord(item)
    && typeof item.reply_id === 'string' && typeof item.reply_text === 'string'
    && isTimestamp(item.created_at));
  return validItems ? value as unknown as ParentLessonFeedbackReplyPageV1 : null;
}

export class ParentApiError extends ParentApplicationError {
  constructor(
    code: string,
    requestId: string,
    status?: number,
    metadata: ParentApplicationErrorMetadata = {},
    displayMessage?: string,
  ) {
    super(code, displayMessage ?? apiErrorMessage(code), requestId, status, {
      ...metadata,
      ...(displayMessage ? { safeDisplayMessage: displayMessage } : {}),
    });
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
    return this.requestValidated('/v1/parent/consent-policy', readParentConsentPolicyV1);
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

  listContextEntriesV1(profileId: string, cursor?: string | null) {
    const query = new URLSearchParams({ limit: '25' });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.request<ParentContextEntryListView>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}/context-entries?${query.toString()}`,
      'GET',
    );
  }

  createContextEntryV1(profileId: string, input: CreateParentContextEntryRequest, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    const body = {
      entry_kind: input.entry_kind,
      short_text: input.short_text,
      source_kind: input.source_kind,
      ...(input.approximate_date === undefined ? {} : { approximate_date: input.approximate_date }),
    };
    return this.request<ParentContextEntryEnvelope>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}/context-entries`,
      'POST',
      body,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  getSupportNeedsV1(profileId: string) {
    return this.request<ParentSupportNeedsV1>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}/support-needs`,
      'GET',
    );
  }

  putSupportNeedsV1(profileId: string, input: SupportNeedsPutV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentSupportNeedsWriteV1>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}/support-needs`,
      'PUT',
      { expected_revision: input.expected_revision, category: input.category, note: input.note },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
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
    return this.request<ParentActiveStoryRunEnvelopeV1>('/v1/story-runs/active/current', 'GET').then((result) => ({
      ...result,
      story_run: result.story_run ? validateRunMainActivity(result.story_run, result.request_id) : null,
    }));
  }

  getStoryRunV1(runId: string) {
    return this.request<ParentStoryRunResultV1>(`/v1/story-runs/${encodeURIComponent(runId)}`, 'GET').then((result) => {
      if ('story_run' in result) {
        return { ...result, story_run: validateRunMainActivity(result.story_run, result.request_id) };
      }
      return result;
    });
  }

  listActivitiesV1(runId: string) {
    const query = new URLSearchParams({ story_run_id: runId });
    return this.request<ParentActivityListV1>(`/v1/activities?${query.toString()}`, 'GET');
  }

  suggestActivitiesV1(runId: string, expectedUnderstandingRevision: number, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentActivitySuggestionSetV1>(
      `/api/parent/v1/ai/story-runs/${encodeURIComponent(runId)}/activity-suggestions`,
      'POST',
      // A reopened app or a reload takes the set the run already has instead of generating a second one.
      { expected_understanding_revision: expectedUnderstandingRevision, reuse_latest: true },
      1_850_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  requestActivitySuggestionsV1(storyRunId: string, revision: number, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 200);
    if (!storyRunId.trim() || !Number.isInteger(revision) || revision < 1) {
      return Promise.reject(new ParentApiError('PARENT_ACTIVITY_CONTEXT_REQUIRED', 'local-request', 400));
    }
    return this.request<ActivitySuggestionResult>(
      `/api/parent/v1/ai/story-runs/${encodeURIComponent(storyRunId)}/activity-suggestions`,
      'POST',
      { expected_understanding_revision: revision },
      1_850_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  selectSuggestedActivityV1(input: {
    storyRunId: string;
    suggestionSetId: string;
    revision: number;
    activityIndex: number;
    actionIdentity: ParentActionIdentity;
  }) {
    assertIdempotencyKey(input.actionIdentity, 200);
    if (!input.storyRunId.trim() || !input.suggestionSetId.trim()
      || !Number.isInteger(input.revision) || input.revision < 1
      || !Number.isInteger(input.activityIndex) || input.activityIndex < 0 || input.activityIndex > 23) {
      return Promise.reject(new ParentApiError('PARENT_ACTIVITY_SELECTION_INVALID', 'local-request', 400));
    }
    return this.request<ActivitySelectionReceipt>(
      `/api/parent/v1/ai/story-runs/${encodeURIComponent(input.storyRunId)}/activity-selection`,
      'POST',
      {
        suggestion_set_id: input.suggestionSetId,
        expected_understanding_revision: input.revision,
        activity_index: input.activityIndex,
      },
      30_000,
      { 'Idempotency-Key': input.actionIdentity },
    );
  }

  selectActivityV1(runId: string, input: ParentActivitySelectionRequestV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/activity-selection`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then(liveRunOrLifecycleError);
  }

  createStoryRunV1(input: ParentStoryRunCreateV1, actionIdentity: ParentActionIdentity) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStoryRunEnvelopeV1>(
      '/v1/story-runs',
      'POST',
      {
        parent_profile_id: input.parent_profile_id,
        topic: input.topic,
        adult_confirmed_idea: input.adult_confirmed_idea,
        ...(input.lesson_version === undefined ? {} : { lesson_version: input.lesson_version === null ? null : {
          lesson_id: input.lesson_version.lesson_id,
          version_id: input.lesson_version.version_id,
          content_sha256: input.lesson_version.content_sha256,
        } }),
      },
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

  confirmStoryRunSubjectV1(
    runId: string,
    revision: number,
    subject: string,
    actionIdentity: ParentActionIdentity,
    subjectRoles?: ParentSubjectRoleV1[],
  ) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<ParentStorySubjectConfirmationAcceptedV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/subject-confirmation`,
      'POST',
      {
        expected_understanding_revision: revision,
        confirmed_subject: subject,
        ...(subjectRoles && subjectRoles.length > 0 ? { subject_roles: subjectRoles } : {}),
      },
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

  /** Retry dispatch of the already attached queued drawing; never uploads or resends its image. */
  resumeDrawingAnalysisV1(runId: string, inputRevision: number) {
    return this.request<ParentDrawingAnalysisResumeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/drawing-analysis/resume`,
      'POST',
      { expected_input_revision: inputRevision },
      30_000,
    );
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

  listLessons(options: ParentLessonListOptions = {}): Promise<ParentLessonPage> {
    const query = lessonListQuery(options);
    return this.request<ParentLessonPage>(
      `/api/lesson-library/v1/me/lessons?${query.toString()}`, 'GET', undefined, 30_000,
    );
  }

  listSvgCatalogGuides(topicKey?: string, limit = 50): Promise<SvgGuideCatalogPageV1> {
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      return Promise.reject(new ParentApiError('INVALID_LIMIT', 'local-request', 422));
    }
    if (topicKey !== undefined && !/^[a-z0-9-]{1,120}$/.test(topicKey)) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 422));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (topicKey !== undefined) query.set('topic_key', topicKey);
    return this.request<unknown>(`/api/svg-catalog/v1/parent/guides?${query.toString()}`, 'GET')
      .then((payload) => {
        if (!isRecord(payload) || payload.contract !== 'SvgGuideCatalogPageV1'
          || !Array.isArray(payload.items)) {
          throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
        }
        const items = filterSafeSvgGuideCatalogItems(payload.items);
        if (payload.items.length > 0 && items.length === 0) {
          throw new ParentApiError('PARENT_SVG_GUIDE_INVALID', 'local-response', 200);
        }
        return { ...payload, items } as unknown as SvgGuideCatalogPageV1;
      });
  }

  listLessonInvitations() {
    return this.request<{ contract: string; items: LessonInvitation[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/lesson-invitations?limit=50',
      'GET',
    );
  }

  acceptLessonInvitation(invitationId: string, actionIdentity: ParentActionIdentity = createIdempotencyKey()) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(invitationId)}/accept`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  declineLessonInvitation(invitationId: string, actionIdentity: ParentActionIdentity = createIdempotencyKey()) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(invitationId)}/decline`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  listParentGroupInvitations() {
    return this.request<{ contract: string; items: ParentGroupInvitation[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/parent-group-invitations?limit=50',
      'GET',
    );
  }

  acceptParentGroupInvitation(membershipId: string, actionIdentity: ParentActionIdentity = createIdempotencyKey()) {
    assertVisibleAsciiKey(actionIdentity);
    return this.request<unknown>(
      `/api/lesson-library/v1/me/parent-group-invitations/${encodeURIComponent(membershipId)}/accept`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  declineParentGroupInvitation(
    membershipId: string,
    actionIdentity: ParentActionIdentity,
  ): Promise<ParentGroupMembershipV1> {
    assertVisibleAsciiKey(actionIdentity);
    if (!membershipId.trim()) throw invalidLessonListRequest();
    return this.request<unknown>(
      `/api/lesson-library/v1/me/parent-group-invitations/${encodeURIComponent(membershipId)}/decline`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then((payload) => {
      const membership = readParentGroupMembershipV1(payload);
      if (!membership || membership.membership_id !== membershipId || membership.state !== 'DECLINED' || membership.accepted_at !== null) {
        throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
      }
      return membership;
    });
  }

  leaveParentGroup(
    organizationId: string,
    parentGroupId: string,
    membershipId: string,
    revision: number,
    actionIdentity: ParentActionIdentity,
  ): Promise<ParentGroupMembershipV1> {
    assertVisibleAsciiKey(actionIdentity);
    if (!organizationId.trim() || !parentGroupId.trim() || !membershipId.trim()
      || !Number.isInteger(revision)) {
      throw invalidLessonListRequest();
    }
    return this.request<unknown>(
      `/api/lesson-library/v1/organizations/${encodeURIComponent(organizationId)}/parent-groups/${encodeURIComponent(parentGroupId)}/members/${encodeURIComponent(membershipId)}`,
      'DELETE',
      undefined,
      30_000,
      { 'If-Match': `"${revision}"`, 'Idempotency-Key': actionIdentity },
    ).then((payload) => {
      const membership = readParentGroupMembershipV1(payload);
      if (!membership
        || membership.membership_id !== membershipId
        || membership.parent_group_id !== parentGroupId
        || (membership.organization_id !== undefined && membership.organization_id !== organizationId)
        || membership.state !== 'REVOKED'
        || membership.revision !== revision + 1) {
        throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
      }
      return membership;
    });
  }

  listParentGroupMemberships(cursor?: string | null): Promise<ParentGroupMembershipPage> {
    if (cursor !== undefined && cursor !== null
      && (typeof cursor !== 'string' || cursor.length > 1024 || /\p{Cc}/u.test(cursor))) {
      throw invalidLessonListRequest();
    }
    const query = new URLSearchParams({ limit: '25' });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.request<unknown>(
      `/api/lesson-library/v1/me/parent-group-memberships?${query.toString()}`,
      'GET',
    ).then((payload) => {
      const page = readParentGroupMembershipPage(payload);
      if (!page) throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
      return page;
    });
  }

  getLesson(lessonId: string) {
    return this.request<LessonDetail>(`/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}`, 'GET');
  }

  downloadLesson(lessonId: string): Promise<LessonExportV1> {
    if (!lessonId.trim()) return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}/download`,
      'GET',
    ).then((payload) => {
      if (!isLessonExportV1(payload, lessonId)) {
        throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
      }
      return payload;
    });
  }

  listTopicSuggestions(draftId: string, excludedSetIds: string[], requestId = createRequestId()) {
    const query = new URLSearchParams({ draft_id: draftId, request_id: requestId });
    excludedSetIds.slice(-16).forEach((setId) => query.append('exclude_set_ids', setId));
    return this.request<ParentTopicSuggestionSetV1>(
      `/api/parent/v1/topics/suggestions?${query.toString()}`,
      'GET',
    );
  }

  listDrawingSubjectSuggestions(input: {
    draftId: string;
    topicId: string;
    topic: string;
    excludedSetIds: string[];
    excludedSubjects?: string[];
    requestId?: string;
  }) {
    const query = new URLSearchParams({
      draft_id: input.draftId,
      request_id: input.requestId ?? createRequestId(),
      topic: input.topic,
    });
    input.excludedSetIds.slice(-16).forEach((setId) => query.append('exclude_set_ids', setId));
    normalizeExcludedSubjects(input.excludedSubjects).forEach((subject) => query.append('exclude_subjects', subject));
    return this.request<ParentDrawingSubjectSuggestionSetV1>(
      `/api/parent/v1/topics/${encodeURIComponent(input.topicId)}/drawing-subject-suggestions?${query.toString()}`,
      'GET',
    );
  }

  validateCustomSubject(input: { topicId: string; topic: string; subject: string }) {
    return this.request<ParentCustomSubjectValidationV1>(
      '/api/parent/v1/topics/custom-subject-validation',
      'POST',
      { topic_id: input.topicId, topic: input.topic, subject: input.subject },
    );
  }

  generateSketchGuide(topic: string, intendedSubject?: string): Promise<SvgTopicStrokeGuideSourceDraftV1>;
  generateSketchGuide(
    topic: string,
    intendedSubject: string | undefined,
    difficulty: 'beginner' | 'simple',
  ): Promise<SvgTopicStrokeGuideDraftV1>;
  generateSketchGuide(
    topic: string,
    intendedSubject?: string,
    difficulty: 'beginner' | 'simple' = 'beginner',
  ): Promise<SvgTopicStrokeGuideDraftV1> {
    return this.request<SvgTopicStrokeGuideDraftV1>(
      '/api/parent/v1/ai/sketch-guides',
      'POST',
      {
        contract: 'SvgTopicStrokeGuideRequestV1',
        topic,
        ...(intendedSubject?.trim() ? { intended_subject: intendedSubject.trim() } : {}),
        difficulty,
      },
      60_000,
    );
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

  listProfileShares(profileId: string, limit = 25, cursor?: string | null): Promise<ParentShareGrantPageV1> {
    if (!isUuid(profileId) || !Number.isInteger(limit) || limit < 1 || limit > 100
      || (cursor !== undefined && cursor !== null
        && (typeof cursor !== 'string' || cursor.length > 2048 || /\p{Cc}/u.test(cursor)))) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    const query = new URLSearchParams({ profile_id: profileId, limit: String(limit) });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.requestValidated(`/v1/parent/share-grants?${query.toString()}`, (value) => {
      const page = readParentShareGrantPageV1(value);
      return page && page.items.every((grant) => grant.profile_id === profileId) ? page : null;
    });
  }

  getProfileShare(grantId: string): Promise<ParentShareGrantV1> {
    if (!isUuid(grantId)) return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    return this.requestValidated(
      `/v1/parent/share-grants/${encodeURIComponent(grantId)}`,
      (value) => {
        const grant = readParentShareGrantV1(value);
        return grant?.share_grant_id === grantId ? grant : null;
      },
    );
  }

  createProfileShare(
    profileId: string,
    grantedFields: ParentShareField[],
    actionIdentity: ParentActionIdentity,
  ): Promise<ParentShareGrantCreatedV1> {
    assertVisibleAsciiKey(actionIdentity);
    const fields = [...new Set(grantedFields)].sort();
    if (!isUuid(profileId) || fields.length < 1 || fields.length > 3
      || fields.some((field) => !PARENT_SHARE_FIELDS.includes(field as ParentShareField))) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    return this.requestValidated(
      '/v1/parent/share-grants',
      (value) => {
        const created = readParentShareGrantCreatedV1(value);
        return created?.profile_id === profileId ? created : null;
      },
      'POST',
      { profile_id: profileId, granted_fields: fields },
      { 'Idempotency-Key': actionIdentity },
    );
  }

  revokeProfileShare(
    grantId: string,
    revision: number,
    actionIdentity: ParentActionIdentity,
  ): Promise<ParentShareGrantV1> {
    assertVisibleAsciiKey(actionIdentity);
    if (!isUuid(grantId) || !Number.isInteger(revision) || revision < 1) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    return this.requestValidated(
      `/v1/parent/share-grants/${encodeURIComponent(grantId)}/revoke`,
      (value) => {
        const grant = readParentShareGrantV1(value);
        return grant?.share_grant_id === grantId ? grant : null;
      },
      'POST',
      undefined,
      { 'If-Match': `"${revision}"`, 'Idempotency-Key': actionIdentity },
    );
  }

  listProfileShareDeliveries(
    grantId: string,
    limit = 25,
    cursor?: string | null,
  ): Promise<ParentShareDeliveryPageV1> {
    if (!isUuid(grantId) || !Number.isInteger(limit) || limit < 1 || limit > 100
      || (cursor !== undefined && cursor !== null
        && (typeof cursor !== 'string' || cursor.length > 2048 || /\p{Cc}/u.test(cursor)))) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.requestValidated(
      `/v1/parent/share-grants/${encodeURIComponent(grantId)}/deliveries?${query.toString()}`,
      (value) => {
        const page = readParentShareDeliveryPageV1(value);
        return page?.share_grant_id === grantId ? page : null;
      },
    );
  }

  listLessonDeliveries(profileId: string, cursor?: string | null) {
    void profileId;
    void cursor;
    return this.unavailable<ParentLessonDeliveryPage>('lesson-history');
  }

  submitLessonFeedback(
    lessonId: string,
    feedbackText: string,
    actionIdentity: ParentActionIdentity,
  ): Promise<ParentLessonFeedbackV1> {
    assertVisibleAsciiKey(actionIdentity);
    const value = feedbackText.trim();
    const characterCount = Array.from(value).length;
    if (!lessonId.trim() || characterCount < 1 || characterCount > 1200) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    return this.requestValidated(
      `/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}/feedback`,
      (payload) => {
        const feedback = readParentLessonFeedbackV1(payload);
        return feedback?.lesson_id === lessonId ? feedback : null;
      },
      'POST',
      { feedback_text: value },
      { 'Idempotency-Key': actionIdentity },
    );
  }

  getParentLessonFeedback(lessonId: string): Promise<ParentLessonFeedbackStateV1> {
    if (!lessonId.trim()) return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    return this.requestValidated(
      `/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}/feedback`,
      (payload) => {
        const state = readParentLessonFeedbackStateV1(payload);
        return state?.lesson_id === lessonId ? state : null;
      },
    );
  }

  listParentLessonFeedbackReplies(
    lessonId: string,
    limit = 25,
    cursor?: string | null,
  ): Promise<ParentLessonFeedbackReplyPageV1> {
    if (!lessonId.trim() || !Number.isInteger(limit) || limit < 1 || limit > 100
      || (cursor !== undefined && cursor !== null
        && (typeof cursor !== 'string' || cursor.length > 768 || /\p{Cc}/u.test(cursor)))) {
      return Promise.reject(new ParentApiError('INVALID_REQUEST', 'local-request', 400));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.requestValidated(
      `/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}/feedback/replies?${query.toString()}`,
      (payload) => {
        const page = readParentLessonFeedbackReplyPageV1(payload);
        return page !== null ? page : null;
      },
    );
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

  registerPushEndpointV1(
    input: PushEndpointRegistrationV1,
    actionIdentity: ParentActionIdentity,
  ): Promise<PushEndpointRegistrationResultV1> {
    assertVisibleAsciiKey(actionIdentity);
    if (input.contract !== 'PushEndpointRegistrationV1'
      || !['WEB', 'ANDROID'].includes(input.platform_kind)
      || !['WEB_PUSH', 'ANDROID_PUSH'].includes(input.provider_kind)
      || typeof input.encrypted_registration_proof !== 'string'
      || input.encrypted_registration_proof.length < 1
      || input.encrypted_registration_proof.length > 8192
      || (input.app_version !== undefined && typeof input.app_version !== 'string')) {
      throw invalidLessonListRequest();
    }
    const body: PushEndpointRegistrationV1 = {
      contract: 'PushEndpointRegistrationV1',
      platform_kind: input.platform_kind,
      provider_kind: input.provider_kind,
      encrypted_registration_proof: input.encrypted_registration_proof,
      ...(input.app_version === undefined ? {} : { app_version: input.app_version }),
    };
    return this.request<unknown>(
      '/v1/notifications/push-endpoints',
      'POST',
      body,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    ).then((payload) => {
      if (!isRecord(payload) || typeof payload.contract !== 'string'
        || typeof payload.endpoint_id !== 'string' || typeof payload.version !== 'number'
        || !Number.isInteger(payload.version) || payload.version < 1) {
        throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 201);
      }
      return payload as unknown as PushEndpointRegistrationResultV1;
    });
  }

  deletePushEndpointV1(
    endpointId: string,
    expectedVersion: number,
    actionIdentity: ParentActionIdentity,
  ): Promise<void> {
    assertVisibleAsciiKey(actionIdentity);
    if (!endpointId.trim() || !Number.isInteger(expectedVersion) || expectedVersion < 1) {
      throw invalidLessonListRequest();
    }
    return this.request<void>(
      `/v1/notifications/push-endpoints/${encodeURIComponent(endpointId)}`,
      'DELETE',
      undefined,
      30_000,
      { 'If-Match': `"${expectedVersion}"`, 'Idempotency-Key': actionIdentity },
    );
  }

  getVideoQuota() {
    return this.readQuota<ParentVideoQuota>(
      '/api/be1/v1/billing/video-quota',
      readParentVideoQuota,
    );
  }

  getQuotaProducts() {
    return this.readQuota<ParentQuotaProduct[]>(
      '/api/be1/v1/billing/video-quota/products',
      readParentQuotaProducts,
    );
  }

  getQuotaInvoices(limit = 50) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      return Promise.reject(new ParentApiError('INVALID_LIMIT', 'local-request'));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    return this.readQuota<ParentQuotaInvoicePage>(
      `/api/be1/v1/billing/video-quota/invoices?${query.toString()}`,
      readParentQuotaInvoices,
    );
  }

  getQuotaPaymentSettings() {
    return this.readQuota<ParentQuotaPaymentSettings>(
      '/api/be1/v1/billing/video-quota/payment-settings',
      readParentQuotaPaymentSettings,
    );
  }

  checkoutQuotaProduct(productId: string, provider: ParentPaymentProvider, actionIdentity: ParentActionIdentity) {
    if (!productId.trim()) throw new ParentApiError('INVALID_REQUEST', 'local-request', 400);
    assertVisibleAsciiKey(actionIdentity);
    return this.readQuota<ParentQuotaCheckoutResult>(
      '/api/be1/v1/billing/video-quota/checkout',
      readParentQuotaCheckoutResult,
      'POST',
      { product_id: productId, provider, payment_mode: 'MANUAL' },
      { 'Idempotency-Key': actionIdentity },
    );
  }

  reconcileQuotaInvoice(invoiceId: string) {
    if (!invoiceId.trim()) throw new ParentApiError('INVALID_REQUEST', 'local-request', 400);
    return this.readQuota<ParentQuotaReconcileResult>(
      `/api/be1/v1/billing/video-quota/invoices/${encodeURIComponent(invoiceId)}/reconcile`,
      readParentQuotaReconcileResult,
      'POST',
    );
  }

  cancelQuotaInvoice(invoiceId: string) {
    if (!invoiceId.trim()) throw new ParentApiError('INVALID_REQUEST', 'local-request', 400);
    return this.readQuota<ParentQuotaCancelResult>(
      `/api/be1/v1/billing/video-quota/invoices/${encodeURIComponent(invoiceId)}/cancel`,
      readParentQuotaCancelResult,
      'POST',
    );
  }

  private async readQuota<T>(
    path: string,
    reader: (value: unknown) => T | null,
    method: 'GET' | 'POST' = 'GET',
    body?: unknown,
    headers: Record<string, string> = {},
  ): Promise<T> {
    const payload = await this.request<unknown>(path, method, body, 30_000, headers);
    const result = reader(payload);
    if (result === null) throw new ParentApiError('INVALID_API_RESPONSE', 'local-response', 200);
    return result;
  }

  private requestValidated<T>(
    path: string,
    reader: (value: unknown) => T | null,
    method: 'GET' | 'POST' = 'GET',
    body?: unknown,
    headers: Record<string, string> = {},
  ): Promise<T> {
    return this.readQuota(path, reader, method, body, headers);
  }

  private async request<T>(
    path: string,
    method: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE',
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
      if (response.status === 204 && response.ok) return undefined as T;
      const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
      if (!response.ok) {
        const allowedCodes = path.startsWith('/v1/activities') || path.endsWith('/activity-selection')
          ? PHASE_A_ACTIVITY_ERROR_CODES
          : path.includes('/context-entries') || path.endsWith('/support-needs')
            ? PHASE_B_PARENT_PROFILE_ERROR_CODES
            : path.endsWith('/context-confirmation')
              ? PHASE_B_PARENT_CONTEXT_CONFIRMATION_ERROR_CODES
              : undefined;
        throw apiErrorFromResponse(payload, response.status, requestId, response.headers, allowedCodes);
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
    PARENT_STORY_RUN_STORE_UNAVAILABLE: 'Buổi học đang tạm thời không khả dụng. Hãy thử tải lại sau.',
    DEPENDENCY_UNAVAILABLE: 'Danh sách hoạt động đang tạm thời không khả dụng. Hãy thử tải lại sau.',
    FORBIDDEN: 'Tài khoản này chưa có quyền thực hiện thao tác vừa chọn.',
    ACCOUNT_SCOPE_UNAVAILABLE: 'Tài khoản phụ huynh chưa sẵn sàng cho thao tác này.',
    LESSON_NOT_FOUND: 'Không tìm thấy bài học này hoặc bài học không còn khả dụng.',
    PARENT_ACTIVITY_SELECTION_REQUIRED: 'Hãy chọn và lưu một hoạt động trước khi tiếp tục câu chuyện.',
    SUPPORT_NEEDS_UNAVAILABLE: 'Mục này chưa khả dụng, hãy thử lại sau.',
    PROFILE_NOT_FOUND: 'Không tìm thấy hồ sơ này hoặc hồ sơ không còn khả dụng.',
    SUBJECT_NOT_CONFIRMED: 'Hãy xem lại và xác nhận chủ thể trước khi chọn hoạt động.',
    RESOURCE_NOT_FOUND: 'Không tìm thấy nội dung hoặc bạn không thể truy cập nội dung này.',
    INVALID_IDEMPOTENCY_KEY: 'Thao tác chưa khớp với lần gửi trước. Hãy tải lại trạng thái rồi thử lại.',
    ACTIVE_RUN_EXISTS: 'Hồ sơ đang có một buổi học chưa hoàn tất.',
    STALE_REVISION: 'Dữ liệu đã thay đổi. Hãy tải lại và kiểm tra trước khi tiếp tục.',
    INVALID_STATE_TRANSITION: 'Trạng thái hồ sơ đã thay đổi. Hãy tải lại hồ sơ.',
    INVALID_REQUEST: 'Yêu cầu chưa hợp lệ. Hãy kiểm tra lại thông tin rồi thử lại.',
    VIDEO_REGENERATION_LIMIT_REACHED: 'Đã dùng hết lượt tạo video của buổi học này. Bạn có thể dừng buổi học trong lịch sử.',
    VIDEO_SAFETY_BLOCKED: 'Video chưa qua kiểm tra an toàn. Hãy xác nhận lại câu chuyện hoặc viết lại.',
    STORAGE_UNAVAILABLE: 'Video đang tạm thời không khả dụng. Hãy thử lại sau.',
    PROVIDER_UNAVAILABLE: 'Dịch vụ tạo nội dung hiện chưa khả dụng. Hãy thử lại sau.',
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
    PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED: 'Chủ đề này chưa có gợi ý trong danh mục. Hãy chọn một chủ đề gợi ý hoặc thử lại sau.',
    PARENT_TOPIC_TEXT_NOT_ALLOWED: 'Chỉ nhập tên chủ đề hoặc đồ vật chung; không nhập tên, thông tin liên hệ hay dữ liệu riêng của trẻ.',
  };
  return messages[code] ?? 'Yêu cầu chưa hoàn tất. Vui lòng kiểm tra lại rồi thử lại sau.';
}

export function apiErrorFromResponse(
  payload: Record<string, unknown> | null,
  status: number,
  fallbackRequestId: string,
  headers?: Headers,
  allowedCodes?: ReadonlySet<string>,
): ParentApiError {
  const detail = isRecord(payload?.detail) ? payload.detail : null;
  const candidateCode = safeErrorCode(payload?.code) ?? safeErrorCode(detail?.code);
  const code = candidateCode && (!allowedCodes || allowedCodes.has(candidateCode)) ? candidateCode : `HTTP_${status}`;
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
  const currentVersion = status === 409 && code === 'STALE_REVISION'
    ? primitiveVersion(payload?.current_version) ?? primitiveVersion(detail?.current_version)
    : undefined;
  const fieldErrors = safeFieldErrors(payload?.field_errors) ?? safeFieldErrors(detail?.field_errors);
  const metadata: ParentApplicationErrorMetadata = {
    ...(correlationId ? { correlationId } : {}),
    ...(retryableValue === undefined ? {} : { retryable: retryableValue }),
    ...(retryAfterValue === undefined ? {} : { retryAfterSeconds: retryAfterValue }),
    ...(currentVersion === undefined ? {} : { currentVersion }),
    ...(fieldErrors ? { fieldErrors } : {}),
  };
  const displayMessage = code === 'PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED' || code === 'PARENT_TOPIC_TEXT_NOT_ALLOWED'
    ? safeApiDisplayMessage(detail?.message)
    : undefined;
  return new ParentApiError(code, requestId, status, metadata, displayMessage);
}

function safeApiDisplayMessage(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  const message = value.trim();
  if (message.length < 2 || message.length > 240 || /[\u0000-\u001f\u007f]/.test(message)) return undefined;
  return message;
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
    entry_kind: 'entry_kind',
    short_text: 'short_text',
    source_kind: 'source_kind',
    approximate_date: 'approximate_date',
    selected_context_entry_ids: 'selected_context_entry_ids',
    category: 'category',
    note: 'note',
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
    'DIAGNOSIS_LIKE',
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

function isLessonExportV1(value: unknown, requestedLessonId: string): value is LessonExportV1 {
  if (!isRecord(value)
    || value.contract !== 'LessonExportV1'
    || value.lesson_id !== requestedLessonId
    || typeof value.version_id !== 'string' || !value.version_id.trim()
    || typeof value.version_no !== 'number' || !Number.isInteger(value.version_no) || value.version_no < 1
    || typeof value.content_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(value.content_sha256)
    || typeof value.title !== 'string' || typeof value.topic !== 'string'
    || value.locale !== 'vi-VN'
    || typeof value.target_age_band_ref !== 'string' || !value.target_age_band_ref.trim()
    || typeof value.target_age_band_version !== 'number'
    || !Number.isInteger(value.target_age_band_version) || value.target_age_band_version < 1
    || !isStringArray(value.objectives)
    || typeof value.drawing_subject !== 'string'
    || typeof value.drawing_steps_text !== 'string'
    || typeof value.subject_learning_notes !== 'string'
    || (value.script_direction !== null && typeof value.script_direction !== 'string')
    || typeof value.script_following_allowed !== 'boolean'
    || !Array.isArray(value.activities)
    || (value.access_source !== 'PUBLIC' && value.access_source !== 'SHARED')
    || (value.access_expires_at !== null && typeof value.access_expires_at !== 'string')) return false;

  return value.activities.every((activity) => isRecord(activity)
    && typeof activity.title === 'string'
    && typeof activity.objective === 'string'
    && typeof activity.materials_text === 'string'
    && typeof activity.preparation_text === 'string'
    && typeof activity.instructions_text === 'string'
    && typeof activity.observation_notes === 'string'
    && typeof activity.safety_notes === 'string'
    && (activity.activity_kind === 'outdoor' || activity.activity_kind === 'indoor' || activity.activity_kind === 'mixed'));
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string');
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** Validate the optional selected-activity projection when present; older Phase A runs omit it. */
function validateRunMainActivity(run: ParentStoryRunV1, requestId: string): ParentStoryRunV1 {
  if (run.main_activity === undefined || run.main_activity === null) return run;
  const mainActivity = readMainActivityV1(run.main_activity);
  if (!mainActivity) throw new ParentApiError('INVALID_API_RESPONSE', requestId, 200);
  return { ...run, main_activity: mainActivity };
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
