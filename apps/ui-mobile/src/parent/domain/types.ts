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
  state: 'INVITED' | 'ACTIVE' | 'REVOKED' | 'EXPIRED';
  invited_at: string;
  expires_at: string | null;
  revision: number;
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

export type ParentStoryRunHistoryPage = {
  contract: 'ParentStoryRunHistoryPageV1';
  items: StoryRun[];
  next_cursor: string | null;
};

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

export type ParentAudioTranscription = {
  contract: 'ParentAudioTranscriptionV1';
  request_id: string;
  story_run_id: string;
  audio_input_id: string;
  transcript_revision_id: string;
  transcript_revision_no: number;
  transcript_raw: string;
  language: 'vi';
  language_probability: number;
  state: 'DRAFT' | 'CONFIRMED' | 'SUPERSEDED';
  review_required: true;
  created_at: string;
};

export type ParentTranscriptConfirmation = {
  contract: 'ParentTranscriptConfirmationV1';
  request_id: string;
  story_run_id: string;
  transcript_revision_id: string;
  transcript_revision_no: number;
  transcript_text: string;
  run_input_revision: number;
  context_revision: number;
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
  contract: 'NotificationInboxItemV1';
  notification_id: string;
  kind: 'PROFILE_SHARE_INVITATION' | 'PROFILE_SHARE_ACCEPTED' | 'LESSON_FEEDBACK' | 'LESSON_REPLY';
  title: string;
  resource_kind: string | null;
  resource_ref: string | null;
  created_at: string;
  read_at: string | null;
};

export type ParentNotificationPage = {
  contract: 'NotificationInboxPageV1';
  items: ParentNotification[];
  next_cursor: string | null;
};

export type ParentVideoQuota = {
  contract: 'ParentVideoQuotaSummaryV1';
  configuration_state: 'CONFIGURED' | 'NOT_CONFIGURED';
  period_start: string;
  period_end: string;
  granted: number | null;
  used: number | null;
  available: number | null;
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

export type ParentLessonVersionPinV1 = {
  lesson_id: string;
  version_id: string;
  content_sha256: string;
};

/** V1 context contract intentionally has no consent-policy field. */
export type ParentStoryContextV1 = {
  topic: string;
  adult_confirmed_idea: string;
  age_months?: number;
  interests_summary?: string | null;
};

/** V1 StoryRun is separate from the legacy consent-bearing StoryRun type. */
export type ParentLessonPinSnapshotV1 = ParentLessonVersionPinV1 & {
  schema_version?: 'sketch2life.parent-lesson-pin.v1';
  version_no?: number;
  target_age_band_ref?: string | null;
  target_age_band_version?: number | null;
  title?: string;
  topic?: string;
  drawing_subject?: string;
  subject_learning_notes?: string;
  script_direction?: string | null;
  script_following_allowed?: boolean;
  activities?: Activity[];
};

export type ParentStoryRunV1 = {
  run_id: string;
  run_state: string;
  parent_profile_id: string;
  profile_revision_ref?: string;
  context_revision: number;
  context_confirmed?: boolean;
  context_snapshot: ParentStoryContextV1;
  context_snapshot_sha256: string;
  lesson_pin_snapshot?: ParentLessonPinSnapshotV1 | null;
  current_input_revision?: number | null;
  understanding_revision?: number | null;
  subject_label?: string | null;
  candidate?: ParentCandidate | null;
  story_revision_id?: string | null;
  story_revision_no?: number | null;
  story_status?: string | null;
  story_sha256?: string | null;
  story?: unknown;
  job_state?: string | null;
  retryable?: boolean;
  error_code?: string | null;
};

export type ParentStoryRunCreateV1 = {
  parent_profile_id: string;
  topic: string;
  adult_confirmed_idea: string;
  lesson_version?: ParentLessonVersionPinV1 | null;
};

export type ParentStoryRunEnvelopeV1 = {
  request_id?: string;
  story_run: ParentStoryRunV1;
};

export type ParentActiveStoryRunEnvelopeV1 = {
  request_id?: string;
  story_run: ParentStoryRunV1 | null;
};

export type ParentStoryContextConfirmationV1 = {
  expected_context_revision: number;
  context_snapshot_sha256: string;
  confirmed: true;
};

export type ParentStorySubjectConfirmationV1 = {
  request_id?: string;
  story_run_id: string;
  understanding_revision: number;
  decision: string;
};

export type ParentStoryScriptConfirmationV1 = ParentStoryRunEnvelopeV1;

export type ParentStoryRevisionResultV1 = {
  request_id?: string;
  modal_call_id?: string;
  story?: unknown;
  story_sha256?: string;
  story_run?: ParentStoryRunV1;
};
