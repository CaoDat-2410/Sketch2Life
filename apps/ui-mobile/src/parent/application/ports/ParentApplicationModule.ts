import type { ParentAccountUseCases } from '../use-cases/ParentAccountUseCases';
import type { ParentLearningUseCases } from '../use-cases/ParentLearningUseCases';
import type { ParentLessonUseCases } from '../use-cases/ParentLessonUseCases';
import type { ParentProfileUseCases } from '../use-cases/ParentProfileUseCases';
import type { ParentPlatformUseCases } from '../use-cases/ParentPlatformUseCases';

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
    | 'create'
    | 'revise'
    | 'grantAuthorization'
    | 'revokeAuthorization'
    | 'archive'>;
  lessons: Pick<ParentLessonUseCases,
    | 'list'
    | 'get'
    | 'listInvitations'
    | 'acceptInvitation'
    | 'declineInvitation'
    | 'listGroupInvitations'
    | 'acceptGroupInvitation'>;
  learning: Pick<ParentLearningUseCases,
    | 'getActiveRun'
    | 'getRun'
    | 'generateSketchGuide'
    | 'createRunForDrawing'
    | 'understandDrawing'
    | 'confirmSubject'
    | 'suggestActivities'
    | 'generateStory'
    | 'confirmStory'
    | 'transcribeAudio'
    | 'confirmTranscript'>;
  platform: Pick<ParentPlatformUseCases,
    | 'listRuns'
    | 'cancelRun'
    | 'deleteRun'
    | 'listShares'
    | 'inviteTeacher'
    | 'revokeShare'
    | 'listDeliveries'
    | 'submitFeedback'
    | 'listNotifications'
    | 'markNotificationRead'
    | 'getVideoQuota'>;
}
