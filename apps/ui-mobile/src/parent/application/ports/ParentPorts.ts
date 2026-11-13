import type {
  Activity,
  ParentAudioTranscription,
  ConsentPolicy,
  LessonDetail,
  LessonSummary,
  ParentCandidate,
  LessonInvitation,
  ParentGroupInvitation,
  ParentLessonDeliveryPage,
  ParentNotification,
  ParentNotificationPage,
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
  ParentActiveStoryRunEnvelopeV1,
  ParentTranscriptConfirmation,
  ParentStoryRunHistoryPage,
  ParentUser,
  ParentVideoQuota,
  ParentStoryContextConfirmationV1,
  ParentStoryRevisionResultV1,
  ParentStoryRunCreateV1,
  ParentStoryRunEnvelopeV1,
  ParentStoryRunV1,
  ParentStoryScriptConfirmationV1,
  ParentStorySubjectConfirmationV1,
  StoryRun,
  SuggestedActivity,
} from '../../domain/types';

export interface ParentIdentityPort {
  currentUser(): Promise<ParentUser | null>;
  signIn(email: string, password: string): Promise<ParentUser>;
  signUp(email: string, password: string): Promise<ParentUser>;
  signInWithGoogle(idToken: string): Promise<ParentUser>;
  resetPassword(email: string): Promise<void>;
  changePassword(currentPassword: string, newPassword: string): Promise<void>;
  signOut(): Promise<void>;
}

export interface AuthTokenPort {
  getIdToken(): Promise<string>;
}

export type ParentDrawingMediaType = 'image/jpeg' | 'image/png';

/** An identity is created once for an action and retained unchanged for retries. */
export type ParentActionIdentity = string;

export function createParentActionIdentity(): ParentActionIdentity {
  return `parent-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 14)}`;
}

export interface ParentApiPort {
  getConsentPolicy(): Promise<{ request_id: string; policy: ConsentPolicy }>;
  listProfiles(): Promise<{ request_id: string; profiles: ParentProfile[] }>;
  listProfilesV1(limit?: number, cursor?: string | null): Promise<ParentProfilePageV1>;
  getProfileV1(profileId: string): Promise<ParentProfileRecordV1>;
  createProfileV1(input: ParentProfileCreateV1, actionIdentity: ParentActionIdentity): Promise<ParentProfileReferenceV1>;
  patchProfileV1(profileId: string, input: ParentProfilePatchV1, actionIdentity: ParentActionIdentity): Promise<ParentProfileViewV1>;
  requestProfileDeletionV1(profileId: string, actionIdentity: ParentActionIdentity): Promise<ParentProfileDeletePendingV1>;
  createProfile(input: ProfileCreateInput): Promise<{ request_id: string; profile: ParentProfile }>;
  updateProfile(profileId: string, input: ProfileUpdateInput): Promise<{ request_id: string; profile: ParentProfile }>;
  grantAuthorization(profileId: string, policyVersion: string): Promise<{ request_id: string; profile: ParentProfile }>;
  revokeAuthorization(profileId: string): Promise<{ request_id: string; profile: ParentProfile }>;
  archiveProfile(profileId: string): Promise<{ request_id: string; profile: ParentProfile }>;
  getActiveStoryRun(): Promise<{ request_id: string; story_run: StoryRun | null }>;
  getStoryRun(runId: string): Promise<{ request_id: string; story_run: StoryRun }>;
  getActiveStoryRunV1(): Promise<ParentActiveStoryRunEnvelopeV1>;
  getStoryRunV1(runId: string): Promise<ParentStoryRunEnvelopeV1>;
  listStoryRuns(profileId?: string, cursor?: string | null): Promise<ParentStoryRunHistoryPage>;
  cancelStoryRun(runId: string): Promise<ParentRunLifecycleReceipt>;
  deleteStoryRun(runId: string): Promise<ParentRunLifecycleReceipt>;
  listLessons(): Promise<{ contract: string; items: LessonSummary[]; next_cursor: string | null }>;
  getLesson(lessonId: string): Promise<LessonDetail>;
  listLessonInvitations(): Promise<{ contract: string; items: LessonInvitation[]; next_cursor: string | null }>;
  acceptLessonInvitation(invitationId: string): Promise<unknown>;
  declineLessonInvitation(invitationId: string): Promise<unknown>;
  listParentGroupInvitations(): Promise<{ contract: string; items: ParentGroupInvitation[]; next_cursor: string | null }>;
  acceptParentGroupInvitation(membershipId: string): Promise<unknown>;
  generateSketchGuide(topic: string): Promise<SketchGuideResult>;
  createStoryRun(input: StoryRunCreateInput): Promise<{ request_id: string; story_run: StoryRun }>;
  createStoryRunV1(input: ParentStoryRunCreateV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  confirmStoryRunContextV1(runId: string, input: ParentStoryContextConfirmationV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  confirmStoryRunSubjectV1(runId: string, revision: number, subject: string, actionIdentity: ParentActionIdentity): Promise<ParentStorySubjectConfirmationV1>;
  confirmStoryRunScriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity): Promise<ParentStoryScriptConfirmationV1>;
  createStoryRevisionV1(runId: string, revision: number, rewriteInstruction: string | undefined, actionIdentity: ParentActionIdentity): Promise<ParentStoryRevisionResultV1>;
  analyzeDrawing(storyRunId: string, imageBase64: string, mediaType: ParentDrawingMediaType): Promise<DrawingUnderstandingResult>;
  confirmSubject(storyRunId: string, revision: number, subject: string): Promise<SubjectConfirmationResult>;
  suggestActivities(storyRunId: string, revision: number): Promise<ActivitySuggestionResult>;
  generateStory(storyRunId: string, revision: number, rewriteInstruction?: string): Promise<StoryGenerationResult>;
  confirmStory(storyRunId: string, revision: number, sha256: string): Promise<{ request_id: string; story_run: StoryRun }>;
  transcribeAudio(storyRunId: string, audio: AudioUploadInput): Promise<ParentAudioTranscription>;
  confirmTranscript(storyRunId: string, revision: number, transcriptText: string): Promise<ParentTranscriptConfirmation>;
  listProfileShares(profileId: string): Promise<ParentProfileSharePage>;
  createProfileShare(profileId: string, teacherSubject: string): Promise<{ request_id: string; grant: ParentProfileShareGrant }>;
  revokeProfileShare(profileId: string, grantId: string): Promise<{ request_id: string; grant: ParentProfileShareGrant }>;
  listLessonDeliveries(profileId: string, cursor?: string | null): Promise<ParentLessonDeliveryPage>;
  submitLessonFeedback(occurrenceId: string, profileId: string, feedbackText: string): Promise<{
    contract: 'LessonDeliveryFeedbackV1'; feedback_id: string; feedback_text: string; created_at: string; updated_at: string;
  }>;
  listNotifications(cursor?: string | null): Promise<ParentNotificationPage>;
  markNotificationRead(notificationId: string): Promise<ParentNotification>;
  getVideoQuota(): Promise<ParentVideoQuota>;
}

export type ProfileCreateInput = {
  age_months: number;
  display_name: string;
  interests_summary: string;
  consent_accepted: true;
  consent_policy_version: string;
};

export type AudioUploadInput = {
  uri: string;
  file_name: string;
  media_type: string;
};

export type ProfileUpdateInput = {
  expected_revision: number;
  age_months: number;
  display_name: string;
  interests_summary: string;
};

export type StoryRunCreateInput = {
  parent_profile_id: string;
  expected_profile_revision_id: string;
  consent_policy_version: string;
  topic: string;
  adult_confirmed_idea: string;
  context_confirmed: true;
  lesson_id?: string;
  lesson_version_id?: string;
};

export type SketchGuideResult = {
  request_id: string;
  modal_call_id?: string;
  status: string;
  review_required: true;
  model?: { id: string; revision: string };
  image_base64: string;
  asset?: Record<string, unknown>;
};

export type DrawingUnderstandingResult = {
  request_id: string;
  modal_call_id?: string;
  candidate?: ParentCandidate;
  run_input_revision?: number;
  understanding_revision?: number;
};

export type SubjectConfirmationResult = {
  request_id: string;
  story_run_id: string;
  understanding_revision: number;
  decision: string;
};

export type ActivitySuggestionResult = {
  request_id: string;
  modal_call_id?: string;
  contract: 'ParentActivitySuggestionResponseV2';
  selection_mode: 'CATALOG_SELECTION' | 'AI_GENERATED_FALLBACK';
  catalog_candidate_count: number;
  review_required: true;
  activities: SuggestedActivity[];
};

export type StoryGenerationResult = {
  request_id: string;
  modal_call_id?: string;
  story?: unknown;
  story_sha256?: string;
  story_run?: StoryRun;
};
