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
const accountScreenSource = readFileSync(new URL('../src/parent/presentation/screens/AccountScreen.tsx', import.meta.url), 'utf8');
const settingsScreenSource = readFileSync(new URL('../src/parent/presentation/screens/SettingsScreen.tsx', import.meta.url), 'utf8');
const homeScreenSource = readFileSync(new URL('../src/parent/presentation/screens/HomeScreen.tsx', import.meta.url), 'utf8');
const profileFormSource = readFileSync(new URL('../src/parent/presentation/screens/ProfileFormScreen.tsx', import.meta.url), 'utf8');
const googleSignInButtonSource = readFileSync(new URL('../src/parent/presentation/components/GoogleSignInButton.tsx', import.meta.url), 'utf8');
const profileControllerSource = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
const platformControllerSource = readFileSync(new URL('../src/parent/presentation/navigation/useParentPlatformController.ts', import.meta.url), 'utf8');
const parentExpoAppSource = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
const profileScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ProfileScreen.tsx', import.meta.url), 'utf8');
const profileSharingSource = readFileSync(new URL('../src/parent/presentation/screens/ProfileSharingScreen.tsx', import.meta.url), 'utf8');
const lessonGallerySource = readFileSync(new URL('../src/parent/presentation/screens/LessonGalleryScreen.tsx', import.meta.url), 'utf8');
const lessonPickerSource = readFileSync(new URL('../src/parent/presentation/screens/LessonPickerScreen.tsx', import.meta.url), 'utf8');
const topicScreenSource = readFileSync(new URL('../src/parent/presentation/screens/TopicScreen.tsx', import.meta.url), 'utf8');
const ideaScreenSource = readFileSync(new URL('../src/parent/presentation/screens/IdeaScreen.tsx', import.meta.url), 'utf8');
const captureScreenSource = readFileSync(new URL('../src/parent/presentation/screens/CaptureScreen.tsx', import.meta.url), 'utf8');
const drawingGuideScreenSource = readFileSync(new URL('../src/parent/presentation/screens/DrawingGuideScreen.tsx', import.meta.url), 'utf8');
const understandingScreenSource = readFileSync(new URL('../src/parent/presentation/screens/UnderstandingScreen.tsx', import.meta.url), 'utf8');
const contextScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ContextScreen.tsx', import.meta.url), 'utf8');
const transcriptReviewSource = readFileSync(new URL('../src/parent/presentation/screens/TranscriptReviewScreen.tsx', import.meta.url), 'utf8');
const previewHarnessSource = readFileSync(new URL('../src/parent/presentation/ParentVisualPreviewHarness.tsx', import.meta.url), 'utf8');
const activityScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ActivityScreen.tsx', import.meta.url), 'utf8');
const videoScreenSource = readFileSync(new URL('../src/parent/presentation/screens/VideoScreen.tsx', import.meta.url), 'utf8');
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

  it('uses a native per-corner card edge and a shape cue for the selected aligned tab', () => {
    expect(uiSource).toContain('const outlineWidths = {\n  control: 1.5,\n  card: 1.6,\n  primary: 2,\n  focus: 3,\n} as const;');
    expect(uiSource).toContain('cardEdge: { borderWidth: outlineWidths.card, borderColor: palette.outline, borderTopLeftRadius: 22, borderTopRightRadius: 25, borderBottomRightRadius: 19, borderBottomLeftRadius: 23 }');
    expect(uiSource).toContain('return <View style={[styles.card, style, styles.cardEdge, variant === \'creative\' && styles.creativeCard]}>{children}</View>;');
    expect(uiSource).not.toContain('cardOutlinePath');
    expect(uiSource).not.toContain('preserveAspectRatio="none"');
    expect(bottomBarSource).toContain('const totalBarHeight = 56 + bottom;');
    expect(bottomBarSource).toContain('height: 56');
    expect(bottomBarSource).toContain('size={27}');
    expect(bottomBarSource).toContain('fontSize: 10.5');
    expect(bottomBarSource).toContain('paddingTop: 3');
    expect(bottomBarSource).toContain('paddingBottom: 3');
    expect(bottomBarSource).toContain('activeItem: { backgroundColor:');
    expect(bottomBarSource).toContain('minHeight: 48');
    expect(bottomBarSource).not.toContain('transform:');
  });

  it('keeps minimum and preferred targets and optional prop defaults in the source contract', () => {
    expect(uiSource).toMatch(/minimum:\s*44/);
    expect(uiSource).toMatch(/primary:\s*52/);
    expect(uiSource).toMatch(/navigation:\s*52/);
    expect(uiSource).toContain('backDisabled = false');
    expect(uiSource).toContain('subtitle?: string;');
    expect(uiSource).toContain('safeAreaEdges?: Edge[];');
    expect(uiSource).toContain('disabled = false');
    expect(uiSource).toContain('busy = false');
    expect(uiSource).toContain('destructive = false');
    expect(uiSource).toContain("tone = 'info'");
    expect(uiSource).toContain('style?: object');
    expect(uiSource).toContain('detail?: string; selected?: boolean; onPress: () => void');
  });

  it('sets the paper status bar for every app step without adding a second status inset', () => {
    expect(parentExpoAppSource).toContain('const visualPreviewEnabled = __DEV__ && process.env.EXPO_PUBLIC_FEAT081_VISUAL_PREVIEW === \'true\';');
    expect(parentExpoAppSource).toContain('return <>\n    <StatusBar barStyle="dark-content" backgroundColor={palette.background} />\n    {visualPreviewEnabled ? <ParentVisualPreviewHarness /> : <ParentExpoAppContent application={application} />}\n  </>;');
    expect(parentExpoAppSource.indexOf('<StatusBar barStyle="dark-content" backgroundColor={palette.background} />'))
      .toBeLessThan(parentExpoAppSource.indexOf('{visualPreviewEnabled ? <ParentVisualPreviewHarness />'));
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

describe('L1 Vietnamese copy and paper presentation contracts', () => {
  it('uses the concept auth, account, and settings copy without exposing provider wording', () => {
    expect(authScreenSource).toContain('Đăng nhập phụ huynh');
    expect(authScreenSource).toContain('mode === \'signup\' ? \'Tạo tài khoản phụ huynh\' : \'Đăng nhập phụ huynh\'');
    expect(authScreenSource).toContain('Tiếp tục quản lý hành trình của bé.');
    expect(authScreenSource).toContain('Nếu email hợp lệ, hướng dẫn sẽ được gửi đến bạn.');
    expect(authScreenSource).toContain('onClearAuthError');
    expect(authScreenSource).toContain('validateForm');
    expect(authScreenSource).not.toContain('Tài khoản dùng để đăng nhập vào Sketch2Life.');
    expect(authScreenSource).not.toContain('Tài khoản được tạo trên Firebase Authentication và backend Sketch2Life.');
    expect(authScreenSource).not.toContain('<AuthIllustration');
    expect(accountScreenSource).toContain('Mật khẩu đã được cập nhật.');
    expect(accountScreenSource).not.toContain('Mật khẩu đã được cập nhật trên Firebase Authentication.');
    expect(googleSignInButtonSource).toContain('Đăng nhập bằng Google hiện chưa khả dụng. Bạn có thể dùng email để tiếp tục.');
    expect(googleSignInButtonSource).toContain('Chưa thể hoàn tất đăng nhập bằng Google. Hãy thử lại hoặc dùng email.');
    expect(googleSignInButtonSource).not.toContain('response.params.error_description');
    expect(googleSignInButtonSource).not.toContain('Google Sign-In chưa cấu hình.');
    expect(googleSignInButtonSource).toContain('minHeight: 52');
    expect(googleSignInButtonSource).toContain('name="logo-google" size={18}');
    expect(settingsScreenSource).toContain('Chỉ áp dụng cho buổi hiện tại, chưa lưu vào tài khoản.');
    expect(settingsScreenSource).toContain('Bật gợi ý nét vẽ trong phiên hiện tại');
    expect(settingsScreenSource).not.toContain('line-sketch');
    expect(settingsScreenSource).toContain('title="Cài đặt" subtitle="Tùy chỉnh trải nghiệm trên thiết bị."');
  });

  it('keeps each L1 surface on its named paper-card composition', () => {
    expect(uiSource).toContain("require('../../../../assets/applied/sketch2life-logo.png')");
    expect(uiSource).not.toContain('brandDotText');
    expect(authScreenSource).toContain('styles.fixedContent');
    expect(authScreenSource).toContain('styles.backgroundImage');
    expect(authScreenSource).toContain('styles.formCard');
    expect(accountScreenSource).toContain('style={styles.emailRow}');
    expect(settingsScreenSource).toContain('style={styles.preferenceRow}');
    expect(homeScreenSource).toContain('styles.profileSelector');
    expect(homeScreenSource).toContain('styles.heroActions, compact && styles.heroActionsCompact');
    expect(profileScreenSource).toContain('style={styles.profileListCard}');
    expect(profileFormSource).toContain('style={styles.fieldsCard}');
    expect(profileFormSource).toContain('style={styles.genderGrid}');
    expect(profileFormSource).toContain('style={styles.formBadge}>HỒ SƠ');
    expect(profileFormSource).not.toContain('genderCard');
    expect(profileFormSource).not.toContain('actionsCard');
    expect(profileSharingSource).toContain('style={styles.inviteCard}');
    expect(googleSignInButtonSource).toContain('style={styles.unavailableGroup}');
  });

  it('keeps auth recovery in the existing screen and passes each action to its original handler', () => {
    expect(authScreenSource).toContain("type AuthMode = 'signin' | 'signup' | 'recovery';");
    expect(authScreenSource).toContain('onSignIn(email, password)');
    expect(authScreenSource).toContain('onSignUp(email, password)');
    expect(authScreenSource).toContain('void onReset(email)');
    expect(authScreenSource).toContain('setMode(nextMode)');
    expect(authScreenSource).toContain('Quay lại đăng nhập');
    expect(authScreenSource).toContain('accessibilityLabel="Quay lại đăng nhập"');
    expect(authScreenSource).not.toContain('onRecovery');
  });

  it('starts profile fields blank, keeps gender local, and shows sharing as unavailable without sample grants', () => {
    expect(profileFormSource).toContain("useState(profile ? String(profile.age_months) : '')");
    expect(profileFormSource).toContain('placeholder="Nhập tên hiển thị"');
    expect(profileFormSource).toContain('Giới tính chỉ là bản nháp trên thiết bị, không dùng tạo câu chuyện.');
    expect(profileFormSource).toContain('Giới tính của trẻ (tùy chọn)');
    expect(profileFormSource).toContain('Không muốn chia sẻ');
    expect(profileFormSource).toContain('CHILD_AGE_RANGE_MESSAGE');
    expect(profileFormSource).toContain('disabled={submitDisabled}');
    expect(profileFormSource).not.toContain('consent_accepted');
    expect(profileFormSource).not.toContain('consent_policy_version');
    expect(profileFormSource).toContain('ageMonths.trim().length > 0 && !ageValid');
    expect(profileFormSource).not.toContain('Ví dụ: Bé Mây');
    expect(profileFormSource).not.toContain('Thiên nhiên, côn trùng…');
    expect(profileSharingSource).toContain("const sharingUnavailable = props.capability.state === 'unavailable';");
    expect(profileSharingSource).toContain('Chỉ chia sẻ với giáo viên bạn chọn.');
    expect(profileSharingSource).toContain('Chia sẻ hiện chưa khả dụng. Chưa có thay đổi nào được xác nhận.');
    expect(profileSharingSource).not.toContain('phạm vi 90 ngày');
  });

  it('keeps home and profile actions on the existing run, selection, and eligibility conditions', () => {
    expect(homeScreenSource).toContain('Từ nét vẽ đến câu chuyện');
    expect(homeScreenSource).toContain("require('../../../../assets/home/home-story-hero.png')");
    expect(homeScreenSource).toContain('Chụp tranh ngay');
    expect(homeScreenSource).toContain('Chọn ảnh từ thư viện');
    expect(homeScreenSource).toContain('const compact = width < 420;');
    expect(homeScreenSource).toContain('visibleRun = activeRun && !terminalRunStates.has(activeRun.run_state)');
    expect(homeScreenSource).toContain('function runProgressState(run: ParentStoryRunV1)');
    expect(homeScreenSource).not.toContain('home-creative-duo.png');
    expect(homeScreenSource).not.toContain('percent:');
    expect(homeScreenSource).toContain('accessibilityLabel={`${title}. ${subtitle}`}');
    expect(homeScreenSource).toContain('onPress={onOpenLessons}');
    expect(homeScreenSource).toContain('onPress={onStart}');
    expect(homeScreenSource).toContain('onPress={onPickFromLibrary}');
    expect(homeScreenSource).toContain('setProfilePickerVisible(true)');
    expect(homeScreenSource).toContain('Quản lý hồ sơ');
    expect(homeScreenSource).not.toContain('Tạo hồ sơ để lưu độ tuổi và sở thích cho từng buổi.');
    expect(homeScreenSource).not.toContain('hồ sơ đã sẵn sàng.');
    expect(homeScreenSource).not.toContain('Không gian của gia đình');
    expect(homeScreenSource).not.toContain('Tài khoản và bảo mật');
    expect(bottomBarSource).toContain("{ id: 'activity', label: 'Câu chuyện', icon: 'book-outline' }");
    expect(bottomBarSource).toContain('accessibilityRole="tab"');
    expect(bottomBarSource).toContain('Sáng tạo');
    expect(parentExpoAppSource).toContain("if (tab === 'activity') return openHistory('home');");
    expect(parentExpoAppSource).toContain('onStart={startOrResume}');
    expect(parentExpoAppSource).toContain("mainSection('activity', <StoryHistoryScreen");
    expect(bottomBarSource).toContain("{ id: 'profiles', label: 'Cá nhân'");
    expect(profileScreenSource).toContain('Không gian gia đình');
    expect(profileScreenSource).toContain('Tài khoản và bảo mật');
    expect(profileScreenSource).toContain('Cài đặt');
    expect(profileScreenSource).toContain('Thông báo');
    expect(profileScreenSource).toContain('Lượt tạo video');
    expect(profileScreenSource).toContain('Lịch sử hoạt động');
    expect(profileScreenSource).toContain('Bài giáo viên đã dạy');
    expect(profileScreenSource).toContain('Chia sẻ hồ sơ với giáo viên');
    expect(profileScreenSource).toContain('Chọn hồ sơ trẻ để xem bài đã dạy hoặc quản lý chia sẻ.');
    expect(profileScreenSource).toContain('disabled={!selected}');
    expect(profileScreenSource).toContain('Đăng xuất');
    expect(profileScreenSource).not.toContain('Tiếp tục buổi đang mở');
    expect(profileScreenSource).toContain('Mỗi buổi học gắn với một hồ sơ trẻ.');
    expect(profileScreenSource.indexOf('Mỗi buổi học gắn với một hồ sơ trẻ.'))
      .toBeGreaterThan(profileScreenSource.indexOf('<Card style={styles.profileListCard}>'));
    expect(profileScreenSource).toContain('disabled={!mayStartRun}');
    expect(profileScreenSource).toContain('Hồ sơ cũ, chỉ xem hoặc xóa');
    expect(profileScreenSource).toContain('nên chưa thể bắt đầu buổi học');
    expect(profileScreenSource).not.toContain('vẫn có thể tiếp tục');
    expect(profileScreenSource).toContain('Hồ sơ dữ liệu mô phỏng nên không cần đồng ý xử lý dữ liệu.');
    expect(profileScreenSource).toContain('canStartProfileLearning(selectedAgeEligibility, consentState.status, selected!.data_origin)');
    expect(profileControllerSource).toContain('canStartProfileLearning(ageEligibility, consentState.status, target.data_origin)');
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
    )).toBe(false);
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
    expect(canStartProfileLearning('supported', createUnavailableParentConsentState('route-not-in-be-handoff').status)).toBe(false);
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
    expect(profileFormSource).toContain('void onCreate(input).catch(() => undefined)');
    expect(profileFormSource).toContain('Giới tính chỉ là bản nháp trên thiết bị, không dùng tạo câu chuyện.');
    expect(profileSharingSource).not.toContain('phạm vi 90 ngày');
    expect(profileSharingSource).toContain('Chưa xác nhận được lời mời. Kiểm tra trạng thái trước khi gửi lại.');
    expect(profileControllerSource).not.toContain('getConsentPolicy');
    expect(profileControllerSource).not.toMatch(/application\.profiles\.(grantAuthorization|revokeAuthorization)/);
    expect(profileControllerSource).not.toMatch(/child_gender|childGender/);
    // FEAT-081 C3b plus goal v3 Phase C T-8a: only confirmed run-history and inbox routes are live.
    expect(new Set(Array.from(platformControllerSource.matchAll(/application\.platform\.(\w+)/g), (match) => match[1])))
      .toEqual(new Set(['listRuns', 'cancelRunV1', 'deleteRunV1', 'listNotifications', 'markNotificationRead', 'markAllNotificationsRead']));
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
      { capability: 'profiles', request: () => api.listProfiles() },
      { capability: 'profiles', request: () => api.createProfile({ age_months: 72, display_name: 'Synthetic', interests_summary: '', consent_accepted: true, consent_policy_version: 'synthetic-v1' }) },
      { capability: 'profiles', request: () => api.updateProfile('synthetic-profile', { expected_revision: 1, age_months: 72, display_name: 'Synthetic', interests_summary: '' }) },
      { capability: 'consent', request: () => api.grantAuthorization('synthetic-profile', 'synthetic-v1') },
      { capability: 'consent', request: () => api.revokeAuthorization('synthetic-profile') },
      { capability: 'profiles', request: () => api.archiveProfile('synthetic-profile') },
      { capability: 'story-creation', request: () => api.getActiveStoryRun() },
      { capability: 'story-creation', request: () => api.getStoryRun('synthetic-run') },
      { capability: 'run-history', request: () => api.cancelStoryRun('synthetic-run') },
      { capability: 'run-history', request: () => api.deleteStoryRun('synthetic-run') },
      { capability: 'story-creation', request: () => api.createStoryRun({ parent_profile_id: 'synthetic-profile', expected_profile_revision_id: 'synthetic-revision', consent_policy_version: 'synthetic-v1', topic: 'synthetic topic', adult_confirmed_idea: 'synthetic idea', context_confirmed: true }) },
      { capability: 'story-creation', request: () => api.confirmSubject('synthetic-run', 1, 'synthetic subject') },
      { capability: 'story-creation', request: () => api.confirmStory('synthetic-run', 1, 'a'.repeat(64)) },
      { capability: 'profile-sharing', request: () => api.listProfileShares('synthetic-profile') },
      { capability: 'profile-sharing', request: () => api.createProfileShare('synthetic-profile', 'synthetic-teacher') },
      { capability: 'profile-sharing', request: () => api.revokeProfileShare('synthetic-profile', 'synthetic-grant') },
      { capability: 'lesson-history', request: () => api.listLessonDeliveries('synthetic-profile') },
      { capability: 'lesson-history', request: () => api.submitLessonFeedback('synthetic-occurrence', 'synthetic-profile', 'synthetic feedback') },
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
    expect(parentApiSource).toContain('/v1/story-runs/active/current');
    expect(parentApiSource).toContain('/v1/parent/profiles');
    for (const removed of ['/api/parent/v1/child-profiles', '/api/parent/v1/consent-policy', '/api/parent/v1/story-runs', 'data-authorizations', 'story-revision-confirmations', 'subject-confirmations']) {
      expect(parentApiSource).not.toContain(removed);
    }
    expect(parentApiSource).toContain('/api/parent/v1/ai/story-runs/');
    expect(parentApiSource).not.toMatch(/\/api\/(?:notifications|billing)\/v1\//);
    expect(parentApiSource).not.toContain('/api/lesson-library/v1/me/deliveries');
    expect(parentApiSource).not.toContain('audio-transcriptions');
    expect(parentApiSource).not.toContain('transcript-confirmations');
  });

  it('keeps topic and lesson pin optional while showing server version and invitation states', () => {
    expect(lessonPickerSource).toContain('title="Chọn bài học"');
    expect(ideaScreenSource).toContain('Bài học tham khảo');
    expect(ideaScreenSource).toContain('Có thể ghim một bài học từ thư viện.');
    expect(profileControllerSource).toContain('Định dạng bản ghi âm chưa được hỗ trợ.');
    expect(topicScreenSource).toContain('onPress={() => props.onTopic(option.title)}');
    expect(ideaScreenSource).toContain('Tiếp tục đến bức tranh');
    expect(lessonGallerySource).not.toContain('Có thể tiếp tục không cần bài giảng');
    expect(lessonGallerySource).not.toContain('Tiếp tục không dùng bài giảng');
    expect(ideaScreenSource).not.toContain('cause.message');
    expect(lessonGallerySource).toContain('`Phiên bản ${props.selectedLesson.version_no}`');
    expect(lessonGallerySource).toContain('lessonInvitationStateLabel(item.state)');
    expect(lessonGallerySource).toContain('parentGroupInvitationStateLabel(item.state)');
    expect(lessonGallerySource).toContain("catalog.emptyState === 'no-lessons' && !props.loading && !props.error");
    expect(lessonGallerySource).not.toContain('Nhóm phụ huynh · {item.membership_id}');
    expect(profileControllerSource).toContain('application.learning.getActiveRunV1()');
    expect(profileControllerSource).not.toContain('createRunBeforeDrawingV1');
    expect(profileControllerSource).toContain('application.learning.listActivitiesV1');
    expect(parentExpoAppSource).toContain('photoSelected: Boolean(parent.photo)');
  });

  it('keeps L2 screens on paper cards and gates the synthetic preview outside normal app flow', () => {
    expect(ideaScreenSource).toContain('Gợi ý nét vẽ do trí tuệ nhân tạo tạo');
    expect(ideaScreenSource).not.toContain('Gợi ý nét vẽ do AI tạo');
    expect(ideaScreenSource).not.toContain('Gợi ý line sketch được tạo bởi AI');
    expect(lessonGallerySource).toContain('catalogCard: {');
    expect(lessonGallerySource).toContain('activityItem: {');
    expect(lessonPickerSource).toContain('lessonCard: {');
    expect(ideaScreenSource).toContain('guideImage: { backgroundColor: palette.white');
    expect(drawingGuideScreenSource).toContain('title="Gợi ý vẽ (tùy chọn)"');
    expect(drawingGuideScreenSource).toContain('<PrimaryButton label="Bỏ qua hướng dẫn" onPress={props.onContinue} />');
    expect(drawingGuideScreenSource).toContain('currentStep: { color: palette.ink');
    expect(captureScreenSource).toContain('aspectRatio: 1.42, minHeight: 176');
    expect(captureScreenSource).toContain('<Text style={styles.requiredBadge}>BẮT BUỘC</Text>');
    expect(transcriptReviewSource).toContain('emptyCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(understandingScreenSource).toContain('candidateCard: { gap: 13 }');
    expect(understandingScreenSource).toContain('label="Xác nhận chủ thể"');
    expect(contextScreenSource).toContain('snapshotCard: { backgroundColor: palette.white, gap: 14, minWidth: 0 }');
    expect(contextScreenSource).toContain('Sở thích được phép dùng: {snapshot.interests_summary}');
    expect(contextScreenSource).not.toContain('consent');
    expect(contextScreenSource).toContain('snapshotText: { color: palette.ink, fontSize: 14, lineHeight: 21, minWidth: 0, flexShrink: 1 }');
    expect(contextScreenSource).toContain('</Card>\n\n      {props.contextRun && !subjectConfirmed ? <Notice');
    expect(contextScreenSource).not.toContain('position: \'absolute\'');
    expect(lessonGallerySource).toContain('<Card style={styles.catalogCard}>');
    expect(lessonGallerySource).toContain('{catalog.visibleLessons.map((lesson) => (');
    expect(lessonGallerySource).not.toContain('position: \'absolute\'');

    expect(parentExpoAppSource).toContain('const visualPreviewEnabled = __DEV__ && process.env.EXPO_PUBLIC_FEAT081_VISUAL_PREVIEW === \'true\';');
    expect(parentExpoAppSource).toContain('{visualPreviewEnabled ? <ParentVisualPreviewHarness /> : <ParentExpoAppContent application={application} />}');
    expect(previewHarnessSource).toContain('BẢN XEM TRƯỚC · DỮ LIỆU MÔ PHỎNG');
    expect(previewHarnessSource).toContain('numberOfLines={1} allowFontScaling={false} style={styles.marker}');
    expect(previewHarnessSource).toContain('style={styles.tabStrip}');
    expect(previewHarnessSource).toContain('tabStrip: { height: 56, maxHeight: 56, flexGrow: 0, flexShrink: 0 }');
    expect(previewHarnessSource).toContain('tab: { minHeight: 44');
    expect(previewHarnessSource).toContain("{ id: 'profiles', label: 'Gia đình' }");
    expect(previewHarnessSource).toContain("{ id: 'family-unselected', label: 'Gia đình · chưa chọn' }");
    expect(previewHarnessSource).toContain("{ id: 'home-new', label: 'Trang chủ · buổi mới' }");
    expect(previewHarnessSource).toContain('profiles={[]}\n      selectedProfile={null}\n      activeRun={previewContextRun}');
    expect(previewHarnessSource).toContain('selectedProfileId=""');
    expect(previewHarnessSource).toContain('screenContent: { flex: 1, minHeight: 0');
    expect(previewHarnessSource).toContain("candidate_subject: 'Mô phỏng · một con bướm'");
    expect(previewHarnessSource).toContain('age_band_ref: null');
    expect(previewHarnessSource).toContain('age_band_version: null');
    expect(previewHarnessSource).toContain('function ignoreAction(): void {}');
    expect(previewHarnessSource).toContain('function pendingPreviewAsync(): Promise<void>');
    expect(previewHarnessSource).toContain('return new Promise<void>((resolve) => { void resolve; });');
    expect(previewHarnessSource).toContain('function pendingPreviewProfile(): Promise<ParentProfileViewV1>');
    expect(previewHarnessSource).toContain('return new Promise<ParentProfileViewV1>((resolve) => { void resolve; });');
    expect(previewHarnessSource).not.toContain('async () => previewProfile');
    expect(previewHarnessSource).not.toContain('function ignoreAsync()');
    expect(previewHarnessSource).toContain('lesson={null}');
    expect(previewHarnessSource).toContain('canContinue={false}');
    expect(previewHarnessSource).toContain('guideBase64=""');
    expect(previewHarnessSource).toContain('transcript={previewTranscript}');
    expect(previewHarnessSource).toContain('const previewTranscript: ParentRunTranscriptV1 | null = null;');
    expect(transcriptReviewSource).toContain('{props.transcript && !props.waiting ? <Card style={styles.transcriptCard}>');
    expect(previewHarnessSource).toContain('<LessonGalleryScreen');
    expect(previewHarnessSource).toContain('<LessonPickerScreen');
    expect(previewHarnessSource).toContain('<AuthScreen');
    expect(previewHarnessSource).toContain('<AccountScreen');
    expect(previewHarnessSource).toContain('<SettingsScreen');
    expect(previewHarnessSource).toContain('<HomeScreen');
    expect(previewHarnessSource).toContain('<ProfileScreen');
    expect(previewHarnessSource).toContain('<ProfileFormScreen mode="create"');
    expect(previewHarnessSource).toContain('<ProfileFormScreen mode="edit"');
    expect(previewHarnessSource).toContain('<ProfileSharingScreen');
    expect(previewHarnessSource).toContain('<TopicScreen');
    expect(previewHarnessSource).toContain('<DrawingGuideScreen');
    expect(previewHarnessSource).toContain('capture: <CapturePreviewScreen state="empty" />');
    expect(previewHarnessSource).toContain('<TranscriptReviewScreen');
    expect(previewHarnessSource).toContain('<UnderstandingScreen');
    expect(previewHarnessSource).toContain('<ContextScreen');
    expect(previewHarnessSource).toContain('<ActivityScreen');
    expect(previewHarnessSource).toContain('<StoryScreen');
    expect(previewHarnessSource).toContain('<HandoffScreen');
    expect(previewHarnessSource).toContain('<StoryHistoryScreen');
    expect(previewHarnessSource).toContain('<LessonHistoryScreen');
    expect(previewHarnessSource).toContain('<QuotaScreen');
    expect(previewHarnessSource).toContain('<NotificationsScreen');
    expect(previewHarnessSource).toContain('<ParentBottomBar');
    expect(previewHarnessSource).toContain('<ParentBottomBar activeTab="home" onNavigate={ignoreAction} onStart={ignoreAction} startLabel="Bắt đầu" />');
    expect(previewHarnessSource).not.toContain('ParentApi');
    expect(previewHarnessSource).not.toContain('fetch(');
    expect(previewHarnessSource).not.toContain('EXPO_PUBLIC_API_URL');
    expect(previewHarnessSource).not.toContain('useParentController');
    expect(previewHarnessSource).not.toContain('useParentPlatformController');
  });
});

describe('M3 concept surfaces and truthful capability states', () => {
  it('keeps the existing flow, typed unavailable states, and concept presentation', () => {
    expect(activityScreenSource).toContain('title="Hoạt động cùng bé"');
    expect(activityScreenSource).toContain('Chọn một hoạt động chính');
    expect(activityScreenSource).toContain('lesson_title');
    expect(activityScreenSource).toContain('noCandidate');
    expect(parentExpoAppSource).toContain('activities={parent.activitySuggestions}');
    expect(parentExpoAppSource).toContain('storyBlockedReason');
    expect(parentExpoAppSource).toContain('onContinue={() => void parent.selectActivity()}');
    expect(storyScreenSource).toContain('title="Câu chuyện của bé"');
    expect(storyScreenSource).toContain('disabled={!props.storyReady || !props.rewriteInstruction.trim() || props.busy}');
    expect(storyScreenSource).toContain('disabled={!props.storyReady || !props.canConfirm');
    expect(storyScreenSource).toContain('editable={props.storyReady && !props.busy}');
    expect(storyScreenSource).toContain('disabled={!props.storyReady || !props.rewriteInstruction.trim() || props.busy}');
    expect(storyScreenSource).toContain('!props.storyReady || !props.canConfirm');
    expect(storyScreenSource).toContain('storyLanguageLabel(props.story.language)');
    expect(storyScreenSource).toContain('Viết lại câu chuyện');
    expect(storyScreenSource).toContain('props.rewritesLeft > 0');
    expect(storyScreenSource).toContain('generationCard: { gap: 13 }');
    expect(storyScreenSource).toContain('style={styles.scene}');
    expect(storyScreenSource).toContain('storyReady');
    expect(handoffScreenSource).toContain('title="Trạng thái buổi học"');
    expect(handoffScreenSource).toContain('style={styles.statusCard}');
    expect(handoffScreenSource).toContain('eventRow: { flexDirection: \'row\', alignItems: \'flex-start\', justifyContent: \'space-between\'');
    expect(handoffScreenSource).toContain('eventStageLabel(event.stage)');
    expect(handoffScreenSource).toContain('Tiến độ được máy chủ ghi nhận.');
    expect(handoffScreenSource).not.toContain('event.durationMs');
    expect(storyHistoryScreenSource).toContain('runCard: {');
    expect(storyHistoryScreenSource).toContain("return labels[value] ?? 'Trạng thái chưa xác định'");
    expect(lessonHistoryScreenSource).toContain('title="Bài giáo viên đã dạy"');
    expect(lessonHistoryScreenSource).toContain('deliveryCard: {');
    expect(quotaScreenSource).toContain('Số lượt sử dụng');
    expect(quotaScreenSource).toContain('summaryCard: {');
    expect(notificationsScreenSource).toContain('Thông tin dành riêng cho tài khoản phụ huynh.');
    expect(notificationsScreenSource).toContain('Đánh dấu đã đọc');
    expect(notificationsScreenSource).toContain('styles.notificationCard, unread ? styles.unreadCard : styles.readCard');
    expect(transcriptReviewSource).toContain('<SectionTitle>Nội dung nhận dạng</SectionTitle>');
    expect(transcriptReviewSource).not.toContain('Whisper · tiếng Việt');
    expect(transcriptReviewSource).toContain('ScreenFrame title="Rà soát bản chép lời"');
    expect(transcriptReviewSource).toContain('transcriptCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(previewHarnessSource).toContain('capture: <CapturePreviewScreen state="empty" />');
    expect(previewHarnessSource).toContain("'capture-denied': <CapturePreviewScreen state=\"camera-denied\" />");
    expect(previewHarnessSource).toContain("'capture-selected': <CapturePreviewScreen state=\"photo-selected\" />");
    expect(previewHarnessSource).toContain('Camera chưa được cấp quyền. Vẫn có thể chọn tranh từ thư viện.');
    expect(previewHarnessSource).toContain('Ảnh minh họa mô phỏng · không phải tranh thật');
    expect(previewHarnessSource).not.toContain('CaptureScreen');
    expect(previewHarnessSource).not.toContain('ImagePicker');
    expect(previewHarnessSource).not.toContain('requestCameraPermissionsAsync');
    expect(previewHarnessSource).not.toContain('requestMediaLibraryPermissionsAsync');
    expect(previewHarnessSource).not.toContain('ParentApi');
    expect(previewHarnessSource).not.toContain('useParentController');
    expect(previewHarnessSource).not.toContain('fetch(');
    const capturePreviewStart = previewHarnessSource.indexOf('function CapturePreviewScreen');
    const capturePreviewEnd = previewHarnessSource.indexOf('function CapturePreviewDrawing', capturePreviewStart);
    const capturePreviewMarkup = previewHarnessSource.slice(capturePreviewStart, capturePreviewEnd);
    const requiredBadgeAt = capturePreviewMarkup.indexOf('<Text style={styles.capturePreviewRequired}>');
    const permissionNoticeAt = capturePreviewMarkup.indexOf('{cameraDenied ? <Notice');
    const cameraActionAt = capturePreviewMarkup.indexOf('<PrimaryButton label={hasPhoto ?');
    const galleryActionAt = capturePreviewMarkup.indexOf('<SecondaryButton label="Chọn từ thư viện ảnh"');
    const photoSlotAt = capturePreviewMarkup.indexOf('<View style={styles.capturePreviewImageFrame}>');
    expect(captureScreenSource).toContain('Ảnh chỉ được gửi sau khi bạn chọn “Nhận diện tranh”.');
    const requiredPhotoNoticeAt = captureScreenSource.indexOf('Bước này sẽ tạo buổi học cho ảnh đã chọn rồi gửi tranh để nhận diện.');
    const continueActionAt = captureScreenSource.indexOf('Tạo buổi và nhận diện tranh');
    for (const position of [requiredBadgeAt, permissionNoticeAt, cameraActionAt, galleryActionAt, photoSlotAt, requiredPhotoNoticeAt, continueActionAt]) {
      expect(position).toBeGreaterThanOrEqual(0);
    }
    expect(requiredBadgeAt).toBeLessThan(permissionNoticeAt);
    expect(permissionNoticeAt).toBeLessThan(cameraActionAt);
    expect(cameraActionAt).toBeLessThan(galleryActionAt);
    expect(galleryActionAt).toBeLessThan(photoSlotAt);
    expect(photoSlotAt).toBeLessThan(requiredPhotoNoticeAt);
    expect(requiredPhotoNoticeAt).toBeLessThan(continueActionAt);
  });
});

describe('R3 story workflow safety boundaries', () => {
  it('keeps camera and gallery alternatives, pre-upload limits, and one artwork per run', () => {
    expect(captureScreenSource).toContain('requestCameraPermissionsAsync');
    expect(captureScreenSource).toContain('requestMediaLibraryPermissionsAsync');
    expect(captureScreenSource).toContain('launchImageLibraryAsync');
    expect(captureScreenSource).toContain('if (!permission.granted)');
    expect(captureScreenSource).toContain('isWithinOfflinePhotoLimit(sourceBytes)');
    expect(captureScreenSource).toContain('disabled={photoLocked || analysisBusy}');
    expect(captureScreenSource).toContain('disabled={busy || photoLocked || analysisBusy}');
    expect(profileControllerSource).toContain('function setAudio(value: SelectedAudio | null)');
    expect(profileControllerSource).toContain('setAudioValue(null)');
    expect(profileControllerSource).not.toMatch(/application\.learning\.(transcribeAudio|confirmTranscript)\(/);
    expect(ideaScreenSource).toContain('Audio.requestPermissionsAsync()');
    expect(ideaScreenSource).toContain('onChangeText={props.onIdea}');
    expect(ideaScreenSource).toContain('durationMillis >= 120_000');
    expect(profileControllerSource).toContain("stage.kind !== 'awaiting-drawing'");
    expect(profileControllerSource).toContain('!retakeAvailable');
    // Review F7b and F2: a cancelled wait never clears a newer action's busy flag, and a fresh run is not "processing".
    expect(profileControllerSource).toContain('function beginBusy(label: string): number');
    expect(profileControllerSource).toContain('if (busyEpoch.current === token) setBusy(\'\')');
    expect(profileControllerSource).toContain('function leaveWait(next: AppStep): void');
    expect(profileControllerSource).toContain('if (waitsBlocked.current)');
    expect(profileControllerSource).toContain('retakeUsed.current = false');
    expect(profileControllerSource).toContain('currentRunRevision: async () => (await readLiveRun(run.run_id)).run_revision');
    expect(parentExpoAppSource).toContain('parent.leaveWait(parent.videoBackStep)');
    expect(profileControllerSource).toContain('createRunAfterPhotoV1');
    expect(profileControllerSource).not.toContain('createRunBeforeDrawingV1(');
    expect(profileControllerSource).not.toContain('application.learning.generateSketchGuide(');
    expect(profileControllerSource).toContain('Gợi ý nét vẽ tự động 4–8 bước chưa khả dụng.');
    expect(parentApiSource).toContain('image_base64: string');
    expect(parentApiSource).not.toMatch(/generateSketchGuide\([\s\S]*?ordered_steps/);
    expect(profileControllerSource).toContain('retainedKeySet(drawingUploadAction');
    expect(profileControllerSource).toContain('await handleOrWaitDrawing(latest)');
    expect(profileControllerSource).not.toContain('drawingAnalysisAttemptedRunId');
    expect(captureScreenSource).toContain('step={stepLabel}');
    expect(understandingScreenSource).toContain('step={props.stepLabel}');
    expect(contextScreenSource).toContain('step={props.stepLabel}');
  });

  it('keeps guide output ordered and bounded, and subject review free of mismatch heuristics', () => {
    expect(drawingGuideScreenSource).toContain('parseDrawingGuideSteps(props.lesson.drawing_steps_text)');
    expect(drawingGuideScreenSource).toContain('guide.kind === \'steps\'');
    expect(understandingScreenSource).toContain('subject');
    expect(understandingScreenSource).not.toMatch(/toLowerCase\(\)[\s\S]{0,120}includes\(/);
    expect(understandingScreenSource).toContain('title="Nhận diện tranh"');
    expect(profileControllerSource).toContain('confirmSubjectV1(runId, understandingRevision, confirmedSubject, actionIdentity)');
    expect(profileControllerSource).not.toContain('readRunPinnedLessonActivities');
    expect(profileControllerSource).toMatch(/application\.learning\.listActivitiesV1\(/);
    expect(profileControllerSource).toMatch(/application\.learning\.selectActivityV1\(/);
    expect(activityScreenSource).toContain('Lưu lựa chọn và tiếp tục');
    expect(parentApiSource).toContain('/v1/activities?');
    expect(parentApiSource).toContain('/activity-selection');
    expect(parentApiSource).not.toContain('activity-suggestions');
    expect(parentApiSource).toContain('/context-confirmation');
    expect(parentApiSource).toContain('/script-confirmation');
    expect(storyScreenSource).not.toContain('mainActivityConfirmed');
    expect(parentExpoAppSource).not.toContain("onSkip={() => parent.setStep('story')}");
    expect(parentExpoAppSource).toContain('storyReady={storyReady}');
    expect(parentExpoAppSource).toContain('Boolean(\n    parent.contextRun?.run_id\n    && parent.contextConfirmed\n    && parent.subjectConfirmed');
  });

  it('requires GET reconciliation, exact story revision/hash pins, and no activity or media fields in story requests', () => {
    const analysisStart = profileControllerSource.indexOf('async function analyzeDrawingForRun');
    const analysisEnd = profileControllerSource.indexOf('async function analyzeDrawingForCurrentRun', analysisStart);
    const analysisSource = profileControllerSource.slice(analysisStart, analysisEnd);
    expect(analysisSource.indexOf('getLatestRun(runId)')).toBeGreaterThanOrEqual(0);
    // T-2b: the screen no longer calls the synchronous legacy route; the drawing goes through an upload session.
    expect(analysisSource.indexOf('getLatestRun(runId)')).toBeLessThan(analysisSource.indexOf('attachDrawingV1('));
    expect(analysisSource).not.toContain('understandDrawing(');
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
    expect(contextConfirmationSource).not.toContain('readRunPinnedLessonActivities');
    expect(contextConfirmationSource).toContain("contextConfirmationAction.current = null");
    expect(contextConfirmationSource).toContain('getLatestRun(run.run_id)');
    expect(contextConfirmationSource).not.toMatch(/catch[\s\S]*?confirmRunContextV1\(/);
    expect(contextConfirmationSource).toContain("cause.code === 'STALE_REVISION'");
    const selectionStart = profileControllerSource.indexOf('async function selectActivity');
    const selectionEnd = profileControllerSource.indexOf('async function handleStoryGateResult', selectionStart);
    const selectionSource = profileControllerSource.slice(selectionStart, selectionEnd);
    expect(selectionSource).toContain('expected_revision: latest.run_revision');
    expect(selectionSource).toContain('activity: selected.activity_ref');
    expect(selectionSource).toContain('application.learning.selectActivityV1');
    expect(selectionSource).toContain("cause.code === 'STALE_REVISION'");
    expect(selectionSource).toContain("cause.code === 'INVALID_STATE_TRANSITION'");
    expect(profileControllerSource).not.toContain('async function requestStory');
    expect(profileControllerSource).not.toContain('activitySelectionPersisted');
    expect(profileControllerSource).not.toContain('application.learning.createStoryRevisionV1');
    expect(profileControllerSource).toContain("state === 'SAFETY_BLOCKED' && run.story_revision_id");
    expect(homeScreenSource).toContain("run.run_state === 'SCRIPT_REVIEW' && run.video?.state === 'SAFETY_BLOCKED'");
    expect(storyScreenSource).toContain('props.confirmationRequired');
    expect(storyScreenSource).toContain('props.onlyCancel');
    expect(videoScreenSource).toContain('panel.postVideoActivities.map');
    expect(parentExpoAppSource).toContain('parent.watchHistoryRun(id)');
    expect(profileControllerSource).toContain("if (state === 'PREPARATION_REVIEW')");
    expect(profileControllerSource).toContain('await requestActivityList(false, run)');
    expect(profileControllerSource).toContain('await followFirstStory(run.run_id)');
    expect(analysisSource).not.toContain('PARENT_CONTEXT_NOT_CONFIRMED');
  });
});

describe('R4 absent delivery and lifecycle contracts', () => {
  it('keeps video and job operations typed unavailable without dispatching an adapter call', () => {
    // Goal v3 Phase B: the video routes are live and owned by the main controller; the platform hook keeps only the absent ones.
    expect(platformControllerSource).toContain("jobStatus: apiConfigured('job-status')");
    expect(platformControllerSource).toContain("video: apiConfigured('video')");
    expect(platformControllerSource).not.toContain('requestVideo');
    // Phase C review P2-1: the inbox and the run list never outlive the account that loaded them.
    expect(platformControllerSource).toContain('function resetAccountData(): void');
    expect(platformControllerSource).toContain('notificationActionKeys.current.clear()');
    expect(platformControllerSource).toContain('isDefinitiveNotificationFailure(failure)');
    expect(parentExpoAppSource).toContain('platform.resetAccountData()');
    expect(platformControllerSource).not.toContain('videoOperationState');
    expect(new Set(Array.from(platformControllerSource.matchAll(/application\.platform\.(\w+)/g), (match) => match[1])))
      .toEqual(new Set(['listRuns', 'cancelRunV1', 'deleteRunV1', 'listNotifications', 'markNotificationRead', 'markAllNotificationsRead']));
    expect(jobStageHasNoPercent).toBe(false);
    // The player lives only on the video step and receives headers, never a token in the address.
    expect(storyScreenSource).not.toMatch(/<(?:Video|VideoPlayer|VideoView)\b/);
    expect(videoScreenSource).toMatch(/<Video\b/);
    expect(videoScreenSource).toContain('headers: props.playback.headers');
    expect(videoScreenSource).not.toMatch(/[?&]token=|X-Playback-Token|Authorization/);
  });

  it('uses only resume for the active run and never claims video or run completion', () => {
    expect(handoffScreenSource).toContain('onResumeActiveRun');
    expect(handoffScreenSource).not.toContain('onRestart');
    expect(handoffScreenSource).not.toContain('resetWorkflow');
    expect(handoffScreenSource).toContain('Tạo video chưa khả dụng vì dịch vụ chưa được xác nhận.');
    expect(handoffScreenSource).toContain('Tác vụ hoàn tất; trình phát chưa khả dụng.');
    expect(parentExpoAppSource).toContain('onResumeActiveRun={parent.resumeActiveRun}');
  });

  it('does not present empty-success states or lifecycle actions when history routes are absent', () => {
    expect(parentExpoAppSource).toContain('<StoryHistoryScreen');
    expect(parentExpoAppSource).toContain('<LessonHistoryScreen');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.runs}');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.deliveries}');
    expect(storyHistoryScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(storyHistoryScreenSource.indexOf('const canCancel'));
    expect(storyHistoryScreenSource).toContain('Dịch vụ chưa có hợp đồng được xác nhận.');
    expect(lessonHistoryScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(lessonHistoryScreenSource.indexOf('Chưa có bài học được chia sẻ'));
    expect(lessonHistoryScreenSource).toContain('Bài đã dạy chưa khả dụng');
  });

  it('shows only confirmed quota and inbox summaries and provides no purchase action', () => {
    expect(parentExpoAppSource).toContain('<QuotaScreen');
    expect(parentExpoAppSource).toContain('<NotificationsScreen');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.quota}');
    expect(parentExpoAppSource).toContain('capability={platform.capabilities.notifications}');
    expect(quotaScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(quotaScreenSource.indexOf('>Còn lại<'));
    expect(quotaScreenSource).toContain('Chưa đủ dữ liệu hạn mức để hiển thị.');
    expect(quotaScreenSource).not.toContain('onPurchase');
    expect(notificationsScreenSource.indexOf("if (props.capability.state === 'unavailable')"))
      .toBeLessThan(notificationsScreenSource.indexOf('Chưa có thông báo nào'));
    expect(notificationsScreenSource).toContain('Danh sách chưa tải không cho biết bạn có hay không có thông báo mới.');
    expect(platformControllerSource).toContain("const notificationCapability = apiConfigured('notifications')");
    expect(notificationsScreenSource).toContain('classifyNotificationInbox');
    expect(notificationsScreenSource).toContain('notificationUnreadCountLabel');
    expect(notificationsScreenSource).not.toContain('item.notification_type');
    expect(notificationsScreenSource).not.toContain('item.safe_parameters');
    expect(notificationsScreenSource).not.toContain('item.title');
  });
});
