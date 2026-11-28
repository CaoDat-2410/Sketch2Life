import type {
  ConsentPolicy,
  LessonDetail,
  LessonExportV1,
  LessonSummary,
  ParentCandidate,
  ParentSubjectRoleV1,
  ParentTopicSuggestionSetV1,
  ParentDrawingSubjectSuggestionSetV1,
  ParentCustomSubjectValidationV1,
  LessonInvitation,
  ParentGroupInvitation,
  ParentGroupMembershipPage,
  ParentGroupMembershipV1,
  ParentLessonListOptions,
  ParentLessonPage,
  ParentLessonDeliveryPage,
  ParentNotification,
  ParentNotificationPage,
  ParentNotificationReadAllV1,
  PushEndpointRegistrationResultV1,
  PushEndpointRegistrationV1,
  ParentProfile,
  ParentContextEntryListView,
  ParentContextEntryEnvelope,
  CreateParentContextEntryRequest,
  ParentProfileCreateV1,
  ParentProfileDeletePendingV1,
  ParentProfileReferenceV1,
  ParentProfilePageV1,
  ParentProfilePatchV1,
  ParentProfileRecordV1,
  ParentProfileViewV1,
  ParentSupportNeedsV1,
  ParentSupportNeedsWriteV1,
  SupportNeedsPutV1,
  ParentProfileShareGrant,
  ParentProfileSharePage,
  ParentConsentPolicyV1,
  ParentShareField,
  ParentShareGrantV1,
  ParentShareGrantCreatedV1,
  ParentShareGrantPageV1,
  ParentShareDeliveryPageV1,
  ParentLessonFeedbackV1,
  ParentLessonFeedbackStateV1,
  ParentLessonFeedbackReplyPageV1,
  ParentRunLifecycleReceipt,
  ParentActivityListV1,
  ParentActivitySelectionReceiptV1,
  ParentActivitySuggestionSetV1,
  ParentActivitySelectionRequestV1,
  ParentStoryRunLifecycleEnvelopeV1,
  ParentStoryRunResultV1,
  ParentActiveStoryRunEnvelopeV1,
  ParentStoryRunHistoryPage,
  ParentUser,
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
  ParentStoryScriptConfirmationV1,
  ParentStorySubjectConfirmationAcceptedV1,
  ParentPlaybackSourceV1,
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
import type { ParentPaymentProvider } from '../parentQuota';
import type { SvgGuideCatalogPageV1, SvgTopicStrokeGuideSourceDraftV1 } from '../../domain/svgGuide';

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
  getConsentPolicy(): Promise<ParentConsentPolicyV1>;
  listProfiles(): Promise<{ request_id: string; profiles: ParentProfile[] }>;
  listProfilesV1(limit?: number, cursor?: string | null): Promise<ParentProfilePageV1>;
  getProfileV1(profileId: string): Promise<ParentProfileRecordV1>;
  listContextEntriesV1(profileId: string, cursor?: string | null): Promise<ParentContextEntryListView>;
  createContextEntryV1(profileId: string, input: CreateParentContextEntryRequest, actionIdentity: ParentActionIdentity): Promise<ParentContextEntryEnvelope>;
  getSupportNeedsV1(profileId: string): Promise<ParentSupportNeedsV1>;
  putSupportNeedsV1(profileId: string, input: SupportNeedsPutV1, actionIdentity: ParentActionIdentity): Promise<ParentSupportNeedsWriteV1>;
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
  getStoryRunV1(runId: string): Promise<ParentStoryRunResultV1>;
  listActivitiesV1(runId: string): Promise<ParentActivityListV1>;
  suggestActivitiesV1(runId: string, expectedUnderstandingRevision: number, actionIdentity: ParentActionIdentity): Promise<ParentActivitySuggestionSetV1>;
  selectActivityV1(runId: string, input: ParentActivitySelectionRequestV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  requestActivitySuggestionsV1(storyRunId: string, revision: number, actionIdentity: ParentActionIdentity): Promise<ActivitySuggestionResult>;
  selectSuggestedActivityV1(input: {
    storyRunId: string;
    suggestionSetId: string;
    revision: number;
    activityIndex: number;
    actionIdentity: ParentActionIdentity;
  }): Promise<ActivitySelectionReceipt>;
  listStoryRuns(profileId?: string, cursor?: string | null): Promise<ParentStoryRunHistoryPage>;
  cancelStoryRun(runId: string): Promise<ParentRunLifecycleReceipt>;
  cancelStoryRunV1(runId: string, expectedRevision: number, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunLifecycleEnvelopeV1>;
  deleteStoryRunV1(runId: string, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunLifecycleEnvelopeV1>;
  deleteStoryRun(runId: string): Promise<ParentRunLifecycleReceipt>;
  listLessons(options?: ParentLessonListOptions): Promise<ParentLessonPage>;
  downloadLesson(lessonId: string): Promise<LessonExportV1>;
  getLesson(lessonId: string): Promise<LessonDetail>;
  listLessonInvitations(): Promise<{ contract: string; items: LessonInvitation[]; next_cursor: string | null }>;
  acceptLessonInvitation(invitationId: string, actionIdentity?: ParentActionIdentity): Promise<unknown>;
  declineLessonInvitation(invitationId: string, actionIdentity?: ParentActionIdentity): Promise<unknown>;
  listParentGroupInvitations(): Promise<{ contract: string; items: ParentGroupInvitation[]; next_cursor: string | null }>;
  acceptParentGroupInvitation(membershipId: string, actionIdentity?: ParentActionIdentity): Promise<unknown>;
  declineParentGroupInvitation(membershipId: string, actionIdentity: ParentActionIdentity): Promise<ParentGroupMembershipV1>;
  leaveParentGroup(
    organizationId: string,
    parentGroupId: string,
    membershipId: string,
    revision: number,
    actionIdentity: ParentActionIdentity,
  ): Promise<ParentGroupMembershipV1>;
  listParentGroupMemberships(cursor?: string | null): Promise<ParentGroupMembershipPage>;
  listTopicSuggestions(draftId: string, excludedSetIds: string[], requestId?: string): Promise<ParentTopicSuggestionSetV1>;
  listDrawingSubjectSuggestions(input: {
    draftId: string;
    topicId: string;
    topic: string;
    excludedSetIds: string[];
    excludedSubjects?: string[];
    requestId?: string;
  }): Promise<ParentDrawingSubjectSuggestionSetV1>;
  validateCustomSubject(input: { topicId: string; topic: string; subject: string }): Promise<ParentCustomSubjectValidationV1>;
  listSvgCatalogGuides(topicKey?: string, limit?: number): Promise<SvgGuideCatalogPageV1>;
  generateSketchGuide(topic: string, intendedSubject?: string): Promise<SvgTopicStrokeGuideSourceDraftV1>;
  generateSketchGuide(topic: string, intendedSubject: string | undefined, difficulty: 'beginner' | 'simple'): Promise<SvgTopicStrokeGuideDraftV1>;
  createStoryRun(input: StoryRunCreateInput): Promise<{ request_id: string; story_run: StoryRun }>;
  createStoryRunV1(input: ParentStoryRunCreateV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  confirmStoryRunContextV1(runId: string, input: ParentStoryContextConfirmationV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  confirmStoryRunSubjectV1(runId: string, revision: number, subject: string, actionIdentity: ParentActionIdentity, subjectRoles?: ParentSubjectRoleV1[]): Promise<ParentStorySubjectConfirmationAcceptedV1>;
  confirmStoryRunScriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity): Promise<ParentStoryScriptConfirmationV1>;
  createStoryRevisionV1(runId: string, revision: number, rewriteInstruction: string | undefined, actionIdentity: ParentActionIdentity): Promise<ParentStoryRevisionResultV1>;
  analyzeDrawing(storyRunId: string, imageBase64: string, mediaType: ParentDrawingMediaType): Promise<DrawingUnderstandingResult>;
  confirmSubject(storyRunId: string, revision: number, subject: string): Promise<SubjectConfirmationResult>;
  generateStory(storyRunId: string, revision: number, rewriteInstruction?: string): Promise<StoryGenerationResult>;
  confirmStory(storyRunId: string, revision: number, sha256: string): Promise<{ request_id: string; story_run: StoryRun }>;
  attachRunAssetV1(runId: string, assetRef: string, expectedRunRevision: number | null, actionIdentity: ParentActionIdentity): Promise<ParentRunAssetAcceptedV1>;
  resumeDrawingAnalysisV1(runId: string, inputRevision: number): Promise<ParentDrawingAnalysisResumeV1>;
  addRunIdeaV1(runId: string, input: ParentRunIdeaRequestV1, actionIdentity: ParentActionIdentity): Promise<ParentRunIdeaAcceptedV1>;
  getRunTranscriptV1(runId: string): Promise<ParentRunTranscriptV1>;
  confirmRunTranscriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity): Promise<ParentTranscriptConfirmedV1>;
  createStoryRewriteV1(runId: string, input: ParentStoryRewriteRequestV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRewriteAcceptedV1>;
  requestVideoGenerationV1(runId: string, input: ParentVideoRequestV1, actionIdentity: ParentActionIdentity): Promise<ParentVideoGenerationAcceptedV1>;
  markVideoUnsuitableV1(runId: string, input: ParentVideoUnsuitableRequestV1, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  completeRunV1(runId: string, expectedRevision: number, actionIdentity: ParentActionIdentity): Promise<ParentStoryRunEnvelopeV1>;
  openPlaybackV1(runId: string): Promise<ParentPlaybackSourceV1>;
  listProfileShares(profileId: string, limit?: number, cursor?: string | null): Promise<ParentShareGrantPageV1>;
  getProfileShare(grantId: string): Promise<ParentShareGrantV1>;
  createProfileShare(profileId: string, grantedFields: ParentShareField[], actionIdentity: ParentActionIdentity): Promise<ParentShareGrantCreatedV1>;
  revokeProfileShare(grantId: string, revision: number, actionIdentity: ParentActionIdentity): Promise<ParentShareGrantV1>;
  listProfileShareDeliveries(grantId: string, limit?: number, cursor?: string | null): Promise<ParentShareDeliveryPageV1>;
  listLessonDeliveries(profileId: string, cursor?: string | null): Promise<ParentLessonDeliveryPage>;
  submitLessonFeedback(lessonId: string, feedbackText: string, actionIdentity: ParentActionIdentity): Promise<ParentLessonFeedbackV1>;
  getParentLessonFeedback(lessonId: string): Promise<ParentLessonFeedbackStateV1>;
  listParentLessonFeedbackReplies(lessonId: string, limit?: number, cursor?: string | null): Promise<ParentLessonFeedbackReplyPageV1>;
  listNotifications(cursor?: string | null, limit?: number): Promise<ParentNotificationPage>;
  markNotificationRead(notificationId: string, actionIdentity: ParentActionIdentity): Promise<ParentNotification>;
  markAllNotificationsRead(actionIdentity: ParentActionIdentity): Promise<ParentNotificationReadAllV1>;
  registerPushEndpointV1(input: PushEndpointRegistrationV1, actionIdentity: ParentActionIdentity): Promise<PushEndpointRegistrationResultV1>;
  deletePushEndpointV1(endpointId: string, expectedVersion: number, actionIdentity: ParentActionIdentity): Promise<void>;
  getVideoQuota(): Promise<ParentVideoQuota>;
  getQuotaProducts(): Promise<ParentQuotaProduct[]>;
  getQuotaInvoices(limit?: number): Promise<ParentQuotaInvoicePage>;
  getQuotaPaymentSettings(): Promise<ParentQuotaPaymentSettings>;
  checkoutQuotaProduct(productId: string, provider: ParentPaymentProvider, actionIdentity: ParentActionIdentity): Promise<ParentQuotaCheckoutResult>;
  reconcileQuotaInvoice(invoiceId: string): Promise<ParentQuotaReconcileResult>;
  cancelQuotaInvoice(invoiceId: string): Promise<ParentQuotaCancelResult>;
}

export type ProfileCreateInput = {
  age_months: number;
  display_name: string;
  interests_summary: string;
  consent_accepted: true;
  consent_policy_version: string;
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

export type SketchGuideResult = SvgTopicStrokeGuideDraftV1;

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

export type ActivitySuggestionResult = ParentActivitySuggestionSetV1;

export type ActivitySelectionReceipt = ParentActivitySelectionReceiptV1;

export type StoryGenerationResult = {
  request_id: string;
  modal_call_id?: string;
  story?: unknown;
  story_sha256?: string;
  story_run?: StoryRun;
};
