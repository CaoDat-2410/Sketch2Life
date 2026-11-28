import type { ParentAccountUseCases } from '../use-cases/ParentAccountUseCases';
import type { ParentLearningUseCases } from '../use-cases/ParentLearningUseCases';
import type { ParentLessonUseCases } from '../use-cases/ParentLessonUseCases';
import type { ParentProfileUseCases } from '../use-cases/ParentProfileUseCases';
import type { ParentPlatformUseCases } from '../use-cases/ParentPlatformUseCases';
import type { ParentActiveStoryRunEnvelopeV1 } from '../../domain/types';

/** Public application boundary passed from the Expo composition root. */
export interface ParentApplicationModule {
  publicSettings: {
    googleAndroidClientId: string;
    googleWebClientId: string;
  };
  account: Pick<ParentAccountUseCases,
    | 'currentUser'
    | 'signIn'
    | 'signUp'
    | 'signInWithGoogle'
    | 'resetPassword'
    | 'changePassword'
    | 'signOut'>;
  profiles: Pick<ParentProfileUseCases,
    | 'getConsentPolicy'
    | 'listProfiles'
    | 'listPageV1'
    | 'getV1'
    | 'listContextEntriesV1'
    | 'createContextEntryV1'
    | 'getSupportNeedsV1'
    | 'putSupportNeedsV1'
    | 'createV1'
    | 'patchV1'
    | 'requestDeletionV1'
    | 'create'
    | 'revise'
    | 'grantAuthorization'
    | 'revokeAuthorization'
    | 'archive'>;
  lessons: Pick<ParentLessonUseCases,
    | 'list'
    | 'download'
    | 'get'
    | 'listInvitations'
    | 'acceptInvitation'
    | 'declineInvitation'
    | 'listGroupInvitations'
    | 'acceptGroupInvitation'
    | 'declineGroupInvitation'
    | 'leaveGroup'
    | 'listGroupMemberships'>;
  learning: Pick<ParentLearningUseCases,
    | 'getRunV1'
    | 'listTopicSuggestions'
    | 'listDrawingSubjectSuggestions'
    | 'validateCustomSubject'
    | 'listSvgCatalogGuides'
    | 'generateSketchGuide'
    | 'createRunAfterPhotoV1'
    | 'confirmRunContextV1'
    | 'confirmSubjectV1'
    | 'listActivitiesV1'
    | 'suggestActivitiesV1'
    | 'selectActivityV1'
    | 'requestActivitySuggestionsV1'
    | 'selectSuggestedActivityV1'
    | 'confirmScriptV1'
    | 'createStoryRevisionV1'
    | 'understandDrawing'
    | 'attachDrawingV1'
    | 'resumeDrawingAnalysisV1'
    | 'submitVoiceIdeaV1'
    | 'submitTextIdeaV1'
    | 'getTranscriptV1'
    | 'correctTranscriptV1'
    | 'confirmTranscriptV1'
    | 'rewriteStoryV1'
    | 'requestVideoV1'
    | 'markVideoUnsuitableV1'
    | 'completeRunV1'
    | 'openPlaybackV1'> & {
      getActiveRunV1(): Promise<ParentActiveStoryRunEnvelopeV1>;
    };
  platform: Pick<ParentPlatformUseCases,
    | 'listRuns'
    | 'cancelRun'
    | 'deleteRun'
    | 'cancelRunV1'
    | 'deleteRunV1'
    | 'listShares'
    | 'inviteTeacher'
    | 'revokeShare'
    | 'getShareGrant'
    | 'listShareDeliveries'
    | 'listDeliveries'
    | 'submitFeedback'
    | 'getLessonFeedback'
    | 'listLessonFeedbackReplies'
    | 'listNotifications'
    | 'markNotificationRead'
    | 'markAllNotificationsRead'
    | 'registerPushEndpointV1'
    | 'deletePushEndpointV1'
    | 'getVideoQuota'
    | 'getQuotaProducts'
    | 'getQuotaInvoices'
    | 'getQuotaPaymentSettings'
    | 'checkoutQuotaProduct'
    | 'reconcileQuotaInvoice'
    | 'cancelQuotaInvoice'>;
}
