import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type {
  ParentJobStageState,
  ParentCapabilityId,
  ParentOperationState,
} from '../src/parent/application/ports/ParentCapabilityPorts';
import { ParentApi, ParentApiUnavailableError } from '../src/parent/infrastructure/http/ParentApi';
import { ParentUnavailableCapabilityAdapter } from '../src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter';
import { ParentAuth } from '../src/parent/infrastructure/auth/ParentAuth';
import {
  canStartProfileLearning,
  createUnavailableParentConsentState,
  isParentSessionExpired,
  parentProfileAgeEligibility,
  parentShareGrantExpiryState,
  parentShareGrantStateLabel,
  safeParentIdentityErrorMessage,
  toParentProfileMutationInput,
} from '../src/parent/presentation/navigation/workflowTypes';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

const uiSource = readFileSync(new URL('../src/parent/presentation/components/ui.tsx', import.meta.url), 'utf8');
const bottomBarSource = readFileSync(new URL('../src/parent/presentation/screens/ParentBottomBar.tsx', import.meta.url), 'utf8');
const authScreenSource = readFileSync(new URL('../src/parent/presentation/screens/AuthScreen.tsx', import.meta.url), 'utf8');
const profileFormSource = readFileSync(new URL('../src/parent/presentation/screens/ProfileFormScreen.tsx', import.meta.url), 'utf8');
const profileControllerSource = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
const platformControllerSource = readFileSync(new URL('../src/parent/presentation/navigation/useParentPlatformController.ts', import.meta.url), 'utf8');
const parentExpoAppSource = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
const profileScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ProfileScreen.tsx', import.meta.url), 'utf8');
const profileSharingSource = readFileSync(new URL('../src/parent/presentation/screens/ProfileSharingScreen.tsx', import.meta.url), 'utf8');
const lessonGallerySource = readFileSync(new URL('../src/parent/presentation/screens/LessonGalleryScreen.tsx', import.meta.url), 'utf8');
const lessonPickerSource = readFileSync(new URL('../src/parent/presentation/screens/LessonPickerScreen.tsx', import.meta.url), 'utf8');
const topicScreenSource = readFileSync(new URL('../src/parent/presentation/screens/TopicScreen.tsx', import.meta.url), 'utf8');
const captureScreenSource = readFileSync(new URL('../src/parent/presentation/screens/CaptureScreen.tsx', import.meta.url), 'utf8');
const drawingGuideScreenSource = readFileSync(new URL('../src/parent/presentation/screens/DrawingGuideScreen.tsx', import.meta.url), 'utf8');
const understandingScreenSource = readFileSync(new URL('../src/parent/presentation/screens/UnderstandingScreen.tsx', import.meta.url), 'utf8');
const contextScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ContextScreen.tsx', import.meta.url), 'utf8');
const activityScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ActivityScreen.tsx', import.meta.url), 'utf8');
const storyScreenSource = readFileSync(new URL('../src/parent/presentation/screens/StoryScreen.tsx', import.meta.url), 'utf8');
const handoffScreenSource = readFileSync(new URL('../src/parent/presentation/screens/HandoffScreen.tsx', import.meta.url), 'utf8');
const storyHistoryScreenSource = readFileSync(new URL('../src/parent/presentation/screens/StoryHistoryScreen.tsx', import.meta.url), 'utf8');
const lessonHistoryScreenSource = readFileSync(new URL('../src/parent/presentation/screens/LessonHistoryScreen.tsx', import.meta.url), 'utf8');
const quotaScreenSource = readFileSync(new URL('../src/parent/presentation/screens/QuotaScreen.tsx', import.meta.url), 'utf8');
const notificationsScreenSource = readFileSync(new URL('../src/parent/presentation/screens/NotificationsScreen.tsx', import.meta.url), 'utf8');
const parentApiSource = readFileSync(new URL('../src/parent/infrastructure/http/ParentApi.ts', import.meta.url), 'utf8');
const learningUseCasesSource = readFileSync(new URL('../src/parent/application/use-cases/ParentLearningUseCases.ts', import.meta.url), 'utf8');
const paletteBody = uiSource.match(/export const palette = \{([\s\S]*?)\n\};/)?.[1] ?? '';
const pairBody = uiSource.match(/const contrastPairs = \[([\s\S]*?)\n\] as const;/)?.[1] ?? '';
const palette = Object.fromEntries(
  Array.from(paletteBody.matchAll(/^\s+(\w+): '(#[0-9A-Fa-f]{6})',?$/gm), (match) => [match[1], match[2]]),
);
const contrastPairs = Array.from(
  pairBody.matchAll(
    /\{ name: '([^']+)', foreground: palette\.(\w+), background: palette\.(\w+), minimumRatio: ([0-9.]+) \}/g,
  ),
  (match) => ({
    name: match[1],
    foreground: palette[match[2]],
    background: palette[match[3]],
    minimumRatio: Number(match[4]),
  }),
);

function luminance(hex: string): number {
  const [red, green, blue] = hex.slice(1).match(/.{2}/g)!.map((channel) => {
    const value = Number.parseInt(channel, 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

type HasPercentField = 'percent' extends keyof ParentJobStageState
  ? true
  : 'percentage' extends keyof ParentJobStageState
    ? true
    : false;
type AssertFalse<Value extends false> = Value;
const jobStageHasNoPercent: AssertFalse<HasPercentField> = false;

describe('R0 parent primitives accessibility contracts', () => {
  it('meets the declared contrast threshold for every foreground and fill pair', () => {
    expect(contrastPairs.length).toBeGreaterThan(0);

    for (const pair of contrastPairs) {
      expect(pair.foreground, pair.name + ': foreground token').toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(pair.background, pair.name + ': fill token').toMatch(/^#[0-9A-Fa-f]{6}$/);
      const light = Math.max(luminance(pair.foreground), luminance(pair.background));
      const dark = Math.min(luminance(pair.foreground), luminance(pair.background));
      expect((light + 0.05) / (dark + 0.05), pair.name).toBeGreaterThanOrEqual(pair.minimumRatio);
    }
  });

  it('communicates selected, busy, and notice states through semantics and distinct cues', () => {
    expect(uiSource).toContain('accessibilityState={{ disabled: disabled || busy, busy }}');
    expect(uiSource).toContain('accessibilityState={{ selected }}');
    expect(uiSource).toContain('{selected ? <Text style={styles.choiceCheck}>✓</Text> : null}');
    expect(uiSource).toContain('const iconName = tone ===');
    expect(uiSource).toContain('accessibilityRole={tone ===');
    expect(bottomBarSource).toContain('accessibilityState={{ selected: active }}');
    expect(jobStageHasNoPercent).toBe(false);

    const pending: ParentOperationState<string> = { state: 'pending' };
    expect(pending.state).not.toBe('confirmed');
  });

  it('keeps minimum and preferred targets and optional prop defaults in the source contract', () => {
    expect(uiSource).toMatch(/minimum:\s*44/);
    expect(uiSource).toMatch(/primary:\s*52/);
    expect(uiSource).toMatch(/navigation:\s*52/);
    expect(uiSource).toContain('backDisabled = false');
    expect(uiSource).toContain('subtitle?: string; step?: string; onBack?: () => void; backDisabled?: boolean');
    expect(uiSource).toContain('disabled = false');
    expect(uiSource).toContain('busy = false');
    expect(uiSource).toContain('destructive = false');
    expect(uiSource).toContain("tone = 'info'");
    expect(uiSource).toContain('style?: object');
    expect(uiSource).toContain('detail?: string; selected?: boolean; onPress: () => void');
  });

  it('sets the paper status bar for every app step without adding a second status inset', () => {
    expect(parentExpoAppSource).toContain('export default function ParentExpoApp({ application }: Props): React.JSX.Element {\n  return <>\n    <StatusBar barStyle="dark-content" backgroundColor={palette.background} />\n    <ParentExpoAppContent application={application} />\n  </>;\n}\n');
    expect(parentExpoAppSource.indexOf('<StatusBar barStyle="dark-content" backgroundColor={palette.background} />'))
      .toBeLessThan(parentExpoAppSource.indexOf('<ParentExpoAppContent application={application} />'));
    expect(uiSource).not.toContain('StatusBar.currentHeight');
  });

  it('returns explicit unavailable capability and operation states without fake success', () => {
    const adapter = new ParentUnavailableCapabilityAdapter();

    expect(adapter.capabilityState('lessons')).toEqual({
      capability: 'lessons',
      state: 'unavailable',
      reason: 'capability-not-configured',
    });
    expect(adapter.operationState<string>()).toEqual({
      state: 'unavailable',
      reason: 'capability-not-configured',
    });

    const absentRouteAdapter = new ParentUnavailableCapabilityAdapter('route-not-in-be-handoff');
    expect(absentRouteAdapter.capabilityState('profile-sharing')).toEqual({
      capability: 'profile-sharing',
      state: 'unavailable',
      reason: 'route-not-in-be-handoff',
    });
    expect(absentRouteAdapter.operationState<void>()).toEqual({
      state: 'unavailable',
      reason: 'route-not-in-be-handoff',
    });
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('R1 account and profile boundaries', () => {
  it('coalesces an expired-session token refresh and presents a safe re-authentication message', async () => {
    const jsonResponse = (body: unknown): Response => new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    let refreshCalls = 0;
    let releaseRefresh: ((response: Response) => void) | undefined;
    const refreshResult = new Promise<Response>((resolve) => {
      releaseRefresh = resolve;
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('accounts:signInWithPassword')) {
        return jsonResponse({
          localId: 'synthetic-parent',
          idToken: 'synthetic-id-token-1',
          refreshToken: 'synthetic-refresh-token-1',
          expiresIn: '3600',
          email: 'synthetic-parent-login',
        });
      }
      if (url.endsWith('/api/auth/v1/me')) return jsonResponse({ role: 'parent', state: 'active' });
      if (url.includes('securetoken.googleapis.com')) {
        refreshCalls += 1;
        return refreshResult;
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    const auth = new ParentAuth();
    await auth.signIn('synthetic-parent-login', 'synthetic-password');
    const privateSession = auth as unknown as { session: { expiresAt: number } };
    privateSession.session.expiresAt = Date.now() - 1;

    const firstToken = auth.getIdToken();
    const secondToken = auth.getIdToken();
    expect(refreshCalls).toBe(1);
    releaseRefresh?.(jsonResponse({
      user_id: 'synthetic-parent',
      id_token: 'synthetic-id-token-2',
      refresh_token: 'synthetic-refresh-token-2',
      expires_in: '3600',
    }));
    await expect(Promise.all([firstToken, secondToken])).resolves.toEqual([
      'synthetic-id-token-2', 'synthetic-id-token-2',
    ]);
    expect(refreshCalls).toBe(1);
    expect(isParentSessionExpired({ code: 'AUTH_REQUIRED', message: 'synthetic private detail' })).toBe(true);
    expect(safeParentIdentityErrorMessage({ code: 'AUTH_REQUIRED', message: 'synthetic private detail' }))
      .toBe('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục.');
  });

  it('keeps consent and age-band states explicit when server bands are absent', () => {
    const supported = { age_months: 72, age_band_ref: 'synthetic-age-6', age_band_version: 'synthetic-age-6-v1' };
    const legacy = { ...supported, age_months: 121 };
    expect(parentProfileAgeEligibility(supported)).toBe('supported');
    expect(parentProfileAgeEligibility(legacy)).toBe('legacy-read-only');
    const missingBand = { age_months: 72, age_band_ref: null, age_band_version: null };
    expect(parentProfileAgeEligibility(missingBand)).toBe('supported');
    expect(canStartProfileLearning(
      parentProfileAgeEligibility(missingBand),
      createUnavailableParentConsentState('route-not-in-be-handoff').status,
    )).toBe(true);
    expect(parentProfileAgeEligibility({
      age_months: 72, age_band_ref: 'synthetic-age-6', age_band_version: null,
    })).toBe('unavailable');
    expect(parentProfileAgeEligibility({
      age_months: 72, age_band_ref: null, age_band_version: 'synthetic-age-6-v1',
    })).toBe('unavailable');
    expect(profileScreenSource).toContain('const versionLabel = hasAgeBandRef && hasAgeBandVersion');
    expect(profileScreenSource).toContain('const hasIncompleteAgeBand = hasAgeBandRef !== hasAgeBandVersion');
    expect(profileScreenSource).toContain("'Nhóm tuổi chưa khả dụng'");
    expect(canStartProfileLearning('supported', { state: 'confirmed', source: 'server', policyRevision: 'synthetic-policy-v1' })).toBe(true);
    expect(canStartProfileLearning('supported', createUnavailableParentConsentState('route-not-in-be-handoff').status)).toBe(true);
    expect(canStartProfileLearning('supported', { state: 'revoked' })).toBe(false);

    const mutation = toParentProfileMutationInput({
      displayName: 'Synthetic child', ageMonths: 72, interests: 'synthetic interest', childGender: 'prefer_not_to_say',
    });
    expect(mutation).toEqual({ displayName: 'Synthetic child', ageMonths: 72, interests: 'synthetic interest' });
    expect(mutation).not.toHaveProperty('childGender');
    expect(mutation).not.toHaveProperty('child_gender');

    for (const state of ['INVITED', 'ACTIVE', 'DECLINED', 'REVOKED', 'EXPIRED'] as const) {
      expect(parentShareGrantStateLabel(state).length).toBeGreaterThan(0);
    }
    const now = Date.parse('2026-11-13T00:00:00.000Z');
    expect(parentShareGrantExpiryState('ACTIVE', '2027-02-11T00:00:00.000Z', now)).toBe('active');
    expect(parentShareGrantExpiryState('ACTIVE', '2026-11-12T23:59:59.000Z', now)).toBe('expired');
    expect(parentShareGrantExpiryState('REVOKED', '2027-02-11T00:00:00.000Z', now)).toBe('not-active');

    expect(authScreenSource).toContain("const [email, setEmail] = useState('')");
    expect(authScreenSource).toContain("const [password, setPassword] = useState('')");
    expect(profileFormSource).toContain("useState<ChildGenderDraft>('')");
    expect(profileFormSource).toContain('void action(input).catch(() => undefined)');
    expect(profileFormSource).toContain('Cơ sở đồng ý cho trường này đang chờ xác nhận');
    expect(profileSharingSource).toContain('phạm vi 90 ngày');
    expect(profileSharingSource).toContain('Chưa thể xác nhận lời mời đang chờ');
    expect(profileControllerSource).not.toMatch(/application\.profiles\.(getConsentPolicy|grantAuthorization|revokeAuthorization)/);
    expect(profileControllerSource).not.toMatch(/child_gender|childGender/);
    expect(platformControllerSource).not.toContain('application.platform.');
    expect(authScreenSource).not.toContain('cause.message');
    expect(profileControllerSource).not.toContain('cause.message');
    expect(platformControllerSource).not.toContain('cause.message');
  });
});

describe('R2 backend route boundary', () => {
  it('returns typed unavailable errors locally for every absent Parent API route', async () => {
    const auth = { getIdToken: vi.fn(async () => 'synthetic-token') };
    const fetcher = vi.fn(async () => new Response('{}', { status: 200 })) as unknown as typeof fetch;
    const api = new ParentApi(auth, fetcher, 'https://api.synthetic.test');
    const absentOperations: Array<{ capability: ParentCapabilityId; request: () => Promise<unknown> }> = [
      { capability: 'consent', request: () => api.getConsentPolicy() },
      { capability: 'profiles', request: () => api.listProfiles() },
      { capability: 'profiles', request: () => api.createProfile({ age_months: 72, display_name: 'Synthetic', interests_summary: '', consent_accepted: true, consent_policy_version: 'synthetic-v1' }) },
      { capability: 'profiles', request: () => api.updateProfile('synthetic-profile', { expected_revision: 1, age_months: 72, display_name: 'Synthetic', interests_summary: '' }) },
      { capability: 'consent', request: () => api.grantAuthorization('synthetic-profile', 'synthetic-v1') },
      { capability: 'consent', request: () => api.revokeAuthorization('synthetic-profile') },
      { capability: 'profiles', request: () => api.archiveProfile('synthetic-profile') },
      { capability: 'story-creation', request: () => api.getActiveStoryRun() },
      { capability: 'story-creation', request: () => api.getStoryRun('synthetic-run') },
      { capability: 'run-history', request: () => api.listStoryRuns('synthetic-profile') },
      { capability: 'run-history', request: () => api.cancelStoryRun('synthetic-run') },
      { capability: 'run-history', request: () => api.deleteStoryRun('synthetic-run') },
      { capability: 'story-creation', request: () => api.createStoryRun({ parent_profile_id: 'synthetic-profile', expected_profile_revision_id: 'synthetic-revision', consent_policy_version: 'synthetic-v1', topic: 'synthetic topic', adult_confirmed_idea: 'synthetic idea', context_confirmed: true }) },
      { capability: 'story-creation', request: () => api.confirmSubject('synthetic-run', 1, 'synthetic subject') },
      { capability: 'story-creation', request: () => api.suggestActivities('synthetic-run', 1) },
      { capability: 'story-creation', request: () => api.confirmStory('synthetic-run', 1, 'a'.repeat(64)) },
      { capability: 'story-creation', request: () => api.transcribeAudio('synthetic-run', { uri: 'synthetic://audio', file_name: 'synthetic.m4a', media_type: 'audio/mp4' }) },
      { capability: 'story-creation', request: () => api.confirmTranscript('synthetic-run', 1, 'synthetic transcript') },
      { capability: 'profile-sharing', request: () => api.listProfileShares('synthetic-profile') },
      { capability: 'profile-sharing', request: () => api.createProfileShare('synthetic-profile', 'synthetic-teacher') },
      { capability: 'profile-sharing', request: () => api.revokeProfileShare('synthetic-profile', 'synthetic-grant') },
      { capability: 'lesson-history', request: () => api.listLessonDeliveries('synthetic-profile') },
      { capability: 'lesson-history', request: () => api.submitLessonFeedback('synthetic-occurrence', 'synthetic-profile', 'synthetic feedback') },
      { capability: 'notifications', request: () => api.listNotifications() },
      { capability: 'notifications', request: () => api.markNotificationRead('synthetic-notification') },
      { capability: 'quota', request: () => api.getVideoQuota() },
    ];

    for (const operation of absentOperations) {
      const failure = await operation.request().catch((error: unknown) => error);
      expect(failure).toBeInstanceOf(ParentApiUnavailableError);
      expect(failure).toMatchObject({
        state: 'unavailable', reason: 'route-not-in-be-handoff', capability: operation.capability,
        code: 'CAPABILITY_UNAVAILABLE',
      });
    }
    expect(fetcher).not.toHaveBeenCalled();
    expect(auth.getIdToken).not.toHaveBeenCalled();
    expect(parentApiSource).not.toMatch(/\/api\/parent\/v1\/(?:child-profiles|story-runs)(?:\/|['?])/);
    expect(parentApiSource).not.toMatch(/\/api\/(?:notifications|billing)\/v1\//);
    expect(parentApiSource).not.toContain('/api/lesson-library/v1/me/deliveries');
    expect(parentApiSource).not.toContain('audio-transcriptions');
    expect(parentApiSource).not.toContain('transcript-confirmations');
  });

  it('keeps topic optional while requiring a pinned lesson and shows version, hash, and invitation states from the server', () => {
    expect(lessonPickerSource).toContain('Bạn chưa thể tiếp tục nếu chưa ghim một phiên bản bài giảng');
    expect(lessonPickerSource).not.toContain('Tiếp tục không dùng bài giảng');
    expect(topicScreenSource).toContain('Chủ đề và ý tưởng có thể bổ sung, nhưng cần ghim một phiên bản bài giảng');
    expect(topicScreenSource).not.toContain('Không chọn bài giảng cũng được');
    expect(lessonGallerySource).not.toContain('Có thể tiếp tục không cần bài giảng');
    expect(lessonGallerySource).not.toContain('Tiếp tục không dùng bài giảng');
    expect(topicScreenSource).toContain('SHA-256 ${props.lesson.content_sha256}');
    expect(topicScreenSource).not.toContain('cause.message');
    expect(lessonGallerySource).toContain('SHA-256: {props.selectedLesson.content_sha256}');
    expect(lessonGallerySource).toContain('Trạng thái từ máy chủ: {lessonInvitationStateLabel(item.state)}');
    expect(lessonGallerySource).toContain('Trạng thái từ máy chủ: {parentGroupInvitationStateLabel(item.state)}');
    expect(lessonGallerySource).toContain("catalog.emptyState === 'no-lessons' && !props.loading && !props.error");
    expect(lessonGallerySource).not.toContain('Nhóm phụ huynh · {item.membership_id}');
    expect(profileControllerSource).toContain('application.learning.getActiveRunV1()');
    expect(profileControllerSource).not.toContain('createRunBeforeDrawingV1');
    expect(profileControllerSource).not.toContain('application.learning.suggestActivities');
    expect(parentExpoAppSource).toContain('photoSelected: Boolean(parent.photo)');
  });
});

describe('R3 story workflow safety boundaries', () => {
  it('keeps camera and gallery alternatives, pre-upload limits, and one artwork per run', () => {
    expect(captureScreenSource).toContain('requestCameraPermissionsAsync');
    expect(captureScreenSource).toContain('requestMediaLibraryPermissionsAsync');
    expect(captureScreenSource).toContain('launchImageLibraryAsync');
    expect(captureScreenSource).toContain('if (!permission.granted)');
    expect(captureScreenSource).toContain('isWithinOfflinePhotoLimit(sourceBytes)');
    expect(captureScreenSource).toContain('disabled={photoLocked}');
    expect(captureScreenSource).toContain('disabled={busy || photoLocked}');
    expect(profileControllerSource).toContain('function setAudio(value: SelectedAudio | null)');
    expect(profileControllerSource).toContain('setAudioValue(null)');
    expect(profileControllerSource).not.toMatch(/application\.learning\.(transcribeAudio|confirmTranscript)\(/);
    expect(topicScreenSource).toContain('Audio.requestPermissionsAsync()');
    expect(topicScreenSource).toContain('onChangeText={props.onIdea}');
    expect(topicScreenSource).toContain('durationMillis >= 120_000');
    expect(profileControllerSource).toContain('if (latest.current_input_revision !== 1)');
    expect(profileControllerSource).toContain('createRunAfterPhotoV1');
    expect(profileControllerSource).not.toContain('createRunBeforeDrawingV1(');
    expect(profileControllerSource).not.toContain('application.learning.generateSketchGuide(');
    expect(profileControllerSource).toContain('Gợi ý nét vẽ tự động 4–8 bước chưa khả dụng.');
    expect(parentApiSource).toContain('image_base64: string');
    expect(parentApiSource).not.toMatch(/generateSketchGuide\([\s\S]*?ordered_steps/);
    expect(profileControllerSource).toContain('drawingAnalysisAttemptedRunId.current === runId');
    expect(profileControllerSource).toContain('Không gửi lại ảnh; hãy kiểm tra trạng thái buổi học sau.');
    expect(captureScreenSource).toContain("stepLabel === '4 / 7' ? '3 / 7'");
    expect(understandingScreenSource).toContain("props.stepLabel === '5 / 7' ? '4 / 7'");
    expect(contextScreenSource).toContain("'5 / 7' : props.stepLabel");
  });

  it('keeps guide output ordered and bounded, and subject review free of mismatch heuristics', () => {
    expect(drawingGuideScreenSource).toContain('parseDrawingGuideSteps(props.lesson.drawing_steps_text)');
    expect(drawingGuideScreenSource).toContain('guide.kind === \'steps\'');
    expect(understandingScreenSource).toContain('subject');
    expect(understandingScreenSource).not.toMatch(/toLowerCase\(\)[\s\S]{0,120}includes\(/);
    expect(profileControllerSource).toContain('confirmSubjectV1(runId, understandingRevision, confirmedSubject, actionIdentity)');
    expect(profileControllerSource).toContain('readRunPinnedLessonActivities(confirmedRun.lesson_pin_snapshot)');
    expect(profileControllerSource).not.toMatch(/application\.learning\.suggestActivities\(/);
    expect(activityScreenSource).toContain('PINNED_LESSON');
    expect(activityScreenSource).toContain('Hoạt động chính: chưa khả dụng.');
    expect(storyScreenSource).toContain('Kịch bản vẫn có thể tiếp tục mà không gắn hoạt động.');
  });

  it('requires GET reconciliation, exact story revision/hash pins, and no activity or media fields in story requests', () => {
    const analysisStart = profileControllerSource.indexOf('async function analyzeDrawingForRun');
    const analysisEnd = profileControllerSource.indexOf('async function analyzeDrawingForCurrentRun', analysisStart);
    const analysisSource = profileControllerSource.slice(analysisStart, analysisEnd);
    expect(analysisSource.indexOf('getLatestRun(runId)')).toBeGreaterThanOrEqual(0);
    expect(analysisSource.indexOf('getLatestRun(runId)')).toBeLessThan(analysisSource.indexOf('understandDrawing(runId'));
    const storyMethod = parentApiSource.slice(
      parentApiSource.indexOf('  createStoryRevisionV1('),
      parentApiSource.indexOf('  listStoryRuns(', parentApiSource.indexOf('  createStoryRevisionV1(')),
    );
    expect(storyMethod).toContain('expected_understanding_revision');
    expect(storyMethod).toContain('rewrite_instruction');
    for (const forbidden of ['activity', 'image_base64', 'audio', 'profile', 'child_gender', 'gender']) {
      expect(storyMethod.toLowerCase()).not.toContain(forbidden);
    }
    expect(profileControllerSource).toContain('isActiveOrUnreconciledStoryRun(latest)');
    expect(profileControllerSource).toContain('latest.story_sha256 !== revisionSha256');
    expect(profileControllerSource).toContain("confirmedRun.story_status !== 'CONFIRMED'");
    expect(storyScreenSource).toContain('story.sha256');
    expect(learningUseCasesSource).toContain('expected_context_revision: run.context_revision');
    expect(learningUseCasesSource).toContain('context_snapshot_sha256: run.context_snapshot_sha256');
    expect(parentApiSource).toContain('expected_understanding_revision: revision');
    expect(profileControllerSource).toContain("setStep('context')");
    expect(profileControllerSource).toContain("setStep('activity')");
    expect(contextScreenSource).toContain('disabled={props.busy || !subjectConfirmed}');
    const contextConfirmationStart = profileControllerSource.indexOf('async function confirmContext');
    const contextConfirmationEnd = profileControllerSource.indexOf('async function analyzeDrawingForRun', contextConfirmationStart);
    const contextConfirmationSource = profileControllerSource.slice(contextConfirmationStart, contextConfirmationEnd);
    expect(contextConfirmationSource).toContain('setSubjectConfirmed(isConfirmedRunSubject(confirmedRun, subject))');
    expect(contextConfirmationSource).toContain('readRunPinnedLessonActivities(confirmedRun.lesson_pin_snapshot)');
    expect(contextConfirmationSource).toContain("contextConfirmationAction.current = null");
    expect(contextConfirmationSource).toContain('getLatestRun(run.run_id)');
    expect(contextConfirmationSource).not.toMatch(/catch[\s\S]*?confirmRunContextV1\(/);
    expect(contextConfirmationSource).toContain("cause.code === 'STALE_REVISION'");
    const storyRequestStart = profileControllerSource.indexOf('async function requestStory');
    const storyRequestEnd = profileControllerSource.indexOf('async function confirmStory', storyRequestStart);
    const storyRequestSource = profileControllerSource.slice(storyRequestStart, storyRequestEnd);
    expect(storyRequestSource).toContain('latest.context_revision !== expectedContextRevision');
    expect(storyRequestSource).toContain('latest.context_snapshot_sha256 !== expectedContextHash');
    expect(storyRequestSource).toContain('storyRevisionAction.current = null');
    expect(storyRequestSource).toContain('latest.context_confirmed !== true');
    expect(storyRequestSource).not.toContain('activityAttempted');
    expect(storyRequestSource).not.toContain('activities');
    expect(analysisSource).not.toContain('PARENT_CONTEXT_NOT_CONFIRMED');
  });
});

describe('R4 absent delivery and lifecycle contracts', () => {
  it('keeps video and job operations typed unavailable without dispatching an adapter call', () => {
    expect(platformControllerSource).toContain("jobStatus: createUnavailableCapabilityState('job-status', unavailableReason)");
    expect(platformControllerSource).toContain("video: createUnavailableCapabilityState('video', unavailableReason)");
    expect(platformControllerSource).toContain("{ state: 'unavailable', stage: 'unavailable' }");
    expect(platformControllerSource).toContain('requestVideo');
    expect(platformControllerSource).toContain('markVideoUnsuitable');
    expect(platformControllerSource).toContain('regenerateVideo');
    expect(platformControllerSource).toContain('completeRun');
    expect(platformControllerSource).not.toContain('application.platform.');
    expect(platformControllerSource).toContain('videoOperationState: unavailableShareOperation');
    expect(jobStageHasNoPercent).toBe(false);
    expect(storyScreenSource).toContain('videoCapability.state === \'unavailable\'');
    expect(storyScreenSource).toContain('jobStageMessage(props.jobStage)');
    expect(storyScreenSource).not.toMatch(/<(?:Video|VideoPlayer|VideoView)\b/);
  });

  it('uses only resume for the active run and never claims video or run completion', () => {
    expect(handoffScreenSource).toContain('onResumeActiveRun');
    expect(handoffScreenSource).not.toContain('onRestart');
    expect(handoffScreenSource).not.toContain('resetWorkflow');
    expect(handoffScreenSource).toContain('Không có video để phát hoặc tải xuống');
    expect(handoffScreenSource).toContain('Trạng thái hoàn tất chưa được máy chủ xác nhận');
    expect(parentExpoAppSource).toContain('onResumeActiveRun={parent.resumeActiveRun}');
  });

  it('does not present empty-success states or lifecycle actions when history routes are absent', () => {
    expect(parentExpoAppSource).toContain('<StoryHistoryScreen');
    expect(parentExpoAppSource).toContain('<LessonHistoryScreen');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.runs}');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.deliveries}');
    expect(storyHistoryScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(storyHistoryScreenSource.indexOf('const canCancel'));
    expect(storyHistoryScreenSource).toContain('Không có thay đổi trạng thái nào được gửi');
    expect(lessonHistoryScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(lessonHistoryScreenSource.indexOf('Chưa có bài học để xem'));
    expect(lessonHistoryScreenSource).toContain('Không có dữ liệu rỗng hoặc thao tác gửi nào được suy ra');
  });

  it('shows only confirmed quota and inbox summaries and provides no purchase action', () => {
    expect(parentExpoAppSource).toContain('<QuotaScreen');
    expect(parentExpoAppSource).toContain('<NotificationsScreen');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.quota}');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.notifications}');
    expect(quotaScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(quotaScreenSource.indexOf('Còn {quota.available} lượt'));
    expect(quotaScreenSource).toContain('Chưa có tóm tắt hạn mức được máy chủ xác nhận');
    expect(quotaScreenSource).not.toContain('onPurchase');
    expect(notificationsScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(notificationsScreenSource.indexOf('Bạn chưa có thông báo'));
    expect(notificationsScreenSource).toContain('lời nhắc và đóng buổi do máy chủ quản lý');
  });
});
