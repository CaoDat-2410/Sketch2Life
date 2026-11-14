import { isSupportedChildAge } from '../../domain/profileRules';
import type {
  LessonDetail,
  LessonSummary,
  ParentProfileShareGrant,
  ParentProfileViewV1,
} from '../../domain/types';
import type {
  ParentCapabilityUnavailableReason,
  ParentOperationState,
} from '../../application/ports/ParentCapabilityPorts';

export type SelectedPhoto = {
  uri: string;
  base64: string;
  mediaType: 'image/jpeg' | 'image/png';
  fileSizeBytes?: number;
  analysisError?: string;
};

export type SelectedAudio = {
  uri: string;
  fileName: string;
  mediaType: 'audio/mp4' | 'audio/wav' | 'audio/webm' | 'audio/ogg';
};

export type ParentActiveRunCheckState = 'checking' | 'confirmed' | 'unavailable';

export const PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE =
  'Chưa thể xác nhận trạng thái buổi học đang mở. Hãy kiểm tra lại trước khi bắt đầu.';

export type ParentStoryRunCreationGate =
  | 'active-run-check-required'
  | 'active-run-exists'
  | 'photo-required'
  | 'api-unavailable'
  | 'ready';

export function parentStoryRunCreationGate(input: {
  activeRunCheck: ParentActiveRunCheckState;
  activeRun: boolean;
  photoSelected: boolean;
  apiAvailable: boolean;
}): ParentStoryRunCreationGate {
  if (input.activeRunCheck !== 'confirmed') return 'active-run-check-required';
  if (input.activeRun) return 'active-run-exists';
  if (!input.photoSelected) return 'photo-required';
  if (!input.apiAvailable) return 'api-unavailable';
  return 'ready';
}

export function isCurrentAuthorizedLesson(
  summary: LessonSummary,
  detail: LessonDetail,
  nowEpochMs = Date.now(),
): boolean {
  if (detail.contract !== 'ParentLessonDetailV1'
    || detail.lesson_id !== summary.lesson_id
    || detail.version_id !== summary.version_id
    || detail.access_source !== summary.access_source
    || !['PUBLIC', 'SHARED'].includes(detail.access_source)
    || detail.target_age_band_ref !== summary.target_age_band_ref
    || detail.target_age_band_version !== summary.target_age_band_version
    || detail.activity_count !== summary.activity_count
    || !/^[A-Fa-f0-9]{64}$/.test(detail.content_sha256)) {
    return false;
  }

  if (!detail.access_expires_at) return true;
  const expiresAt = Date.parse(detail.access_expires_at);
  return Number.isFinite(expiresAt) && expiresAt > nowEpochMs;
}

export type TimedEvent = {
  stage: string;
  status: 'PASS' | 'FAIL';
  durationMs: number;
  requestId?: string;
  code?: string;
};

export type AppStep =
  | 'auth'
  | 'home'
  | 'profile'
  | 'profile-create'
  | 'profile-edit'
  | 'account'
  | 'settings'
  | 'notifications'
  | 'quota'
  | 'history'
  | 'profile-sharing'
  | 'lesson-history'
  | 'lesson-library'
  | 'topic'
  | 'drawing-guide'
  | 'lessons'
  | 'capture'
  | 'context'
  | 'understanding'
  | 'activity'
  | 'story'
  | 'handoff';

export type ChildGenderDraft = '' | 'boy' | 'girl' | 'prefer_not_to_say';

export type ParentProfileMutationInput = {
  displayName: string;
  ageMonths: number;
  interests: string;
};

export type ParentProfileDraftInput = ParentProfileMutationInput & {
  childGender: ChildGenderDraft;
};

export function toParentProfileMutationInput(draft: ParentProfileDraftInput): ParentProfileMutationInput {
  return {
    displayName: draft.displayName,
    ageMonths: draft.ageMonths,
    interests: draft.interests,
  };
}

export type ParentProfileAgeEligibility = 'supported' | 'legacy-read-only' | 'unavailable';

export function parentProfileAgeEligibility(
  profile: Pick<ParentProfileViewV1, 'age_months' | 'age_band_ref' | 'age_band_version'>,
): ParentProfileAgeEligibility {
  const hasAgeBandRef = Boolean(profile.age_band_ref?.trim());
  const hasAgeBandVersion = Boolean(profile.age_band_version?.trim());
  if (hasAgeBandRef !== hasAgeBandVersion) return 'unavailable';
  if (profile.age_months >= 121 && profile.age_months <= 155) return 'legacy-read-only';
  if (!isSupportedChildAge(profile.age_months)) return 'unavailable';
  return 'supported';
}

export type ParentConsentStatus =
  | { state: 'unknown' }
  | { state: 'pending' }
  | { state: 'confirmed'; source: 'server'; policyRevision: string }
  | { state: 'revoked' }
  | { state: 'unavailable'; reason: ParentCapabilityUnavailableReason };

export type ParentConsentUiState = {
  status: ParentConsentStatus;
  capture: ParentOperationState<void>;
  revoke: ParentOperationState<void>;
};

export function createUnavailableParentConsentState(reason: ParentCapabilityUnavailableReason): ParentConsentUiState {
  return {
    status: { state: 'unavailable', reason },
    capture: { state: 'unavailable', reason },
    revoke: { state: 'unavailable', reason },
  };
}

export function canStartProfileLearning(
  ageEligibility: ParentProfileAgeEligibility,
  consent: ParentConsentStatus,
): boolean {
  if (ageEligibility !== 'supported' || consent.state === 'revoked') return false;
  if (consent.state !== 'confirmed') return true;
  return consent.source === 'server' && Boolean(consent.policyRevision.trim());
}

export function parentShareGrantStateLabel(state: ParentProfileShareGrant['state']): string {
  const labels: Record<ParentProfileShareGrant['state'], string> = {
    INVITED: 'Đang chờ giáo viên chấp nhận',
    ACTIVE: 'Đang chia sẻ',
    DECLINED: 'Đã từ chối',
    REVOKED: 'Đã thu hồi',
    EXPIRED: 'Đã hết hạn',
  };
  return labels[state];
}

export function parentShareGrantExpiryState(
  state: ParentProfileShareGrant['state'],
  expiresAt: string | null,
  nowEpochMs: number,
): 'active' | 'expired' | 'not-active' {
  if (state !== 'ACTIVE') return 'not-active';
  if (!expiresAt) return 'not-active';
  const timestamp = Date.parse(expiresAt);
  if (!Number.isFinite(timestamp)) return 'not-active';
  return timestamp > nowEpochMs ? 'active' : 'expired';
}

export function isParentSessionExpired(error: unknown): boolean {
  if (typeof error !== 'object' || error === null) return false;
  const candidate = error as { code?: unknown; status?: unknown };
  return candidate.status === 401
    || (typeof candidate.code === 'string' && [
      'AUTH_REQUIRED', 'AUTH_API_HTTP_401', 'ID_TOKEN_EXPIRED', 'TOKEN_EXPIRED', 'UNAUTHENTICATED',
    ].includes(candidate.code));
}

export function safeParentIdentityErrorMessage(error: unknown): string {
  if (isParentSessionExpired(error)) return 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục.';
  const code = typeof error === 'object' && error !== null && 'code' in error
    ? (error as { code?: unknown }).code
    : undefined;
  if (typeof code === 'string') {
    if (code === 'CAPABILITY_UNAVAILABLE') return 'Tính năng này chưa có tuyến dịch vụ được xác nhận.';
    if (['INVALID_LOGIN_CREDENTIALS', 'INVALID_PASSWORD', 'EMAIL_NOT_FOUND', 'USER_NOT_FOUND'].includes(code)) {
      return 'Email hoặc mật khẩu chưa đúng. Hãy kiểm tra rồi thử lại.';
    }
    if (code === 'EMAIL_EXISTS') return 'Email này đã có tài khoản. Hãy đăng nhập hoặc dùng email khác.';
    if (code === 'WEAK_PASSWORD') return 'Mật khẩu chưa đủ mạnh. Hãy chọn mật khẩu khác.';
    if (code === 'INVALID_EMAIL') return 'Email chưa đúng định dạng.';
    if (['ACCOUNT_ROLE_MISMATCH', 'ACTION_NOT_ALLOWED', 'PARENT_PROFILE_NOT_AUTHORIZED'].includes(code)) {
      return 'Tài khoản chưa được cấp quyền sử dụng khu vực phụ huynh.';
    }
    if (['NETWORK_ERROR', 'AUTH_NETWORK_ERROR', 'AUTH_API_UNAVAILABLE', 'REQUEST_TIMEOUT'].includes(code)) {
      return 'Chưa kết nối được dịch vụ xác thực. Hãy kiểm tra kết nối rồi thử lại.';
    }
  }
  return 'Chưa thể hoàn tất thao tác tài khoản. Hãy thử lại hoặc đăng nhập lại.';
}
