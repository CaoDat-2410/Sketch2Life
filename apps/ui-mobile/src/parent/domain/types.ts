export type ParentUser = { subject: string; email: string; role: 'parent' };

export type ParentProfile = {
  parent_profile_id: string;
  state: 'ACTIVE' | 'ARCHIVED' | 'DELETED';
  current_revision: {
    profile_revision_id: string;
    revision: number;
    age_months: number;
    display_name: string;
    interests_summary: string;
    revision_sha256: string;
    created_at: string;
  };
  authorization_state: 'GRANTED' | 'REVOKED' | 'EXPIRED' | null;
  authorization_policy_version: string | null;
  authorization_current: boolean;
  created_at: string;
  updated_at: string;
};

export type ConsentPolicy = {
  purpose_code: string;
  policy_version: string;
  consent_text: string;
  consent_text_sha256: string;
};

export type LessonSummary = {
  contract?: 'ParentLessonSummaryV1';
  lesson_id: string;
  version_id: string;
  title: string;
  topic: string;
  target_age_band_ref: string;
  target_age_band_version: number;
  activity_count: number;
  access_source: 'PUBLIC' | 'SHARED';
};

export type ParentLessonListOptions = {
  source?: 'ALL' | 'PUBLIC' | 'SHARED';
  q?: string;
  topic?: string;
  ageBand?: { ref: string; version: number };
  cursor?: string | null;
  limit?: number;
};

export type ParentLessonPage = {
  contract: string;
  items: LessonSummary[];
  next_cursor: string | null;
};

export type Activity = {
  title: string;
  objective: string;
  materials_text: string;
  preparation_text: string;
  instructions_text: string;
  observation_notes: string;
  safety_notes: string;
  activity_kind: 'outdoor' | 'indoor' | 'mixed';
};

export type SuggestedActivity = Activity & {
  source: 'PINNED_LESSON' | 'PUBLISHED_SHARED_LESSON' | 'AI_GENERATED_DRAFT';
  source_lesson_id: string | null;
  source_lesson_title: string | null;
  source_lesson_version_id: string | null;
  source_content_sha256: string | null;
  source_activity_index: number | null;
  match_reason: string | null;
};

export type LessonDetail = Omit<LessonSummary, 'contract'> & {
  contract: 'ParentLessonDetailV1';
  version_no: number;
  content_sha256: string;
  objectives: string[];
  drawing_subject: string;
  drawing_steps_text: string;
  subject_learning_notes: string;
  script_direction: string | null;
  script_following_allowed: boolean;
  access_expires_at: string | null;
  activities: Activity[];
};

export type LessonInvitation = {
  contract?: 'LessonAccessGrantV1';
  access_grant_id: string;
  lesson_id: string;
  version_id: string;
  audience_kind: string;
  capability: string;
  state: string;
  expires_at: string | null;
  revision: number;
};

export type ParentGroupInvitation = {
  contract?: 'ParentGroupMembershipV1';
  membership_id: string;
  parent_group_id: string;
  state: 'INVITED' | 'ACTIVE' | 'REVOKED' | 'EXPIRED' | 'DECLINED';
  invited_at: string;
  expires_at: string | null;
  revision: number;
};

export type ParentGroupMembershipV1 = {
  contract: 'ParentGroupMembershipV1';
  membership_id: string;
  parent_group_id: string;
  organization_id?: string;
  state: 'INVITED' | 'ACTIVE' | 'REVOKED' | 'EXPIRED' | 'DECLINED';
  invited_at: string;
  expires_at: string | null;
  accepted_at: string | null;
  revision: number;
  revision_source: string;
};

export type ParentGroupMembershipPage = {
  contract: string;
  items: ParentGroupMembershipV1[];
  next_cursor: string | null;
};

export type ParentCandidate = {
  candidate_subject?: string | null;
  visible_features: string[];
  confidence: number;
  adult_confirmation_required: true;
  decision: string;
};

export type StoryRun = {
  run_id: string;
  run_state: string;
  parent_profile_id: string;
  profile_revision_ref: string;
  context_revision: number;
  context_snapshot: {
    schema_version: string;
    profile_revision_ref: string;
    age_months: number;
    interests_summary: string;
    topic: string;
    adult_confirmed_idea: string;
    consent_policy_version: string;
  };
  context_snapshot_sha256: string;
  lesson_pin_snapshot: {
    lesson_id: string;
    version_id: string;
    version_no: number;
    content_sha256: string;
    target_age_band_ref?: string | null;
    target_age_band_version?: number | null;
    title: string;
    topic: string;
    drawing_subject: string;
    subject_learning_notes: string;
    script_direction: string | null;
    script_following_allowed: boolean;
    activities: Activity[];
  } | null;
  current_input_revision: number | null;
  understanding_revision: number | null;
  subject_label: string | null;
  candidate: ParentCandidate | null;
  story_revision_id: string | null;
  story_revision_no: number | null;
  story_status: string | null;
  story_sha256: string | null;
  story: unknown;
  job_state: string | null;
  retryable: boolean;
  error_code: string | null;
};

/** FEAT-081 C3b: content-free history item (no story, context, topic or media). */
export type ParentStoryRunSummary = {
  run_id: string;
  parent_profile_id: string | null;
  run_state: string;
  revision: number;
  deleting: boolean;
  can_cancel: boolean;
  can_delete: boolean;
  created_at: string;
  updated_at: string;
};

export type ParentStoryRunHistoryPage = {
  request_id: string;
  items: ParentStoryRunSummary[];
  next_cursor: string | null;
};

/** FR-C-08 content-free projection of a run from DELETE_PENDING on (Contract Draft 11 3.4). */
export type ParentStoryRunLifecycleV1 = {
  run_id: string;
  run_state: 'DELETE_PENDING' | 'DELETED';
  revision: number;
  version: number;
  lifecycle_request_ref: string;
  purge_state: 'PENDING' | 'COMPLETED';
};

export type ParentStoryRunLifecycleEnvelopeV1 = {
  request_id: string;
  lifecycle: ParentStoryRunLifecycleV1;
};

/** A run read is the full run before DELETE_PENDING and the lifecycle projection from then on. */
export type ParentStoryRunResultV1 = ParentStoryRunEnvelopeV1 | ParentStoryRunLifecycleEnvelopeV1;

export function isParentStoryRunLifecycleEnvelope(
  value: ParentStoryRunResultV1,
): value is ParentStoryRunLifecycleEnvelopeV1 {
  return 'lifecycle' in value && typeof value.lifecycle === 'object' && value.lifecycle !== null;
}

export type ParentRunLifecycleReceipt = {
  contract: 'ParentRunLifecycleResponseV1';
  request_id: string;
  lifecycle_request_id: string;
  story_run_id: string;
  operation: 'CANCEL' | 'DELETE';
  run_state: 'DELETE_PENDING';
  purge_state: 'PENDING';
  job_cancel_state: 'NOT_CONNECTED';
  created_at: string;
};

export type ParentProfileShareGrant = {
  contract: 'ParentProfileShareGrantV1';
  grant_id: string;
  parent_profile_id: string;
  teacher_subject: string;
  managed_profile_ref: string | null;
  state: 'INVITED' | 'ACTIVE' | 'DECLINED' | 'REVOKED' | 'EXPIRED';
  created_at: string;
  expires_at: string | null;
  accepted_at: string | null;
  revoked_at: string | null;
  revision: number;
};

export type ParentProfileSharePage = {
  contract: 'ParentProfileSharePageV1';
  items: ParentProfileShareGrant[];
};

export type ParentNotification = {
  contract: 'NotificationV1';
  inbox_item_id: string;
  notification_type: string;
  template_version: number;
  safe_parameters: Record<string, boolean | number | string>;
  created_at: string;
  read_at: string | null;
  expires_at: string | null;
};

export type ParentNotificationPage = {
  contract: 'NotificationPageV1';
  items: ParentNotification[];
  next_cursor: string | null;
  unread_count: number;
};

export type ParentNotificationReadAllV1 = {
  contract: 'NotificationReadAllV1';
  marked_count: number;
};

export type PushEndpointRegistrationV1 = {
  contract: 'PushEndpointRegistrationV1';
  platform_kind: 'WEB' | 'ANDROID';
  provider_kind: 'WEB_PUSH' | 'ANDROID_PUSH';
  encrypted_registration_proof: string;
  app_version?: string;
};

export type PushEndpointRegistrationResultV1 = {
  contract: string;
  endpoint_id: string;
  version: number;
};

/** Parent-scoped BE1 quota summary. Field names mirror the billing service response. */
export type ParentQuotaGrant = {
  grant_id: string;
  kind: string;
  units: number;
  used: number;
  available: number;
  period: string | null;
  expires_at: string | null;
};

export type ParentQuotaAllocation = {
  allocated_unused_units: number;
  available_school_units: number;
  teachers: {
    teacher_ref: string;
    allocation_id: string;
    available_units: number;
    revision: number;
    active: boolean;
  }[];
};

export type ParentVideoQuota = {
  owner_kind: string;
  available_units: number;
  granted_units: number;
  used_units: number;
  grants: ParentQuotaGrant[];
  allocation: ParentQuotaAllocation | null;
};

export type ParentQuotaProduct = {
  product_id: string;
  offer_id: string;
  version: number;
  display_name: string;
  offer_kind: 'MONTHLY' | 'TOP_UP';
  cycle_months: number | null;
  units: number;
  amount_vnd: number;
  active: boolean;
};

export type ParentQuotaPaymentAttempt = {
  provider: string;
  state: string;
  checkout_url: string | null;
  expires_at: string | null;
};

export type ParentQuotaInvoice = {
  invoice_id: string;
  units: number;
  amount_vnd: number;
  state: string;
  provider: string;
  payment_mode: string;
  created_at: string | null;
  attempts: ParentQuotaPaymentAttempt[];
};

export type ParentQuotaInvoicePage = { items: ParentQuotaInvoice[]; total: number };

export type ParentQuotaPaymentSettings = {
  real_payments_enabled: boolean;
  momo_checkout_enabled: boolean;
  vnpay_checkout_enabled: boolean;
  momo_sandbox_enabled: boolean;
  vnpay_sandbox_enabled: boolean;
  monthly_auto_renew_enabled: boolean;
};

export type ParentQuotaCheckoutResult = {
  invoice_id: string;
  state: string;
  checkout_url: string | null;
};

export type ParentQuotaReconcileResult = {
  invoice_id: string;
  state: string;
  reconciled: boolean;
};

export type ParentQuotaCancelResult = {
  invoice_id: string;
  state: string;
  canceled: boolean;
  reconciled: boolean;
};

export type ParentLessonDelivery = {
  contract: 'ParentLessonDeliveryV1';
  occurrence_id: string;
  lesson_id: string;
  version_id: string;
  title: string;
  topic: string;
  delivered_at: string;
  feedback: {
    feedback_id: string;
    feedback_text: string;
    created_at: string;
    updated_at: string;
  } | null;
  replies: Array<{ reply_id: string; reply_text: string; created_at: string }>;
};

export type ParentLessonDeliveryPage = {
  contract: 'ParentLessonDeliveryPageV1';
  items: ParentLessonDelivery[];
  next_cursor: string | null;
};

export type StoryDraft = {
  schema_version: 'sketch2life.story-revision.v1';
  language: 'vi';
  revisionId?: string;
  revisionNo?: number;
  sha256?: string;
  title: string;
  story: { opening: string; middle: string; ending: string };
  duration_ms: number;
  scenes: Array<{
    scene_index: number;
    title: string;
    action: string;
    narration: string;
    start_ms: number;
    duration_ms: number;
  }>;
};

export type LessonPin = NonNullable<StoryRun['lesson_pin_snapshot']>;

/** I2 profile reference returned by the versioned parent-profile routes. */
export type ParentProfileReferenceV1 = {
  profile_id: string;
  revision_no: number;
  revision_hash: string;
};

/** Active profile view. The list route contains active profiles only. */
export type ParentProfileViewV1 = ParentProfileReferenceV1 & {
  state: 'ACTIVE';
  display_name: string;
  age_months: number;
  age_band_ref: string | null;
  age_band_version: string | null;
  interests_summary: string | null;
  data_origin: string;
};

/** GET-by-ID may return this view while an asynchronous deletion is pending. */
export type ParentProfileDeletePendingV1 = {
  profile_id: string;
  state: 'DELETE_PENDING';
  request_id: string;
};

export type ParentProfileRecordV1 = ParentProfileViewV1 | ParentProfileDeletePendingV1;

export type ParentProfilePageV1 = {
  items: ParentProfileViewV1[];
  next_cursor: string | null;
  request_id: string;
};

export type ParentProfileCreateV1 = {
  display_name: string;
  age_months: number;
  interests_summary?: string | null;
};

export type ParentProfilePatchV1 = {
  expected_revision: number;
  display_name: string;
  age_months: number;
  interests_summary?: string | null;
};

export type ParentContextEntryKind = 'OBSERVATION' | 'ACHIEVEMENT' | 'OUTSIDE_EXPERIENCE';

export type ParentContextEntryV1 = {
  context_entry_id: string;
  entry_kind: ParentContextEntryKind;
  short_text: string;
  source_kind: string;
  approximate_date: string | null;
  created_at: string;
};

export type ParentContextEntryListView = {
  context_entries: ParentContextEntryV1[];
  next_cursor: string | null;
  limit: number;
};

/** source_ref is part of the server contract, but this client never sends it. */
export type CreateParentContextEntryRequest = {
  entry_kind: ParentContextEntryKind;
  short_text: string;
  source_kind: string;
  source_ref?: string;
  approximate_date?: string;
};

export type ParentContextEntryEnvelope = {
  context_entry: ParentContextEntryV1;
};

export type ParentSupportNeedsV1 = {
  contract: 'ParentSupportNeedsV1';
  profile_id: string;
  revision: number;
  category: string | null;
  note: string | null;
};

export type SupportNeedsPutV1 = {
  expected_revision: number;
  category: string | null;
  note: string | null;
};

export type ParentSupportNeedsWriteV1 = {
  contract: 'ParentSupportNeedsWriteV1';
  profile_id: string;
  revision: number;
};

export type ParentLessonVersionPinV1 = {
  lesson_id: string;
  version_id: string;
  content_sha256: string;
};

/** V1 context contract intentionally has no consent-policy field. */
export type ParentStoryContextV1 = {
  schema_version: 'sketch2life.parent-context.v1';
  profile_revision_ref: string;
  topic: string;
  adult_confirmed_idea: string;
  age_months: number;
  interests_summary: string;
};

export type ParentRunContextSnapshotV1 = ParentStoryContextV1;

export type ParentRunContextSnapshotV2 = {
  schema_version: 'sketch2life.parent-context.v2';
  profile_revision_ref: string;
  age_months: number;
  interests_summary: string;
  topic: string;
  adult_confirmed_idea: string;
  selected_entries: Array<{
    kind: ParentContextEntryKind;
    text: string;
  }>;
};

export function isParentRunContextSnapshotV2(
  snapshot: ParentRunContextSnapshotV1 | ParentRunContextSnapshotV2,
): snapshot is ParentRunContextSnapshotV2 {
  return snapshot.schema_version === 'sketch2life.parent-context.v2';
}

/** V1 StoryRun is separate from the legacy consent-bearing StoryRun type. */
export type ParentLessonPinSnapshotV1 = ParentLessonVersionPinV1 & {
  schema_version: 'sketch2life.parent-lesson-pin.v1';
  version_no: number;
  target_age_band_ref?: string | null;
  target_age_band_version?: number | null;
  title: string;
  topic: string;
  drawing_subject: string;
  subject_learning_notes: string;
  script_direction?: string | null;
  script_following_allowed: boolean;
  activities: Activity[];
};

/** The frozen M2 projection states (the parity test pins this list). */
export type ParentStoryRunStateV1 =
  | 'INPUT_PROCESSING'
  | 'SUBJECT_REVIEW'
  | 'PREPARATION_REVIEW'
  | 'SCRIPT_GENERATING'
  | 'SCRIPT_GENERATION_UNKNOWN'
  | 'SCRIPT_REVIEW'
  | 'VIDEO_ADMISSION_PENDING'
  | 'DELETE_PENDING'
  | 'FAILED'
  | 'COMPLETED';

/** Goal v3 Phase B states the server can now answer (SRS l.394); additive to the frozen list. */
export type ParentStoryRunPhaseBStateV1 =
  | 'DRAFT'
  | 'INPUT_REVIEW'
  | 'STORY_GENERATING'
  | 'VIDEO_QUEUED'
  | 'VIDEO_GENERATING'
  | 'VIDEO_SAFETY_VALIDATING'
  | 'VIDEO_READY'
  | 'SAFETY_BLOCKED'
  | 'ABANDONED'
  | 'DELETED';

export type ParentStoryStatusV1 =
  | 'GENERATING'
  | 'DRAFT'
  | 'CONFIRMED'
  | 'SUPERSEDED'
  | 'FAILED'
  | 'AWAITING_RECONCILIATION';

export type ParentStoryJobStateV1 =
  | 'QUEUED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'AWAITING_RECONCILIATION';

export type ParentActivityRefV1 = {
  lesson_id: string;
  version_id: string;
  content_sha256: string;
  activity_index: number;
};

export type ParentActivityV1 = {
  activity_ref: ParentActivityRefV1 | null;
  title: string;
  objective: string;
  materials_text: string;
  preparation_text: string;
  instructions_text: string;
  observation_notes: string;
  safety_notes: string;
  activity_kind: 'outdoor' | 'indoor' | 'mixed';
  source: 'PINNED_LESSON' | 'PUBLIC' | 'SHARED' | 'AI_DRAFT';
  lesson_title: string;
  lesson_topic: string;
};

export type ParentActivityListV1 = {
  request_id: string;
  items: ParentActivityV1[];
  basis: {
    age_band: '36-71' | '72-107' | '108-120';
    pinned_lesson: boolean;
    no_candidate: boolean;
  };
};

export type ParentActivitySuggestionSetV1 = Readonly<{
  contract: 'ParentActivitySuggestionSetV1';
  request_id: string;
  story_run_id: string;
  suggestion_set_id: string;
  set_revision: number;
  understanding_revision: number;
  selection_mode: 'CATALOG_SELECTION' | 'AI_GENERATED_FALLBACK';
  catalog_candidate_count: number;
  activities_snapshot_sha256: string;
  review_required: true;
  modal_call_id: string | null;
  activities: ReadonlyArray<SuggestedActivity>;
}>;

export type ParentActivitySelectionReceiptV1 = Readonly<{
  contract: 'ParentActivitySelectionReceiptV1';
  request_id: string;
  story_run_id: string;
  suggestion_set_id: string;
  activity_selection_id: string;
  selection_revision: number;
  understanding_revision: number;
  activity_index: number;
  activity_snapshot_sha256: string;
  persisted_at: string;
}>;

export type ParentTopicCardV1 = Readonly<{
  topic_id: string;
  title_vi: string;
  description_vi: string;
}>;

export type ParentTopicSuggestionSetV1 = Readonly<{
  contract: 'ParentTopicSuggestionSetV1';
  set_id: string;
  draft_id: string;
  catalog_revision: string;
  cards: ReadonlyArray<ParentTopicCardV1>;
  excluded_set_ids: ReadonlyArray<string>;
}>;

export type ParentDrawingSubjectCardV1 = Readonly<{
  subject_id: string;
  title_vi: string;
  guide_subject: string;
  relation_to_topic_vi?: string | null;
}>;

export type ParentDrawingSubjectSuggestionSetV1 = Readonly<{
  contract: 'ParentDrawingSubjectSuggestionSetV1';
  set_id: string;
  draft_id: string;
  topic_id: string;
  topic: string;
  catalog_revision: string;
  generation_source: 'CURATED_CATALOG' | 'QWEN_DRAFT';
  review_required: true;
  cards: ReadonlyArray<ParentDrawingSubjectCardV1>;
  excluded_set_ids: ReadonlyArray<string>;
}>;

export type ParentCustomSubjectValidationV1 = Readonly<{
  contract: 'ParentCustomSubjectValidationV1';
  decision: 'ON_TOPIC' | 'OUT_OF_TOPIC' | 'NEEDS_CLARIFICATION';
  normalized_subject: string | null;
  message_vi: string;
}>;

/** Phase D can add the suggestion-round variant without changing this method's callers. */
export type ParentActivitySelectionRequestV1 =
  | { expected_revision: number; activity: ParentActivityRefV1 }
  | { expected_revision: number; round_id: string; draft_index: number };

export type ParentMainActivityV1 = {
  state: 'NOT_SELECTED' | 'SELECTED';
  selected: ParentActivityV1 | null;
  selected_at: string | null;
};

type ParentPostVideoActivityBaseV1 = Omit<ParentActivityV1, 'activity_ref' | 'source'> & {
  is_main: boolean;
};

export type ParentPostVideoActivityV1 =
  | (ParentPostVideoActivityBaseV1 & {
    activity_ref: ParentActivityRefV1;
    source: 'PINNED_LESSON' | 'PUBLIC' | 'SHARED';
  })
  | (ParentPostVideoActivityBaseV1 & {
    activity_ref: null;
    source: 'AI_DRAFT';
  });

export type ParentDrawingCandidateDecisionV1 =
  | 'REVIEW_REQUIRED'
  | 'CONFIRMED_BY_ADULT'
  | 'CORRECTED_BY_ADULT';

export type ParentDrawingCandidateV1 = {
  candidate_subject: string | null;
  visible_features: string[];
  confidence: number;
  adult_confirmation_required: true;
  decision: ParentDrawingCandidateDecisionV1;
};

export type ParentStoryDisplayV1 = {
  schema_version: 'sketch2life.story-revision.v1';
  language: 'vi';
  title: string;
  story: { opening: string; middle: string; ending: string };
  duration_ms: number;
  scenes: Array<{
    scene_index: number;
    title: string;
    action: string;
    narration: string;
    start_ms: number;
    duration_ms: number;
  }>;
};

export type ParentStoryRunV1 = {
  run_id: string;
  run_revision: number;
  run_state: ParentStoryRunStateV1 | ParentStoryRunPhaseBStateV1;
  parent_profile_id: string;
  profile_revision_ref: string;
  context_revision: number;
  context_confirmed: boolean;
  context_snapshot: ParentRunContextSnapshotV1 | ParentRunContextSnapshotV2;
  context_snapshot_sha256: string;
  lesson_pin_snapshot?: ParentLessonPinSnapshotV1 | null;
  current_input_revision: number | null;
  understanding_revision: number | null;
  subject_label: string | null;
  candidate: ParentDrawingCandidateV1 | null;
  story_revision_id: string | null;
  story_revision_no: number | null;
  story_status: ParentStoryStatusV1 | null;
  story_sha256: string | null;
  story: ParentStoryDisplayV1 | null;
  job_state: ParentStoryJobStateV1 | null;
  main_activity?: ParentMainActivityV1 | null;
  post_video_activities?: ParentPostVideoActivityV1[] | null;
  story_confirmation_required?: boolean;
  retryable: boolean;
  error_code: string | null;
  created_at: string;
  updated_at: string;
  /** StoryRunDetailV1 additions (T-1c, SRS l.1811); absent on older servers, so always optional. */
  video?: ParentStoryRunVideoV1 | null;
  quota?: ParentStoryQuotaSummaryV1;
  timeline?: ParentStoryTimelineEventV1[];
};

export type ParentStoryRunCreateV1 = {
  parent_profile_id: string;
  topic: string;
  adult_confirmed_idea: string;
  lesson_version?: ParentLessonVersionPinV1 | null;
};

export type ParentStoryRunEnvelopeV1 = {
  request_id: string;
  story_run: ParentStoryRunV1;
};

export type ParentActiveStoryRunEnvelopeV1 = {
  request_id: string;
  story_run: ParentStoryRunV1 | null;
};

export type ParentStoryContextConfirmationV1 = {
  expected_context_revision: number;
  context_snapshot_sha256: string;
  confirmed: true;
  selected_context_entry_ids?: readonly string[];
};

export type ParentStorySubjectConfirmationV1 = {
  request_id: string;
  story_run_id: string;
  understanding_revision: number;
  decision: 'CONFIRMED';
};

/**
 * Phase B 202 body of the subject confirmation (SRS l.1666). The frozen `ParentStorySubjectConfirmationV1`
 * above only knows `CONFIRMED`; an edited subject can also answer `RERUN_REQUESTED` (SRS l.394, l.1413):
 * the visual understanding runs again and the new revision is confirmed in a second call.
 */
export type ParentStorySubjectConfirmationAcceptedV1 = Omit<ParentStorySubjectConfirmationV1, 'decision'> & {
  decision: ParentStorySubjectConfirmationV1['decision'] | 'RERUN_REQUESTED';
  run_revision?: number;
};

export type ParentStoryScriptConfirmationV1 = ParentStoryRunEnvelopeV1;

export type ParentStoryRevisionResultV1 = {
  request_id?: string;
  modal_call_id?: string;
  story?: unknown;
  story_sha256?: string;
  story_run?: ParentStoryRunV1;
};

// ---------------------------------------------------------------------------------------------
// Goal v3 Phase B Parent contracts (backend `bb73e958..00d5ee60`; SRS l.1664-1676, l.1811).
// Plain TypeScript shapes; every reader in `application/parentPhaseB.ts` validates at runtime.
// ---------------------------------------------------------------------------------------------

export type ParentAnalysisStateV1 = 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'AWAITING_RECONCILIATION';

/** 202 of `POST /v1/story-runs/{id}/assets` (T-2b). No job reference exists (Q-J). */
export type ParentRunAssetAcceptedV1 = {
  request_id: string;
  story_run_id: string;
  asset_ref: string;
  asset_kind: 'DRAWING';
  asset_state: 'READY';
  input_revision: number;
  run_revision: number;
  run_state: string;
  analysis_state: ParentAnalysisStateV1;
};

export type ParentIdeaSourceV1 = 'TEXT' | 'VOICE' | 'TEXT_AND_VOICE';
export type ParentTranscriptStateV1 = 'NONE' | 'PENDING' | 'NEEDS_CONFIRMATION' | 'CONFIRMED' | 'FAILED';

/** Body of `POST /v1/story-runs/{id}/idea`: text and/or audio, or one transcript correction (T-2c). */
export type ParentRunIdeaRequestV1 =
  | { expected_run_revision: number; text?: string; audio_ref?: string }
  | { expected_run_revision: number; transcript_correction: { base_revision: number; text: string } };

export type ParentRunIdeaAcceptedV1 = {
  request_id: string;
  story_run_id: string;
  input_revision: number;
  run_revision: number;
  run_state: string;
  idea_source: ParentIdeaSourceV1 | null;
  transcript: { transcript_revision: number; state: ParentTranscriptStateV1 } | null;
};

/** The adult's read of the current transcript; a child's words, never cached or logged. */
export type ParentRunTranscriptV1 = {
  story_run_id: string;
  transcript_revision: number | null;
  state: ParentTranscriptStateV1;
  origin: 'ASR' | 'ADULT_CORRECTION' | null;
  text: string | null;
  transcript_sha256: string | null;
  language: string | null;
  error_code: string | null;
  run_revision: number;
};

export type ParentTranscriptConfirmedV1 = {
  request_id: string;
  story_run_id: string;
  transcript_revision: number;
  state: 'CONFIRMED';
  run_revision: number;
  run_state: string;
};

/** 202 of `POST /v1/story-runs/{id}/story-rewrites` (T-2d). No job reference exists (Q-J). */
export type ParentStoryRewriteAcceptedV1 = {
  request_id: string;
  story_run_id: string;
  story_revision_no: number;
  run_revision: number;
  run_state: 'SCRIPT_GENERATING';
};

export type ParentStoryRewriteRequestV1 = {
  expected_story_revision: number;
  expected_story_sha256?: string;
  hint?: string;
};

export type ParentVideoReasonCodeV1 = 'QUALITY_LOW' | 'NOT_MATCHING_STORY' | 'CONTENT_CONCERN' | 'OTHER';

export type ParentVideoGenerationStateV1 =
  | 'ADMISSION_PENDING'
  | 'ADMISSION_REJECTED'
  | 'ACCEPTED'
  | 'QUEUED'
  | 'GENERATING'
  | 'TECHNICAL_VALIDATING'
  | 'SAFETY_VALIDATING'
  | 'READY'
  | 'SAFETY_BLOCKED'
  | 'FAILED'
  | 'REJECTED_BY_ADULT'
  | 'SUPERSEDED';

export type ParentVideoRequestV1 = {
  expected_revision: number;
  story_sha256: string;
  quality_reason_code?: ParentVideoReasonCodeV1;
};

export type ParentVideoUnsuitableRequestV1 = {
  expected_revision: number;
  generation_id: string;
  reason_code: ParentVideoReasonCodeV1;
};

export type ParentVideoGenerationAcceptedV1 = {
  request_id: string;
  video_generation: {
    generation_id: string;
    state: ParentVideoGenerationStateV1;
    generation_no: number | null;
    kind: 'INITIAL' | 'QUALITY_REGEN';
    job_id: string | null;
    run_state: string;
    run_revision: number;
  };
};

export type ParentVideoSceneStateV1 = { scene_index: number; state: 'QUEUED' | 'GENERATING' | 'READY' | 'FAILED' };

export type ParentStoryRunVideoV1 = {
  current_generation_id: string;
  generation_no: number | null;
  kind: 'INITIAL' | 'QUALITY_REGEN';
  state: ParentVideoGenerationStateV1;
  job: {
    job_id: string;
    state: 'queued' | 'running' | 'succeeded' | 'failed_exhausted' | 'blocked_unsafe';
    stage: string | null;
    retryable: boolean;
    error_code: string | null;
  } | null;
  scenes: ParentVideoSceneStateV1[];
  playback: { state: 'AVAILABLE' | 'HIDDEN' | 'UNAVAILABLE'; asset_ref: string | null; token_route: string | null };
  /** The three-request run cap of FR-AI-07 (l.573), not the monthly quota. */
  video_requests_used: number;
  video_requests_remaining: number;
  admission_pending: boolean;
  history: Array<{
    generation_id: string;
    generation_no: number;
    kind: 'INITIAL' | 'QUALITY_REGEN';
    state: ParentVideoGenerationStateV1;
  }>;
};

/** Constant `UNAVAILABLE` marker until a Billing reader exists (TD-22); figures are null, never zero. */
export type ParentStoryQuotaSummaryV1 = {
  state: 'UNAVAILABLE';
  granted: number | null;
  used: number | null;
  available: number | null;
  month: string | null;
};

export type ParentStoryTimelineEventV1 = { event: string; at: string };

/** 200 of `POST /v1/story-runs/{id}/playback-token` (T-1c). The token is a bearer secret. */
export type ParentPlaybackGrantV1 = {
  token: string;
  expires_at: string;
  stream_path: string;
  media_type: 'video/mp4';
  asset_ref: string;
};

export type ParentPlaybackTokenResponseV1 = {
  request_id: string;
  playback: ParentPlaybackGrantV1;
};

/** What a native player needs: the stream address and the two headers (never a token in a URL). */
export type ParentPlaybackSourceV1 = {
  uri: string;
  headers: Record<string, string>;
  /** Epoch milliseconds when the grant stops working. */
  expiresAtMs: number;
};
