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
const captureScreenSource = readFileSync(new URL('../src/parent/presentation/screens/CaptureScreen.tsx', import.meta.url), 'utf8');
const drawingGuideScreenSource = readFileSync(new URL('../src/parent/presentation/screens/DrawingGuideScreen.tsx', import.meta.url), 'utf8');
const understandingScreenSource = readFileSync(new URL('../src/parent/presentation/screens/UnderstandingScreen.tsx', import.meta.url), 'utf8');
const contextScreenSource = readFileSync(new URL('../src/parent/presentation/screens/ContextScreen.tsx', import.meta.url), 'utf8');
const transcriptReviewSource = readFileSync(new URL('../src/parent/presentation/screens/TranscriptReviewScreen.tsx', import.meta.url), 'utf8');
const previewHarnessSource = readFileSync(new URL('../src/parent/presentation/ParentVisualPreviewHarness.tsx', import.meta.url), 'utf8');
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

  it('uses a native per-corner card edge and a shape cue for the selected aligned tab', () => {
    expect(uiSource).toContain('const outlineWidths = {\n  control: 1.5,\n  card: 1.6,\n  primary: 2,\n  focus: 3,\n} as const;');
    expect(uiSource).toContain('cardEdge: { borderWidth: outlineWidths.card, borderColor: palette.outline, borderTopLeftRadius: 22, borderTopRightRadius: 25, borderBottomRightRadius: 19, borderBottomLeftRadius: 23 }');
    expect(uiSource).toContain('return <View style={[styles.card, style, styles.cardEdge]}>{children}</View>;');
    expect(uiSource).not.toContain('cardOutlinePath');
    expect(uiSource).not.toContain('preserveAspectRatio="none"');
    expect(bottomBarSource).toContain('height: 62');
    expect(bottomBarSource).toContain('size={19}');
    expect(bottomBarSource).toContain('fontSize: 9');
    expect(bottomBarSource).toContain('paddingTop: 4');
    expect(bottomBarSource).toContain('paddingBottom: 4');
    expect(bottomBarSource).toContain('<View style={[styles.iconBadge, active && styles.activeIconBadge]}>');
    expect(bottomBarSource).toContain('activeIconBadge: { borderColor: palette.outline, backgroundColor: palette.butter }');
    expect(bottomBarSource).toContain('item: { flex: 1, minWidth: 0, minHeight: 52');
    expect(bottomBarSource).not.toContain('transform:');
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
    expect(authScreenSource).toContain('Chào mừng trở lại');
    expect(authScreenSource).toContain('PHỤ HUYNH');
    expect(authScreenSource).toContain('Sketch2Life · Phụ huynh');
    expect(authScreenSource).toContain('mode === \'signup\' ? \'Tạo tài khoản phụ huynh\' : \'Chào mừng trở lại\'');
    expect(authScreenSource).toContain('Đăng nhập để tiếp tục với hồ sơ gia đình.');
    expect(authScreenSource).toContain('Nếu địa chỉ hợp lệ, hướng dẫn sẽ được gửi. Màn hình không tiết lộ trạng thái đăng ký.');
    expect(authScreenSource).not.toContain('Tài khoản dùng để đăng nhập vào Sketch2Life.');
    expect(authScreenSource).not.toContain('Tài khoản được tạo trên Firebase Authentication và backend Sketch2Life.');
    expect(authScreenSource).not.toContain('<AuthIllustration');
    expect(authScreenSource).toContain('Đăng nhập bằng tài khoản phụ huynh đã xác thực.');
    expect(accountScreenSource).toContain('Mật khẩu đã được cập nhật.');
    expect(accountScreenSource).toContain('Đăng xuất sẽ kết thúc phiên này; cần xác thực lại để tiếp tục.');
    expect(accountScreenSource).not.toContain('Mật khẩu đã được cập nhật trên Firebase Authentication.');
    expect(googleSignInButtonSource).toContain('Đăng nhập bằng Google hiện chưa khả dụng. Bạn có thể dùng email để tiếp tục.');
    expect(googleSignInButtonSource).toContain('Chưa thể hoàn tất đăng nhập bằng Google. Hãy thử lại hoặc dùng email.');
    expect(googleSignInButtonSource).not.toContain('response.params.error_description');
    expect(googleSignInButtonSource).not.toContain('Google Sign-In chưa cấu hình.');
    expect(googleSignInButtonSource).toContain('minHeight: 52');
    expect(googleSignInButtonSource).toContain('name="logo-google" size={18}');
    expect(settingsScreenSource).toContain('Chỉ tạo gợi ý nét vẽ khi người lớn bật tùy chọn này trong buổi học.');
    expect(settingsScreenSource).toContain('Bật gợi ý nét vẽ trong phiên hiện tại');
    expect(settingsScreenSource).not.toContain('line-sketch');
    expect(settingsScreenSource).toContain('title="Cài đặt và tài khoản" subtitle="Quản lý đăng nhập phụ huynh."');
  });

  it('keeps each L1 surface on its named paper-card composition', () => {
    expect(uiSource).toContain("require('../../../../assets/applied/sketch2life-logo.png')");
    expect(uiSource).not.toContain('brandDotText');
    expect(authScreenSource).toContain("step={isRecovery ? undefined : 'PHỤ HUYNH'}");
    expect(authScreenSource).toContain('style={styles.introCard}');
    expect(authScreenSource).toContain('style={styles.formCard}');
    expect(authScreenSource).toContain('style={styles.recoveryCard}');
    expect(accountScreenSource).toContain('style={styles.emailRow}');
    expect(settingsScreenSource).toContain('style={styles.guideToggleRow}');
    expect(homeScreenSource).toContain('style={styles.selectedProfileBadge}');
    expect(homeScreenSource).toContain('style={styles.galleryRow}');
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
    expect(authScreenSource).toContain("onBack={isRecovery ? () => changeMode('signin') : undefined}");
    expect(authScreenSource).not.toContain('onRecovery');
  });

  it('starts profile fields blank, keeps gender local, and shows sharing as unavailable without sample grants', () => {
    expect(profileFormSource).toContain("useState(profile ? String(profile.age_months) : '')");
    expect(profileFormSource).toContain('placeholder="Nhập tên hiển thị"');
    expect(profileFormSource).toContain('Lựa chọn giới tính chỉ là bản nháp trên thiết bị; chưa được gửi, lưu hoặc dùng để tạo câu chuyện.');
    expect(profileFormSource).toContain('Giới tính của trẻ (tùy chọn)');
    expect(profileFormSource).toContain('Không muốn chia sẻ');
    expect(profileFormSource).toContain('CHILD_AGE_RANGE_MESSAGE');
    expect(profileFormSource).toContain('disabled={!displayName.trim() || !ageValid}');
    expect(profileFormSource).toContain('ageMonths.trim().length > 0 && !ageValid');
    expect(profileFormSource).not.toContain('Ví dụ: Bé Mây');
    expect(profileFormSource).not.toContain('Thiên nhiên, côn trùng…');
    expect(profileSharingSource).toContain("props.capability.state === 'unavailable' ? <Card");
    expect(profileSharingSource).toContain('Chỉ mời giáo viên được nêu tên.');
    expect(profileSharingSource).toContain('Chưa thể gửi lời mời hoặc kiểm tra quyền chia sẻ. Chưa có thay đổi quyền nào được xác nhận.');
    expect(profileSharingSource).not.toContain('phạm vi 90 ngày');
  });

  it('keeps home and profile actions on the existing run, selection, and eligibility conditions', () => {
    expect(homeScreenSource).toContain('Cùng con bắt đầu một hành trình khám phá.');
    expect(homeScreenSource).toContain('Minh họa tĩnh bằng nét SVG, không phải tranh của trẻ.');
    expect(homeScreenSource).toContain('viewBox="0 0 280 120"');
    expect(homeScreenSource).toContain('aspectRatio: 280 / 120');
    expect(homeScreenSource).toContain('accessibilityLabel="Khám phá bài giảng"');
    expect(homeScreenSource).toContain('onPress={onOpenLessons}');
    expect(homeScreenSource).toContain('onPress={activeRun ? onResumeRun : onStart}');
    expect(homeScreenSource).toContain("label={activeRun ? 'Tiếp tục buổi đang mở' : 'Bắt đầu buổi vẽ'}");
    expect(homeScreenSource).toContain('Chưa có hồ sơ được chọn.');
    expect(homeScreenSource).toContain('Quản lý hồ sơ');
    expect(homeScreenSource).not.toContain('Tạo hồ sơ để lưu độ tuổi và sở thích cho từng buổi.');
    expect(homeScreenSource).not.toContain('hồ sơ đã sẵn sàng.');
    expect(homeScreenSource).not.toContain('Không gian của gia đình');
    expect(homeScreenSource).not.toContain('Tài khoản và bảo mật');
    expect(bottomBarSource).toContain("{ id: 'activity', label: 'Hoạt động', icon: 'time-outline' }");
    expect(bottomBarSource).toContain('accessibilityRole="button"');
    expect(bottomBarSource).toContain("startLabel === 'Tiếp tục'");
    expect(parentExpoAppSource).toContain("if (tab === 'activity') return openHistory('home');");
    expect(parentExpoAppSource).toContain('onStart={startOrResume}');
    expect(parentExpoAppSource).toContain("mainSection('activity', <StoryHistoryScreen");
    expect(bottomBarSource).toContain("{ id: 'profiles', label: 'Gia đình'");
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
    expect(profileScreenSource).toContain('Mỗi buổi học chỉ gắn với một hồ sơ trẻ.');
    expect(profileScreenSource.indexOf('Mỗi buổi học chỉ gắn với một hồ sơ trẻ.'))
      .toBeLessThan(profileScreenSource.indexOf('<Card style={styles.profileListCard}>'));
    expect(profileScreenSource).toContain('disabled={!mayStartRun}');
    expect(profileScreenSource).toContain('Hồ sơ cũ, chỉ xem hoặc xóa');
    expect(profileScreenSource).toContain('không ngăn bạn tiếp tục với hồ sơ đủ điều kiện');
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
    expect(profileFormSource).toContain('Lựa chọn giới tính chỉ là bản nháp trên thiết bị; chưa được gửi, lưu hoặc dùng để tạo câu chuyện.');
    expect(profileSharingSource).not.toContain('phạm vi 90 ngày');
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
    expect(lessonPickerSource).toContain('title="Bài học từ thư viện"');
    expect(lessonPickerSource).toContain('Bạn chưa thể tiếp tục nếu chưa ghim một phiên bản bài học');
    expect(lessonPickerSource).not.toContain('Tiếp tục không dùng bài giảng');
    expect(topicScreenSource).toContain('cần ghim một phiên bản bài học chính xác để tiếp tục.');
    expect(topicScreenSource).toContain('Chuyển giọng nói thành chữ hiện chưa khả dụng');
    expect(topicScreenSource).toContain('onPress={() => props.onTopic(topic)}');
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

  it('keeps L2 screens on paper cards and gates the synthetic preview outside normal app flow', () => {
    expect(topicScreenSource).toContain('Gợi ý nét vẽ do trí tuệ nhân tạo tạo');
    expect(topicScreenSource).not.toContain('Gợi ý nét vẽ do AI tạo');
    expect(topicScreenSource).not.toContain('Gợi ý line sketch được tạo bởi AI');
    expect(lessonGallerySource).toContain('catalogCard: {\n    padding: 13,\n    backgroundColor: palette.white,\n    gap: 12,\n    minWidth: 0,');
    expect(lessonGallerySource).toContain('activity: {\n    gap: 8,\n    borderTopWidth: 1,');
    expect(lessonPickerSource).toContain('lessonCard: { backgroundColor: palette.white, gap: 8, minWidth: 0 }');
    expect(topicScreenSource).toContain('guideImage: { width: \'100%\', height: 240');
    expect(drawingGuideScreenSource).toContain('title="Gợi ý vẽ (tùy chọn)"');
    expect(drawingGuideScreenSource).toContain('<PrimaryButton label="Bỏ qua hướng dẫn" onPress={props.onContinue} />');
    expect(drawingGuideScreenSource).toContain('currentStep: { color: palette.ink');
    expect(captureScreenSource).toContain('aspectRatio: 280 / 190, minHeight: 190');
    expect(captureScreenSource).toContain('<Text style={styles.requiredBadge}>BẮT BUỘC</Text>');
    expect(transcriptReviewSource).toContain('emptyCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(understandingScreenSource).toContain('candidateCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(understandingScreenSource).toContain('label="Xác nhận chủ thể này"');
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
    expect(previewHarnessSource).toContain('const previewTranscript: ParentAudioTranscription | null = null;');
    expect(transcriptReviewSource).toContain('{props.transcript ? <Card style={styles.transcriptCard}>');
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
    expect(activityScreenSource).toContain('title="Gợi ý hoạt động"');
    expect(activityScreenSource).toContain('onPress={props.onSkip}');
    expect(activityScreenSource).toContain('return \'Chưa xác định loại hoạt động\';');
    expect(activityScreenSource).toContain('activityCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(activityScreenSource).toContain('styles.emptyCard');
    expect(storyScreenSource).toContain('title="Rà soát kịch bản"');
    expect(storyScreenSource).toContain('storyLanguageLabel(props.story.language)');
    expect(storyScreenSource).toContain('Gửi gợi ý viết lại · tối đa 3 lần');
    expect(storyScreenSource).toContain('props.rewriteCount < 3');
    expect(storyScreenSource).not.toContain('Ví dụ:');
    expect(storyScreenSource).toContain('generationCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(storyScreenSource).toContain('style={styles.scene}');
    expect(storyScreenSource).toContain("scene: { borderTopWidth: 1.3, borderTopColor: '#CFC3B3', paddingTop: 10, gap: 8, minWidth: 0 }");
    expect(handoffScreenSource).toContain('title="Trạng thái buổi học"');
    expect(handoffScreenSource).toContain('style={styles.statusCard}');
    expect(handoffScreenSource).toContain('eventRow: { flexDirection: \'row\', alignItems: \'flex-start\', justifyContent: \'space-between\'');
    expect(handoffScreenSource).toContain('eventStageLabel(event.stage)');
    expect(handoffScreenSource).toContain('Không hiển thị phần trăm, thời gian dự kiến hoặc vị trí hàng đợi.');
    expect(handoffScreenSource).not.toContain('event.durationMs');
    expect(storyHistoryScreenSource).toContain('runCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(storyHistoryScreenSource).toContain("return labels[value] ?? 'Trạng thái chưa xác định'");
    expect(lessonHistoryScreenSource).toContain('title="Bài học đã xem"');
    expect(lessonHistoryScreenSource).toContain('deliveryCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(quotaScreenSource).toContain('Tóm tắt lượt dùng');
    expect(quotaScreenSource).toContain('quotaCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 }');
    expect(notificationsScreenSource).toContain('Thông tin dành riêng cho tài khoản phụ huynh.');
    expect(notificationsScreenSource).toContain('Đánh dấu đã đọc');
    expect(notificationsScreenSource).toContain("style={[styles.notificationCard, { backgroundColor: item.read_at ? palette.white : palette.paleBlue }]}");
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
    expect(captureScreenSource).toContain('Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh.');
    const requiredPhotoNoticeAt = capturePreviewMarkup.indexOf('<Notice text="Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh."');
    const continueActionAt = capturePreviewMarkup.indexOf('<PrimaryButton label="Tiếp tục sau khi chọn ảnh"');
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
