import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Image,
  Pressable,
  ActivityIndicator,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  useWindowDimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFonts } from 'expo-font';
import Svg, { Path } from 'react-native-svg';
import { colors, radius, shadows } from '../theme';
import { Kid3DButton } from '../components/Kid3DButton';
import {
  LogoSketch2Life,
  CatDrawingArtwork,
  RainbowFishArtwork,
  StoryRobotArtwork,
  SplashHeroIllustration,
  OnboardingHeroIllustration,
  VoiceGirlMicIllustration,
  MomAvatarImage,
  SunIconSvg,
  ChildAvatarImage,
  BounceInView,
  CuteStarIconSvg,
} from '../components/ArtworkCards';

import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';
import type { ChildLearningProfileInput } from '../demo/api';
import {
  adjustChildAgeByMonths,
  adjustChildAgeByYears,
  formatChildAge,
  splitChildAgeMonths,
} from '../demo/childAge.mjs';
import {
  acceptPreferenceClassification,
  PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT,
  PreferenceRevisionGate,
} from '../demo/preferenceRevisionGate.mjs';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

const PROFILE_SUPPORTS = [
  ['HANDS_ON', 'Thích tự tay thao tác'],
  ['MOVEMENT', 'Thích hoạt động có vận động'],
  ['VISUAL_SEQUENCE', 'Hợp với các bước trực quan'],
  ['OBSERVATION', 'Thích quan sát, khám phá'],
] as const;
const PROFILE_INPUT_METRIC_SAMPLE_COUNT = 24;
// No Firebase client adapter or Google provider configuration is present in
// this repository yet. Keep the entry point visibly discoverable but disabled
// until it can issue a real Firebase credential and backend-authorized session.
const GOOGLE_SIGN_IN_SUPPORTED = false;
const LOGIN_INPUT_WEB_FOCUS_RESET =
  Platform.OS === 'web'
    ? ({ outlineStyle: 'none', outlineWidth: 0, outlineColor: 'transparent' } as any)
    : null;

// ==========================================
// Parent SRS V2.2 — LOGIN
// ==========================================
const LOGIN_ARTBOARD = { width: 941, height: 1672 } as const;
const LOGIN_ARTWORK_LAYOUT = {
  title: { x: 168, y: 710, width: 605, height: 72 },
  // The compact login title replaces the previous welcome copy, so bring the
  // interactive form up into that freed space while keeping it inside the
  // illustrated card's safe area.
  emailLabel: { x: 130, y: 820, width: 680, height: 38 },
  emailField: { x: 128, y: 930, width: 685, height: 87 },
  passwordLabel: { x: 130, y: 1044, width: 680, height: 38 },
  passwordField: { x: 128, y: 1097, width: 685, height: 87 },
  primaryButton: { x: 126, y: 1220, width: 690, height: 102 },
} as const;

/** Official Google G mark, kept as vector artwork so it is never stretched. */
const GoogleMark: React.FC<{ size?: number }> = ({ size = 22 }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <Path
      fill="#4285F4"
      d="M23.49 12.27c0-.79-.07-1.55-.2-2.27H12v4.3h6.45a5.51 5.51 0 0 1-2.39 3.61v3h3.87c2.27-2.09 3.56-5.17 3.56-8.64Z"
    />
    <Path
      fill="#34A853"
      d="M12 24c3.24 0 5.95-1.07 7.93-2.91l-3.87-3A7.18 7.18 0 0 1 12 19.22a7.2 7.2 0 0 1-6.77-4.98H1.23v3.09A12 12 0 0 0 12 24Z"
    />
    <Path
      fill="#FBBC05"
      d="M5.23 14.24A7.2 7.2 0 0 1 4.85 12c0-.78.13-1.54.38-2.24V6.67H1.23A12 12 0 0 0 0 12c0 1.93.46 3.75 1.23 5.33l4-3.09Z"
    />
    <Path
      fill="#EA4335"
      d="M12 4.77c1.76 0 3.34.61 4.58 1.81l3.43-3.43C17.94 1.17 15.24 0 12 0A12 12 0 0 0 1.23 6.67l4 3.09A7.2 7.2 0 0 1 12 4.77Z"
    />
  </Svg>
);

export const LoginScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;
  const [fontsLoaded] = useFonts({
    MaliBold: require('../../assets/fonts/Mali-Bold.ttf'),
    MaliSemiBold: require('../../assets/fonts/Mali-SemiBold.ttf'),
    ItimRegular: require('../../assets/fonts/Itim-Regular.ttf'),
  });
  const { width: viewportWidth, height: viewportHeight } = useWindowDimensions();
  // The web preview wraps the real screen in a phone chassis, so
  // useWindowDimensions() describes the browser window rather than the
  // drawable screen. Measure the actual ScrollView viewport before mapping
  // the illustration's source coordinates to displayed coordinates.
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });
  const canvasWidth = canvasSize.width || viewportWidth;
  const canvasHeight = canvasSize.height || viewportHeight;
  // The desktop preview's phone viewport is shorter than a real 393x852
  // device. Keep the same artwork coordinates, but tighten only the optional
  // auth affordances/gaps so Google + registration remain discoverable without
  // shrinking the required 44/48dp controls.
  const isCompactLoginViewport = Platform.OS === 'web' && canvasHeight < 700;
  const imageScale = Math.max(
    canvasWidth / LOGIN_ARTBOARD.width,
    canvasHeight / LOGIN_ARTBOARD.height,
  );
  const displayedImageWidth = LOGIN_ARTBOARD.width * imageScale;
  const displayedImageHeight = LOGIN_ARTBOARD.height * imageScale;
  const imageLeft = (canvasWidth - displayedImageWidth) / 2;
  const imageTop = (canvasHeight - displayedImageHeight) / 2;
  const mapArtworkRect = (
    rect: { x: number; y: number; width: number; height: number },
    minimumHeight = 0,
  ) => ({
    position: 'absolute' as const,
    left: imageLeft + rect.x * imageScale,
    top: imageTop + rect.y * imageScale,
    width: rect.width * imageScale,
    height: Math.max(minimumHeight, rect.height * imageScale),
  });
  const mapArtworkPosition = (
    rect: { x: number; y: number; width: number },
  ) => ({
    position: 'absolute' as const,
    left: imageLeft + rect.x * imageScale,
    top: imageTop + rect.y * imageScale,
    width: rect.width * imageScale,
  });
  const titleFontSize = Math.max(22, Math.min(28, 50 * imageScale));
  const labelFontSize = Math.max(14, Math.min(17, 31 * imageScale));
  const controlFontSize = Math.max(13, Math.min(16, 28 * imageScale));
  const buttonFontSize = Math.max(16, Math.min(19, 36 * imageScale));
  const fieldHeight = Math.max(44, LOGIN_ARTWORK_LAYOUT.emailField.height * imageScale);
  const labelHeight = Math.max(17, (isCompactLoginViewport ? 34 : 38) * imageScale);
  const labelFieldGap = Math.max(6, 14 * imageScale);
  const sectionGap = isCompactLoginViewport ? 2 : Math.max(8, Math.min(12, 20 * imageScale));
  const buttonGap = isCompactLoginViewport ? 4 : Math.max(8, Math.min(10, 24 * imageScale));
  const errorFontSize = Math.max(12, Math.min(14, 26 * imageScale));
  const errorLineHeight = Math.max(15, errorFontSize * 1.15);
  // Reserve the same line under each field in both valid and invalid states.
  // This keeps the Google/register actions from jumping when validation appears.
  const errorSlotHeight = isCompactLoginViewport ? 15 : Math.max(16, Math.min(20, 24 * imageScale));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authOverlay, setAuthOverlay] = useState<'register' | 'forgot' | null>(null);
  const [authOverlayEmail, setAuthOverlayEmail] = useState('');
  const [authOverlayPassword, setAuthOverlayPassword] = useState('');
  const [authOverlayNotice, setAuthOverlayNotice] = useState('');

  const validateEmail = (value: string) => {
    const normalizedEmail = value.trim();
    if (!normalizedEmail) return 'Vui lòng nhập email.';
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)
      ? ''
      : 'Email chưa đúng định dạng.';
  };

  const validatePassword = (value: string) => {
    // The current SRS/repository does not define a client-side password
    // strength rule. Keep the UI contract to the required-field check only.
    return value ? '' : 'Vui lòng nhập mật khẩu.';
  };

  const handleEmailBlur = () => {
    setEmailFocused(false);
    setEmailError(validateEmail(email));
  };

  const handlePasswordBlur = () => {
    setPasswordFocused(false);
    setPasswordError(validatePassword(password));
  };

  const handleLoginPress = () => {
    if (isSubmitting) return;
    const nextEmailError = validateEmail(email);
    const nextPasswordError = validatePassword(password);
    setEmailError(nextEmailError);
    setPasswordError(nextPasswordError);
    if (nextEmailError || nextPasswordError) return;
    setIsSubmitting(true);
    // Keep the existing navigation contract. Real Firebase/backend auth is
    // intentionally not invented in this UI-only layer.
    try {
      nav('profile_list');
    } catch {
      setIsSubmitting(false);
    }
  };

  if (!fontsLoaded) {
    return <View style={styles.loginScreen} />;
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.loginScreen}
    >
      <ScrollView
        style={styles.loginScroll}
        onLayout={({ nativeEvent: { layout } }) => {
          setCanvasSize((previous) => {
            // Keep the original portrait canvas when Android resizes the
            // viewport for the keyboard; the ScrollView can then pan to the
            // focused field instead of shrinking/cropping the illustration.
            const measuredHeight = previous.height === 0
              ? layout.height
              : Math.max(previous.height, layout.height);
            if (layout.width === previous.width && measuredHeight === previous.height) return previous;
            return { width: layout.width, height: measuredHeight };
          });
        }}
        contentContainerStyle={{ minHeight: canvasHeight }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View
          style={[styles.illustratedLoginCanvas, { height: canvasHeight }]}
        >
          <Image
            accessibilityLabel="Minh họa nền Sketch2Life"
            source={require('../../assets/images/login/login_illustrated_background.png')}
            style={{
              position: 'absolute',
              left: imageLeft,
              top: imageTop,
              width: displayedImageWidth,
              height: displayedImageHeight,
            }}
            resizeMode="contain"
          />

          <View pointerEvents="box-none" style={styles.illustratedLoginOverlay}>
            <Text style={[styles.illustratedTitle, mapArtworkRect(LOGIN_ARTWORK_LAYOUT.title), { fontSize: titleFontSize, lineHeight: titleFontSize * 1.15 }]}>
              Đăng nhập
            </Text>

            <View style={[styles.illustratedFormStack, mapArtworkPosition({ x: LOGIN_ARTWORK_LAYOUT.emailField.x, y: LOGIN_ARTWORK_LAYOUT.emailLabel.y, width: LOGIN_ARTWORK_LAYOUT.emailField.width })]}>
              <Text style={[styles.illustratedFlowLabel, { minHeight: labelHeight, marginLeft: 2 * imageScale, fontSize: labelFontSize, lineHeight: labelFontSize * 1.2 }]}>
                Email
              </Text>
              <View style={[styles.illustratedField, { height: fieldHeight, marginTop: labelFieldGap }, emailFocused && styles.illustratedFieldFocused, emailError && styles.illustratedFieldError]}>
                <Image source={require('../../assets/images/login/icon_email.png')} style={styles.illustratedFieldIcon} resizeMode="contain" />
                <TextInput
                  accessibilityLabel="Email phụ huynh"
                  autoCapitalize="none"
                  autoComplete="email"
                  keyboardType="email-address"
                  placeholder="Nhập email của bạn"
                  placeholderTextColor="#64748B"
                  value={email}
                  onChangeText={(value) => {
                    setEmail(value);
                    if (emailError) setEmailError('');
                  }}
                  onFocus={() => setEmailFocused(true)}
                  onBlur={handleEmailBlur}
                  style={[styles.illustratedInput, LOGIN_INPUT_WEB_FOCUS_RESET, { fontSize: controlFontSize }]}
                  accessibilityHint={emailError || 'Nhập địa chỉ email của phụ huynh.'}
                />
              </View>
              <View style={[styles.illustratedErrorSlot, { minHeight: errorSlotHeight, marginTop: isCompactLoginViewport ? 2 : 5 }]}>
                {emailError && (
                  <Text
                    accessibilityRole="alert"
                    accessibilityLiveRegion="polite"
                    style={[styles.illustratedFieldErrorText, { fontSize: errorFontSize, lineHeight: errorLineHeight }]}
                  >
                    {emailError}
                  </Text>
                )}
              </View>

              <View style={[styles.illustratedPasswordHeaderRow, { minHeight: labelHeight, marginTop: sectionGap }]}>
                <Text style={[styles.illustratedFlowLabel, { fontSize: labelFontSize, lineHeight: labelFontSize * 1.2 }]}>
                  Mật khẩu
                </Text>
                <Pressable
                  accessibilityRole="link"
                  accessibilityLabel="Quên mật khẩu"
                  accessibilityHint="Khôi phục mật khẩu chưa được cấu hình trong phiên bản này."
                  onPress={() => {
                    setAuthOverlayNotice('');
                    setAuthOverlay('forgot');
                  }}
                  hitSlop={8}
                >
                  <Text style={[styles.illustratedForgotLink, { fontSize: Math.max(12, controlFontSize - 1) }]}>Quên mật khẩu?</Text>
                </Pressable>
              </View>
              <View style={[styles.illustratedField, { height: fieldHeight, marginTop: labelFieldGap }, passwordFocused && styles.illustratedFieldFocused, passwordError && styles.illustratedFieldError]}>
                <Image source={require('../../assets/images/login/icon_lock.png')} style={[styles.illustratedFieldIcon, styles.illustratedLockIcon]} resizeMode="contain" />
                <TextInput
                  accessibilityLabel="Mật khẩu phụ huynh"
                  autoCapitalize="none"
                  autoComplete="password"
                  placeholder="Nhập mật khẩu"
                  placeholderTextColor="#64748B"
                  secureTextEntry={!passwordVisible}
                  value={password}
                  onChangeText={(value) => {
                    setPassword(value);
                    if (passwordError) setPasswordError('');
                  }}
                  onFocus={() => setPasswordFocused(true)}
                  onBlur={handlePasswordBlur}
                  style={[styles.illustratedInput, LOGIN_INPUT_WEB_FOCUS_RESET, { fontSize: controlFontSize }]}
                  accessibilityHint={passwordError || 'Nhập mật khẩu của phụ huynh.'}
                />
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel={passwordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  hitSlop={10}
                  onPress={() => setPasswordVisible((visible) => !visible)}
                  style={styles.illustratedPasswordToggle}
                >
                  <Image source={require('../../assets/images/login/icon_eye.png')} style={styles.illustratedEyeIcon} resizeMode="contain" />
                </TouchableOpacity>
              </View>
              <View style={[styles.illustratedErrorSlot, { minHeight: errorSlotHeight, marginTop: isCompactLoginViewport ? 2 : 5 }]}>
                {passwordError && (
                  <Text
                    accessibilityRole="alert"
                    accessibilityLiveRegion="polite"
                    style={[styles.illustratedFieldErrorText, { fontSize: errorFontSize, lineHeight: errorLineHeight }]}
                  >
                    {passwordError}
                  </Text>
                )}
              </View>

              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Đăng nhập và tiếp tục"
                accessibilityState={{ busy: isSubmitting, disabled: isSubmitting }}
                disabled={isSubmitting}
                onPress={handleLoginPress}
                style={({ pressed }) => [styles.illustratedPrimaryButton, { height: Math.max(48, (isCompactLoginViewport ? 94 : LOGIN_ARTWORK_LAYOUT.primaryButton.height) * imageScale), marginTop: buttonGap }, pressed && styles.loginButtonPressed]}
              >
                {isSubmitting ? <ActivityIndicator color="#FFFFFF" size="small" /> : (
                  <>
                    <Text style={[styles.illustratedButtonText, { fontSize: buttonFontSize }]}>Đăng nhập</Text>
                    <Ionicons name="arrow-forward" size={Math.max(19, buttonFontSize + 3)} color="#FFFFFF" />
                  </>
                )}
              </Pressable>

              <View style={[styles.illustratedDivider, isCompactLoginViewport && styles.illustratedDividerCompact]}>
                <View style={styles.illustratedDividerLine} />
                <Text style={[styles.illustratedDividerText, { fontSize: controlFontSize }]}>hoặc</Text>
                <View style={styles.illustratedDividerLine} />
              </View>

              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Đăng nhập với Google"
                accessibilityHint={GOOGLE_SIGN_IN_SUPPORTED ? 'Sử dụng tài khoản Google để đăng nhập.' : 'Google Sign-In chưa được cấu hình trong ứng dụng.'}
                accessibilityState={{ disabled: !GOOGLE_SIGN_IN_SUPPORTED }}
                disabled={!GOOGLE_SIGN_IN_SUPPORTED}
                style={({ pressed }) => [
                  styles.illustratedGoogleButton,
                  !GOOGLE_SIGN_IN_SUPPORTED && styles.illustratedGoogleButtonUnavailable,
                  pressed && styles.loginButtonPressed,
                ]}
              >
                <GoogleMark size={Math.max(20, Math.min(24, 24 * imageScale))} />
                <Text style={[styles.illustratedGoogleText, { fontSize: Math.max(14, buttonFontSize - 1) }]}>Đăng nhập với Google</Text>
              </Pressable>

              <View style={[styles.illustratedRegistrationRow, isCompactLoginViewport && styles.illustratedRegistrationRowCompact]}>
                <Text style={[styles.illustratedRegistrationCopy, { fontSize: controlFontSize }]}>Chưa có tài khoản? </Text>
                <Pressable
                  accessibilityRole="link"
                  accessibilityLabel="Đăng ký ngay"
                  accessibilityHint="Màn hình đăng ký phụ huynh chưa được cấu hình trong phiên bản này."
                  onPress={() => {
                    setAuthOverlayNotice('');
                    setAuthOverlay('register');
                  }}
                  hitSlop={8}
                >
                  <Text style={[styles.illustratedRegistrationLink, { fontSize: controlFontSize }]}>Đăng ký ngay</Text>
                </Pressable>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
      {authOverlay && (
        <View style={styles.authFlowOverlay} accessibilityViewIsModal>
          <ScrollView
            contentContainerStyle={styles.authFlowOverlayContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.authFlowCard}>
              <View style={styles.authFlowHeader}>
                <Text style={styles.authFlowTitle}>
                  {authOverlay === 'register' ? 'Tạo tài khoản' : 'Quên mật khẩu?'}
                </Text>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Đóng"
                  onPress={() => setAuthOverlay(null)}
                  hitSlop={10}
                  style={styles.authFlowClose}
                >
                  <Ionicons name="close" size={22} color="#5B3018" />
                </Pressable>
              </View>

              <Text style={styles.authFlowDescription}>
                {authOverlay === 'register'
                  ? 'Tạo không gian riêng để quản lý hồ sơ và câu chuyện của con.'
                  : 'Nhập email để nhận hướng dẫn khôi phục mật khẩu.'}
              </Text>

              {authOverlay === 'register' && (
                <>
                  <Text style={styles.authFlowLabel}>Họ tên</Text>
                  <View style={styles.authFlowInputWrap}>
                    <Ionicons name="person-outline" size={20} color="#7C8798" />
                    <TextInput
                      accessibilityLabel="Họ tên phụ huynh"
                      placeholder="Nhập họ tên của bạn"
                      placeholderTextColor="#7C8798"
                      style={styles.authFlowInput}
                    />
                  </View>
                </>
              )}

              <Text style={styles.authFlowLabel}>Email</Text>
              <View style={styles.authFlowInputWrap}>
                <Ionicons name="mail-outline" size={20} color="#7C8798" />
                <TextInput
                  accessibilityLabel="Email phụ huynh"
                  autoCapitalize="none"
                  autoComplete="email"
                  keyboardType="email-address"
                  placeholder="Nhập email của bạn"
                  placeholderTextColor="#7C8798"
                  value={authOverlayEmail}
                  onChangeText={setAuthOverlayEmail}
                  style={styles.authFlowInput}
                />
              </View>

              {authOverlay === 'register' && (
                <>
                  <Text style={styles.authFlowLabel}>Mật khẩu</Text>
                  <View style={styles.authFlowInputWrap}>
                    <Ionicons name="lock-closed-outline" size={20} color="#7C8798" />
                    <TextInput
                      accessibilityLabel="Mật khẩu tài khoản mới"
                      autoCapitalize="none"
                      placeholder="Tạo mật khẩu"
                      placeholderTextColor="#7C8798"
                      secureTextEntry
                      value={authOverlayPassword}
                      onChangeText={setAuthOverlayPassword}
                      style={styles.authFlowInput}
                    />
                  </View>
                </>
              )}

              <Pressable
                accessibilityRole="button"
                accessibilityLabel={authOverlay === 'register' ? 'Đăng ký tài khoản' : 'Gửi liên kết khôi phục'}
                onPress={() => setAuthOverlayNotice('UI đã sẵn sàng; bước kết nối xác thực sẽ được nối sau.')}
                style={({ pressed }) => [styles.authFlowPrimaryButton, pressed && styles.loginButtonPressed]}
              >
                <Text style={styles.authFlowPrimaryText}>
                  {authOverlay === 'register' ? 'Đăng ký' : 'Gửi liên kết'}
                </Text>
                <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
              </Pressable>

              {authOverlayNotice && (
                <Text accessibilityRole="alert" style={styles.authFlowNotice}>{authOverlayNotice}</Text>
              )}

              <Pressable
                accessibilityRole="link"
                accessibilityLabel="Quay lại đăng nhập"
                onPress={() => setAuthOverlay(null)}
                style={styles.authFlowBackLink}
              >
                <Text style={styles.authFlowBackText}>Quay lại đăng nhập</Text>
              </Pressable>
            </View>
          </ScrollView>
        </View>
      )}
    </KeyboardAvoidingView>
  );
};

const ChoiceChip: React.FC<{
  label: string;
  selected: boolean;
  disabled?: boolean;
  onPress: () => void;
}> = ({ label, selected, disabled, onPress }) => (
  <TouchableOpacity
    accessibilityRole="checkbox"
    accessibilityState={{ checked: selected, disabled: Boolean(disabled) }}
    onPress={onPress}
    disabled={disabled}
    style={{
      borderRadius: 18,
      borderWidth: 1,
      borderColor: selected ? '#2563EB' : '#CBD5E1',
      backgroundColor: selected ? '#DBEAFE' : '#FFFFFF',
      opacity: disabled ? 0.45 : 1,
      paddingHorizontal: 11,
      paddingVertical: 8,
    }}
  >
    <Text style={{ color: selected ? '#1D4ED8' : '#475569', fontSize: 12, fontWeight: '700' }}>
      {selected ? '✓ ' : ''}{label}
    </Text>
  </TouchableOpacity>
);

// ==========================================
// 1. SPLASH SCREEN (Image 2 - Screen 1)
// ==========================================
export const SplashScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;

  useEffect(() => {
    const timer = setTimeout(() => {
      nav('onboarding');
    }, 3000);
    return () => clearTimeout(timer);
  }, [nav]);

  return (
    <TouchableOpacity
      activeOpacity={0.96}
      onPress={() => nav('onboarding')}
      style={{
        flex: 1,
        backgroundColor: '#FFFFFF',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 36,
        paddingHorizontal: 20,
      }}
    >
      {/* Top Brand Logo & Tagline — 100% Crisp Native Vector */}
      <View style={{ alignItems: 'center', marginTop: 16 }}>
        <LogoSketch2Life size="lg" showTagline={false} />
        <Text style={{ fontSize: 13, fontWeight: '700', color: '#1E40AF', marginTop: 6, textAlign: 'center' }}>
          Mỗi nét vẽ đều có một câu chuyện đang chờ được kể...
        </Text>
      </View>

      {/* Center Hero: Crisp HD Girl + Dino Artwork with Floating Animation */}
      <View style={{ width: '100%', flex: 1, justifyContent: 'center', alignItems: 'center', marginVertical: 8 }}>
        <SplashHeroIllustration height={340} />
      </View>

      {/* Bottom Inspiration Quote — 100% Crisp Native Vector, Never Cropped */}
      <View style={{ alignItems: 'center', marginBottom: 8 }}>
        <Text style={{ fontSize: 13, fontWeight: '800', color: '#1E3A8A', textAlign: 'center' }}>Vẽ hôm nay</Text>
        <Text style={{ fontSize: 12, fontWeight: '600', color: '#2563EB', textAlign: 'center', marginTop: 3 }}>
          Một thế giới diệu kỳ ngày mai ♡
        </Text>
      </View>
    </TouchableOpacity>
  );
};

// ==========================================
// 2. ONBOARDING SCREEN (Image 2 - Screen 2)
// ==========================================
export const OnboardingScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header with ONLY "Bỏ qua" on right matching Image 2 */}
      <View style={[styles.topHeader, { justifyContent: 'flex-end' }]}>
        <TouchableOpacity onPress={() => nav('dashboard')}>
          <Text style={styles.skipBtn}>Bỏ qua</Text>
        </TouchableOpacity>
      </View>

      {/* Main Heading */}
      <View style={styles.headingBox}>
        <Text style={[styles.headingTitle, { fontSize: 24, color: '#1E40AF', lineHeight: 30 }]}>{"Nét vẽ của con\ncó thể sống dậy!"}</Text>
        <Text style={styles.headingSubtitle}>
          Sketch2Life giúp hiểu chủ đề trong tranh và gợi ý hoạt động ngoài màn hình phù hợp với độ tuổi.
        </Text>
      </View>

      {/* Center Illustration: Girl & Dino hugging with sparkles */}
      <View style={styles.centerIllustration}>
        <OnboardingHeroIllustration height={220} />
      </View>

      {/* 3 Value Propositions matching Image 2 */}
      <View style={styles.valuePropsList}>
        <View style={[styles.valuePropCard, { backgroundColor: '#F0F9FF', borderColor: '#BAE6FD' }]}>
          <View style={[styles.valueIconOrb, { backgroundColor: '#38BDF8' }]}>
            <Ionicons name="sparkles" size={18} color={colors.white} />
          </View>
          <Text style={styles.valuePropText}>Khám phá chủ đề từ tranh vẽ và lời kể</Text>
        </View>

        <View style={[styles.valuePropCard, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}>
          <View style={[styles.valueIconOrb, { backgroundColor: '#22C55E' }]}>
            <Ionicons name="mic" size={18} color={colors.white} />
          </View>
          <Text style={styles.valuePropText}>Khuyến khích con kể chuyện bằng giọng nói</Text>
        </View>

        <View style={[styles.valuePropCard, { backgroundColor: '#FFF7ED', borderColor: '#FED7AA' }]}>
          <View style={[styles.valueIconOrb, { backgroundColor: '#FB923C' }]}>
            <Ionicons name="compass" size={18} color={colors.white} />
          </View>
          <Text style={styles.valuePropText}>Gợi ý hoạt động thực tế để con khám phá thế giới quanh mình</Text>
        </View>
      </View>

      {/* Pagination Dots matching Image 2 Screen 2 */}
      <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, marginVertical: 8 }}>
        <View style={{ width: 22, height: 6, borderRadius: 3, backgroundColor: '#3B82F6' }} />
        <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: '#CBD5E1' }} />
        <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: '#CBD5E1' }} />
      </View>

      {/* CTA Button matching Image 2 */}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Bắt đầu hành trình nào!"
          color="blue"
          size="lg"
          onPress={() => nav('dashboard')}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 3. HOME DASHBOARD (Image 2 - Screen 3)
// ==========================================
export const DashboardScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <View style={{ flex: 1, backgroundColor: '#F0F9FF' }}>
      <ScrollView contentContainerStyle={[styles.screenContainer, { backgroundColor: 'transparent' }]} showsVerticalScrollIndicator={false}>
        {/* Header Greeting */}
        <View style={styles.dashboardHeader}>
          <View style={{ flex: 1, minWidth: 0, paddingRight: 8 }}>
            <Text style={styles.greetingTitle}>Chào chị Lan! 👋</Text>
            <Text style={styles.greetingSub}>Cùng bé {selectedChild.name} biến những ý tưởng nhỏ thành câu chuyện lớn nhé!</Text>
          </View>
          <View style={styles.headerIcons}>
            <View style={styles.bellBtn}>
              <Ionicons name="notifications-outline" size={20} color={colors.textBody} />
              <View style={styles.notifDot} />
            </View>
            {/* Mom avatar crisp vector */}
            <View style={[styles.avatarBorder, { overflow: 'hidden' }]}>
              <MomAvatarImage size={28} />
            </View>
          </View>
        </View>

        {/* Keep this high-frequency Home action static to avoid a permanent GPU pulse loop. */}
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Tạo câu chuyện mới"
          activeOpacity={0.9}
          onPress={() => nav('profile')}
          style={[styles.createStoryCard, { shadowColor: '#F59E0B', shadowOpacity: 0.35, shadowRadius: 12, elevation: 8 }]}
        >
          <View style={styles.createIconOrb}>
            <Ionicons name="add" size={28} color={colors.yellowDeep} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.createStoryTitle}>+ Tạo câu chuyện mới</Text>
            <Text style={styles.createStorySub}>Từ một bức vẽ của bé {selectedChild.name}</Text>
          </View>
          <Text style={{ fontSize: 24 }}>✨</Text>
        </TouchableOpacity>

        {/* Recent Stories */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Câu chuyện mẫu</Text>
          <TouchableOpacity accessibilityRole="button" accessibilityLabel="Xem các câu chuyện mẫu" onPress={() => nav('story_preview')}>
            <Text style={styles.sectionLink}>Xem tất cả &gt;</Text>
          </TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.recentStoriesRow}>
          {/* Card 1: Rainbow Fish — BounceIn with delay 0 */}
          <BounceInView delay={0} style={styles.storyCard}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Mở câu chuyện mẫu Chú cá cầu vồng" activeOpacity={0.88} onPress={() => nav('story_preview')} style={{ flex: 1 }}>
              <RainbowFishArtwork height={85} />
              <Text numberOfLines={1} style={styles.storyCardTitle}>Chú cá cầu vồng và đại dương rực rỡ</Text>
              <Text style={styles.storyCardDate}>12 Tháng 4, 2025</Text>
            </TouchableOpacity>
          </BounceInView>

          {/* Card 2: Robot — BounceIn with delay 150ms */}
          <BounceInView delay={150} style={styles.storyCard}>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="Mở câu chuyện mẫu Robot khám phá thiên nhiên" activeOpacity={0.88} onPress={() => nav('story_preview')} style={{ flex: 1 }}>
              <StoryRobotArtwork height={85} />
              <Text numberOfLines={1} style={styles.storyCardTitle}>Robot khám phá thiên nhiên</Text>
              <Text style={styles.storyCardDate}>8 Tháng 4, 2025</Text>
            </TouchableOpacity>
          </BounceInView>
        </ScrollView>

        {/* Today's Recommended Activity */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Hoạt động mẫu hôm nay</Text>
        </View>

        <BounceInView delay={300}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Mở hoạt động mẫu Cùng trồng một hạt mầm"
            activeOpacity={0.9}
            onPress={() => nav('activity_recommend')}
            style={[styles.todayActivityCard, { borderWidth: 2, borderColor: '#FEF08A' }]}
          >
            {/* Animated sun icon */}
            <View style={[styles.todaySunOrb, { backgroundColor: '#FEF3C7', alignItems: 'center', justifyContent: 'center' }]}>
              <SunIconSvg size={32} />
            </View>
            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={styles.todayActTitle}>Cùng trồng một hạt mầm 🌱</Text>
              <Text style={styles.todayActSub}>Giúp bé khám phá thiên nhiên qua những điều nhỏ bé.</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
          </TouchableOpacity>
        </BounceInView>

        {/* Decorative bottom row of floating emojis */}
        <View style={{ height: 16 }} />
      </ScrollView>

      {/* Bottom Navigation Bar */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navItem}>
          <Ionicons name="home" size={22} color={colors.blueDeep} />
          <Text style={[styles.navText, { color: colors.blueDeep, fontWeight: '800' }]}>Trang chủ</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('story_preview')}>
          <Ionicons name="book-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Thư viện</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('activity_recommend')}>
          <Ionicons name="compass-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Khám phá</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => nav('profile')}>
          <Ionicons name="settings-outline" size={22} color={colors.textLight} />
          <Text style={styles.navText}>Hồ sơ</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ==========================================
// 4. CHILD PROFILE (Image 2 - Screen 4)
// ==========================================
export const ChildProfileScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    childrenList,
    selectedChild,
    setSelectedChild,
    selectedAgeMonths,
    setSelectedAgeMonths,
    selectedChildLearningProfile,
    updateSelectedChildLearningProfile,
    resetSelectedChildLearningProfile,
    classifySelectedChildPreferences,
    profileClassificationBusy,
    beginWorkflow,
    workflowBusy,
    sessionState,
  } = useAppContext();
  const nav = onNavigate || navigate;
  const [classificationError, setClassificationError] = useState<string | null>(null);
  const [classificationNotice, setClassificationNotice] = useState<string | null>(null);
  const [classifiedPreferenceRevision, setClassifiedPreferenceRevision] = useState<number | null>(null);
  const preferenceRevisionGateRef = useRef(new PreferenceRevisionGate());
  const selectedChildIdRef = useRef(selectedChild.id);
  selectedChildIdRef.current = selectedChild.id;
  const profileInputFrameSamplesRef = useRef<number[]>([]);
  const [profileInputFrameP95Ms, setProfileInputFrameP95Ms] = useState<number | null>(null);
  const profile = selectedChildLearningProfile;
  const interestDraftRef = useRef(profile?.interest_text || '');
  const avoidDraftRef = useRef(profile?.avoid_text || '');
  const preferenceDraftDirtyRef = useRef(false);
  const hasPreferenceTextRef = useRef(
    Boolean(profile?.interest_text.trim() || profile?.avoid_text.trim()),
  );
  const [hasPreferenceText, setHasPreferenceText] = useState(
    Boolean(profile?.interest_text.trim() || profile?.avoid_text.trim()),
  );
  const [preferenceDraftDirty, setPreferenceDraftDirty] = useState(false);
  const [preferenceInputGeneration, setPreferenceInputGeneration] = useState(0);
  useEffect(() => {
    interestDraftRef.current = profile?.interest_text || '';
    avoidDraftRef.current = profile?.avoid_text || '';
    preferenceDraftDirtyRef.current = false;
    const hasText = Boolean(profile?.interest_text.trim() || profile?.avoid_text.trim());
    hasPreferenceTextRef.current = hasText;
    setHasPreferenceText(hasText);
    setPreferenceDraftDirty(false);
    setClassificationError(null);
    setClassificationNotice(null);
    setClassifiedPreferenceRevision(null);
    preferenceRevisionGateRef.current.reset();
    profileInputFrameSamplesRef.current = [];
    setProfileInputFrameP95Ms(null);
  }, [selectedChild.id]);
  const markPreferenceDraftDirty = () => {
    if (preferenceDraftDirtyRef.current) return;
    preferenceDraftDirtyRef.current = true;
    setPreferenceDraftDirty(true);
  };
  const updateInterestDraft = (value: string) => {
    const boundedValue = value.slice(0, 240);
    if (boundedValue !== interestDraftRef.current) {
      preferenceRevisionGateRef.current.advance();
      if (classifiedPreferenceRevision !== null) {
        setClassifiedPreferenceRevision(null);
      }
      if (classificationNotice !== null) setClassificationNotice(null);
    }
    interestDraftRef.current = boundedValue;
    if (classificationError !== null) setClassificationError(null);
    markPreferenceDraftDirty();
    const hasText = Boolean(boundedValue.trim() || avoidDraftRef.current.trim());
    if (hasPreferenceTextRef.current !== hasText) {
      hasPreferenceTextRef.current = hasText;
      setHasPreferenceText(hasText);
    }
  };
  const updateAvoidDraft = (value: string) => {
    const boundedValue = value.slice(0, 240);
    if (boundedValue !== avoidDraftRef.current) {
      preferenceRevisionGateRef.current.advance();
      if (classifiedPreferenceRevision !== null) {
        setClassifiedPreferenceRevision(null);
      }
      if (classificationNotice !== null) setClassificationNotice(null);
    }
    avoidDraftRef.current = boundedValue;
    if (classificationError !== null) setClassificationError(null);
    markPreferenceDraftDirty();
    const hasText = Boolean(interestDraftRef.current.trim() || boundedValue.trim());
    if (hasPreferenceTextRef.current !== hasText) {
      hasPreferenceTextRef.current = hasText;
      setHasPreferenceText(hasText);
    }
  };
  const handleProfileInputChange = (updateDraft: (value: string) => void, value: string) => {
    if (!__DEV__) {
      updateDraft(value);
      return;
    }
    const startedAt = performance.now();
    updateDraft(value);
    requestAnimationFrame(() => {
      const elapsed = Math.max(0, performance.now() - startedAt);
      const samples = [...profileInputFrameSamplesRef.current, elapsed];
      if (samples.length < PROFILE_INPUT_METRIC_SAMPLE_COUNT) {
        profileInputFrameSamplesRef.current = samples;
        return;
      }
      const ordered = [...samples].sort((left, right) => left - right);
      const p95Index = Math.ceil(0.95 * ordered.length) - 1;
      const p95Ms = Math.round(ordered[p95Index] * 100) / 100;
      console.log(
        `FEAT033_PROFILE_INPUT_P95 samples=${ordered.length} event_to_next_frame_ms=${p95Ms.toFixed(2)}`,
      );
      profileInputFrameSamplesRef.current = [];
      setProfileInputFrameP95Ms(p95Ms);
    });
  };
  const commitPreferenceDrafts = () => {
    if (!preferenceDraftDirtyRef.current) return;
    updateSelectedChildLearningProfile({
      interest_text: interestDraftRef.current,
      avoid_text: avoidDraftRef.current,
      proposed_interest_tags: [],
      proposed_avoid_tags: [],
      interests: [],
      dislikes: [],
      preference_tags_confirmed: false,
    });
    preferenceDraftDirtyRef.current = false;
    setPreferenceDraftDirty(false);
  };
  const profileEditable = sessionState === 'NOT_STARTED' || sessionState === 'FEEDBACK_RECORDED';
  const {years: childAgeYears, months: childAgeExtraMonths} = splitChildAgeMonths(selectedAgeMonths);
  const isUnderThree = selectedAgeMonths < 36;
  const adjustChildAgeYears = (delta: number) => {
    setSelectedAgeMonths(adjustChildAgeByYears(selectedAgeMonths, delta));
  };
  const adjustChildAgeMonths = (delta: number) => {
    setSelectedAgeMonths(adjustChildAgeByMonths(selectedAgeMonths, delta));
  };
  const profileRequiresAdultParticipation = isUnderThree
    ? profile?.caregiver_participating !== true
    : profile?.adult_participating !== true;
  const classificationRevisionComplete = (
    classifiedPreferenceRevision === preferenceRevisionGateRef.current.current()
  );
  const classificationRetryLimitReached = (
    !classificationRevisionComplete && !preferenceRevisionGateRef.current.canClassify()
  );
  const togglePreferenceTag = (field: 'interests' | 'dislikes', conceptId: string) => {
    const current = profile?.[field] || [];
    const other: 'interests' | 'dislikes' = field === 'interests' ? 'dislikes' : 'interests';
    updateSelectedChildLearningProfile({
      [field]: current.includes(conceptId)
        ? current.filter((item) => item !== conceptId)
        : [...current, conceptId],
      [other]: (profile?.[other] || []).filter((item) => item !== conceptId),
      preference_tags_confirmed: false,
    });
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Hồ sơ của bé</Text>
        <View style={{ width: 48 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Bé là ai nhỉ?</Text>
        <Text style={styles.headingSubtitle}>
          Chọn hồ sơ hoặc tạo mới để cá nhân hóa trải nghiệm phù hợp với độ tuổi.
        </Text>
      </View>

      {/* Profiles Row */}
      <View style={styles.profilesRow}>
        {/* An */}
        <TouchableOpacity
          disabled={profileClassificationBusy}
          onPress={() => {
            const kid = childrenList.find((c) => c.name.toLowerCase() === 'an') || childrenList[0];
            setSelectedChild(kid);
          }}
          style={[styles.profileItem, selectedChild.name === 'An' && styles.profileItemSelected]}
        >
          <View style={[styles.avatarCircle, selectedChild.name === 'An' && styles.avatarSelected, { overflow: 'visible', position: 'relative' }]}>
            <ChildAvatarImage childName="An" size={54} />
            {selectedChild.name === 'An' && (
              <View style={{ position: 'absolute', bottom: -1, right: -1, width: 18, height: 18, borderRadius: 9, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: '#fff' }}>
                <Ionicons name="checkmark" size={11} color="#fff" />
              </View>
            )}
          </View>
          <Text style={styles.kidName}>An</Text>
          <Text style={styles.kidAge}>
            {selectedChild.id === childrenList[0].id
              ? formatChildAge(selectedAgeMonths)
              : formatChildAge(childrenList[0].age * 12)}
          </Text>
        </TouchableOpacity>

        {/* Bảo */}
        <TouchableOpacity
          disabled={profileClassificationBusy}
          onPress={() => {
            const kid = childrenList.find((c) => c.name.toLowerCase() === 'bảo') || childrenList[1];
            setSelectedChild(kid);
          }}
          style={[styles.profileItem, selectedChild.name === 'Bảo' && styles.profileItemSelected]}
        >
          <View style={[styles.avatarCircle, selectedChild.name === 'Bảo' && styles.avatarSelected, { overflow: 'hidden' }]}>
            <ChildAvatarImage childName="Bảo" size={54} />
          </View>
          <Text style={styles.kidName}>Bảo</Text>
          <Text style={styles.kidAge}>
            {selectedChild.id === childrenList[1].id
              ? formatChildAge(selectedAgeMonths)
              : formatChildAge(childrenList[1].age * 12)}
          </Text>
        </TouchableOpacity>

        {/* Add Child */}
        <TouchableOpacity style={styles.profileItem}>
          <View style={[styles.avatarCircle, styles.addKidCircle]}>
            <Ionicons name="add" size={28} color={colors.textLight} />
          </View>
          <Text style={[styles.kidName, { color: colors.textLight }]}>Thêm bé</Text>
          <Text style={styles.kidAge}> </Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.formSectionTitle}>Tuổi hiện tại của bé</Text>
      <Text style={{ color: '#64748B', fontSize: 11, lineHeight: 16, marginBottom: 8 }}>
        Nhập số năm và tháng bé đã đủ tuổi; không cần ngày sinh. Tuổi chỉ dùng trong phiên này.
      </Text>
      <View style={{ flexDirection: 'row', gap: 10 }}>
        {([
          { label: 'Năm', value: childAgeYears, decrement: () => adjustChildAgeYears(-1), increment: () => adjustChildAgeYears(1), min: childAgeYears <= 0, max: childAgeYears >= 12 },
          { label: 'Tháng', value: childAgeExtraMonths, decrement: () => adjustChildAgeMonths(-1), increment: () => adjustChildAgeMonths(1), min: selectedAgeMonths <= 0, max: selectedAgeMonths >= 155 },
        ] as const).map((item) => (
          <View key={item.label} style={{ flex: 1, minHeight: 74, padding: 10, borderWidth: 1, borderColor: '#CBD5E1', borderRadius: 14, backgroundColor: '#FFFFFF' }}>
            <Text style={{ color: '#64748B', fontSize: 11, fontWeight: '700', textAlign: 'center' }}>{item.label}</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel={`Giảm ${item.label.toLowerCase()}`}
                accessibilityState={{ disabled: item.min }}
                disabled={item.min}
                onPress={item.decrement}
                style={{ width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: item.min ? '#F1F5F9' : '#DBEAFE' }}
              >
                <Ionicons name="remove" size={19} color={item.min ? '#94A3B8' : '#1D4ED8'} />
              </TouchableOpacity>
              <Text accessibilityLabel={`${item.value} ${item.label.toLowerCase()}`} style={{ color: '#172554', fontSize: 20, fontWeight: '900' }}>{item.value}</Text>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel={`Tăng ${item.label.toLowerCase()}`}
                accessibilityState={{ disabled: item.max }}
                disabled={item.max}
                onPress={item.increment}
                style={{ width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: item.max ? '#F1F5F9' : '#DBEAFE' }}
              >
                <Ionicons name="add" size={19} color={item.max ? '#94A3B8' : '#1D4ED8'} />
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </View>

      <View style={{ marginTop: 18, borderWidth: 1, borderColor: '#BFDBFE', borderRadius: 18, padding: 16, backgroundColor: '#F8FBFF' }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: '#172554' }}>Hồ sơ thử nghiệm cho bé</Text>
            <Text style={{ fontSize: 12, lineHeight: 17, color: '#64748B', marginTop: 4 }}>
              Chỉ giữ trong phiên ứng dụng hiện tại; chưa lưu lâu dài. AI chỉ chạy khi người lớn bấm nút gợi ý, không chạy lúc đang nhập và không dùng để huấn luyện.
            </Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Xóa hồ sơ thử nghiệm"
            onPress={() => {
              preferenceRevisionGateRef.current.reset();
              setClassifiedPreferenceRevision(null);
              setClassificationNotice(null);
              profileInputFrameSamplesRef.current = [];
              setProfileInputFrameP95Ms(null);
              interestDraftRef.current = '';
              avoidDraftRef.current = '';
              preferenceDraftDirtyRef.current = false;
              hasPreferenceTextRef.current = false;
              setHasPreferenceText(false);
              setPreferenceDraftDirty(false);
              setPreferenceInputGeneration((generation) => generation + 1);
              setClassificationError(null);
              resetSelectedChildLearningProfile();
            }}
            disabled={!profileEditable || !profile || profileClassificationBusy}
            style={{ padding: 8, opacity: profileEditable && profile ? 1 : 0.4 }}
          >
            <Text style={{ color: '#B91C1C', fontSize: 12, fontWeight: '800' }}>Xóa thử</Text>
          </TouchableOpacity>
        </View>

        {profile && (
          <Text style={{ color: '#64748B', fontSize: 11, lineHeight: 16, marginTop: 8 }}>
            Khai báo bởi {profile.profile_declared_by === 'CAREGIVER' ? 'cha mẹ/người chăm sóc' : 'Guide'} · cập nhật {new Date(profile.profile_recorded_at).toLocaleString('vi-VN')} · tự xóa khi đóng ứng dụng.
          </Text>
        )}

        {!profileEditable ? (
          <Text style={{ color: '#B45309', fontSize: 13, marginTop: 12 }}>
            Hồ sơ bị khóa trong lúc đang có hoạt động. Có thể chỉnh lại sau khi kết thúc phiên.
          </Text>
        ) : (
          <>
            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 16, marginBottom: 8 }}>
              {isUnderThree ? 'Trẻ dưới 3 tuổi cần caregiver ở bên' : 'Người lớn sẽ đồng hành trong hoạt động?'}
            </Text>
            <ChoiceChip
              label={isUnderThree
                ? 'Người chăm sóc sẽ ở bên và giám sát trực tiếp'
                : 'Có, tôi sẽ ở bên và hỗ trợ bé'}
              selected={isUnderThree
                ? profile?.caregiver_participating === true
                : profile?.adult_participating === true}
              onPress={() => {
                if (isUnderThree) {
                  const confirmed = profile?.caregiver_participating === true;
                  updateSelectedChildLearningProfile({
                    adult_participating: confirmed ? null : true,
                    caregiver_participating: confirmed ? null : true,
                  });
                  return;
                }
                updateSelectedChildLearningProfile({
                  adult_participating: profile?.adult_participating === true ? null : true,
                });
              }}
            />
            <Text style={{ color: '#64748B', fontSize: 11, marginTop: 5 }}>
              {isUnderThree
                ? 'Với trẻ 0–35 tháng, người chăm sóc phải giám sát trực tiếp. Mức yêu cầu riêng của từng hoạt động vẫn được giữ nguyên.'
                : 'Mỗi hoạt động sẽ nêu rõ mức giám sát tối thiểu; ứng dụng không hạ yêu cầu an toàn của hoạt động.'}
            </Text>

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 18, marginBottom: 6 }}>Sở thích tương đối ổn định</Text>
            <TextInput
              key={`${selectedChild.id}-${preferenceInputGeneration}-interest`}
              defaultValue={profile?.interest_text || ''}
              onChangeText={(value) => handleProfileInputChange(updateInterestDraft, value)}
              onBlur={commitPreferenceDrafts}
              editable={profileEditable && !profileClassificationBusy}
              maxLength={240}
              multiline
              placeholder="Ví dụ: thích tìm hiểu các loài chim và cách chúng bay"
              accessibilityLabel="Sở thích ổn định do người lớn khai báo"
              style={{ minHeight: 68, textAlignVertical: 'top', borderWidth: 1, borderColor: '#CBD5E1', borderRadius: 12, backgroundColor: '#FFFFFF', padding: 11, fontSize: 13 }}
            />
            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 12, marginBottom: 6 }}>Chủ đề muốn tránh</Text>
            <TextInput
              key={`${selectedChild.id}-${preferenceInputGeneration}-avoid`}
              defaultValue={profile?.avoid_text || ''}
              onChangeText={(value) => handleProfileInputChange(updateAvoidDraft, value)}
              onBlur={commitPreferenceDrafts}
              editable={profileEditable && !profileClassificationBusy}
              maxLength={240}
              multiline
              placeholder="Không bắt buộc"
              accessibilityLabel="Chủ đề người lớn khai báo bé muốn tránh"
              style={{ minHeight: 58, textAlignVertical: 'top', borderWidth: 1, borderColor: '#CBD5E1', borderRadius: 12, backgroundColor: '#FFFFFF', padding: 11, fontSize: 13 }}
            />
            <Text style={{ color: '#64748B', fontSize: 11, marginTop: 5 }}>Không nhập tên, thông tin sức khỏe hay dữ liệu nhạy cảm. Nội dung chỉ dùng trong phiên hiện tại; AI chỉ đề xuất tag theo danh mục đã duyệt.</Text>
            {__DEV__ && profileInputFrameP95Ms !== null && (
              <Text accessibilityLabel="Đo thử phản hồi nhập liệu trong bản phát triển" style={{ color: '#64748B', fontSize: 10, marginTop: 5 }}>
                Đo dev event → frame kế tiếp: p95 {profileInputFrameP95Ms} ms · 24 mẫu · không lưu nội dung
              </Text>
            )}
            <TouchableOpacity
              accessibilityRole="button"
              disabled={
                !profileEditable
                || profileClassificationBusy
                || !hasPreferenceText
                || classificationRevisionComplete
                || classificationRetryLimitReached
              }
              onPress={async () => {
                const revisionGate = preferenceRevisionGateRef.current;
                const submittedRevision = revisionGate.current();
                const submittedChildId = selectedChild.id;
                if (!revisionGate.beginAttempt(submittedRevision)) return;
                setClassificationError(null);
                setClassificationNotice(null);
                const interestText = interestDraftRef.current;
                const avoidText = avoidDraftRef.current;
                if (interestText.trim() || avoidText.trim()) {
                  updateSelectedChildLearningProfile({
                    interest_text: interestText,
                    avoid_text: avoidText,
                    proposed_interest_tags: [],
                    proposed_avoid_tags: [],
                    interests: [],
                    dislikes: [],
                    preference_tags_confirmed: false,
                  });
                  preferenceDraftDirtyRef.current = false;
                  setPreferenceDraftDirty(false);
                }
                try {
                  const result = await classifySelectedChildPreferences(interestText, avoidText);
                  if (!result) {
                    revisionGate.markFailed(submittedRevision);
                    return;
                  }
                  const acceptedPatch = acceptPreferenceClassification(
                    revisionGate,
                    submittedRevision,
                    selectedChildIdRef.current,
                    submittedChildId,
                    result,
                  );
                  if (!acceptedPatch) return;
                  updateSelectedChildLearningProfile(acceptedPatch);
                  setClassifiedPreferenceRevision(submittedRevision);
                  if (result.interest_unmapped || result.avoid_unmapped) {
                    setClassificationNotice('Một phần nội dung chưa khớp chủ đề trong danh mục; phần đó sẽ không được dùng để gợi ý hoạt động.');
                  } else if (result.interest_tags.length === 0 && result.avoid_tags.length === 0) {
                    setClassificationNotice('Chưa tìm thấy chủ đề phù hợp trong danh mục. Bạn có thể sửa nội dung hoặc tiếp tục mà không dùng tag.');
                  } else {
                    setClassificationNotice('Đã có gợi ý. Hãy xem lại tag và xác nhận trước khi dùng cho hoạt động.');
                  }
                } catch (error) {
                  revisionGate.markFailed(submittedRevision);
                  setClassificationError(error instanceof Error ? error.message : 'Chưa phân loại được. Bạn có thể sửa nội dung hoặc bỏ qua.');
                  if (!revisionGate.canClassify()) {
                    setClassificationNotice('Đã dùng lượt phân loại cho nội dung này. Hãy sửa nội dung nếu muốn tạo lượt mới.');
                  }
                }
              }}
              accessibilityState={{ disabled: profileClassificationBusy || classificationRevisionComplete || classificationRetryLimitReached }}
              style={{ alignSelf: 'flex-start', marginTop: 10, paddingHorizontal: 14, paddingVertical: 9, borderRadius: 18, backgroundColor: profileClassificationBusy || classificationRevisionComplete || classificationRetryLimitReached ? '#CBD5E1' : '#DBEAFE', opacity: classificationRevisionComplete || classificationRetryLimitReached ? 0.72 : 1 }}
            >
              <Text style={{ color: '#1D4ED8', fontSize: 12, fontWeight: '800' }}>{profileClassificationBusy ? 'AI đang phân loại…' : classificationRevisionComplete ? 'Đã phân loại · sửa nội dung để chạy lại' : classificationRetryLimitReached ? 'Đã hết lượt thử · sửa nội dung' : '✨ Gợi ý tag bằng AI'}</Text>
            </TouchableOpacity>
            {classificationError && <Text accessibilityRole="alert" style={{ color: '#B91C1C', fontSize: 12, marginTop: 7 }}>{classificationError}</Text>}
            {classificationNotice && <Text accessibilityRole="text" style={{ color: '#475569', fontSize: 12, lineHeight: 17, marginTop: 7 }}>{classificationNotice}</Text>}
            {!preferenceDraftDirty
              && (Boolean(profile?.proposed_interest_tags.length)
                || Boolean(profile?.proposed_avoid_tags.length)) && (
              <View style={{ marginTop: 12, padding: 12, borderRadius: 12, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#BFDBFE' }}>
                <Text style={{ color: '#1E3A8A', fontWeight: '800', fontSize: 12 }}>AI gợi ý — người lớn chọn/sửa trước khi áp dụng</Text>
                {profile?.proposed_interest_tags.length ? <>
                  <Text style={{ color: '#475569', fontSize: 11, marginTop: 9, marginBottom: 5 }}>Sở thích</Text>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
                    {profile.proposed_interest_tags.map((tag) => <ChoiceChip key={`interest-${tag.concept_id}`} label={`${tag.label_vi} · ${Math.round(tag.confidence * 100)}%`} selected={profile.interests.includes(tag.concept_id)} onPress={() => togglePreferenceTag('interests', tag.concept_id)} />)}
                  </View>
                </> : null}
                {profile?.proposed_avoid_tags.length ? <>
                  <Text style={{ color: '#475569', fontSize: 11, marginTop: 10, marginBottom: 5 }}>Muốn tránh</Text>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
                    {profile.proposed_avoid_tags.map((tag) => <ChoiceChip key={`avoid-${tag.concept_id}`} label={`${tag.label_vi} · ${Math.round(tag.confidence * 100)}%`} selected={profile.dislikes.includes(tag.concept_id)} onPress={() => togglePreferenceTag('dislikes', tag.concept_id)} />)}
                  </View>
                </> : null}
                {(profile?.preference_tags_confirmed) ? (
                  <Text style={{ color: '#15803D', fontSize: 11, marginTop: 9 }}>Tag đã được người lớn xác nhận.</Text>
                ) : (
                  <TouchableOpacity onPress={() => updateSelectedChildLearningProfile({ preference_tags_confirmed: true })} style={{ alignSelf: 'flex-start', marginTop: 10, paddingHorizontal: 13, paddingVertical: 8, borderRadius: 16, backgroundColor: '#DCFCE7' }}>
                    <Text style={{ color: '#166534', fontSize: 12, fontWeight: '800' }}>Xác nhận tag đã chọn</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}

            <Text style={{ color: '#334155', fontSize: 12, fontWeight: '800', marginTop: 16, marginBottom: 8 }}>Cách học người lớn đã chọn cho bé</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
              {PROFILE_SUPPORTS.map(([id, label]) => (
                <ChoiceChip key={id} label={label} selected={Boolean(profile?.learning_support_ids.includes(id))} onPress={() => {
                  const values = profile?.learning_support_ids || [];
                  updateSelectedChildLearningProfile({ learning_support_ids: values.includes(id) ? values.filter((value) => value !== id) : [...values, id] as ChildLearningProfileInput['learning_support_ids'] });
                }} />
              ))}
            </View>
            {profileRequiresAdultParticipation && <Text style={{ color: '#B45309', fontSize: 12, lineHeight: 18, marginTop: 14 }}>Người lớn cần xác nhận sẽ đồng hành trước khi bắt đầu.</Text>}
          </>
        )}
      </View>

      {/* CTA */}
      <View style={styles.actionBottom}>
        <Kid3DButton
          title="Tiếp tục"
          color="blue"
          size="lg"
          rightIcon={<CuteStarIconSvg size={28} />}
          onPress={() => {
            void beginWorkflow();
          }}
          disabled={!!workflowBusy || profileRequiresAdultParticipation || profileClassificationBusy}
        />
      </View>
    </ScrollView>
  );
};

// ==========================================
// 5. CAPTURE / UPLOAD (Image 2 - Screen 5)
// ==========================================
export const CaptureScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    selectedDrawing,
    pickDrawingImage,
    uploadDrawing,
    admission,
    narrationMode,
    setNarrationMode,
    narrationText,
    setNarrationText,
    selectedNarrationAudio,
    isRecording,
    isRecordingStarting,
    startRecording,
    stopRecording,
    cancelRecording,
    uploadNarration,
    workflowBusy,
    workflowNotice,
  } = useAppContext();
  const nav = onNavigate || navigate;

  const handlePickImage = async () => {
    await pickDrawingImage();
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 12 : 0}
    >
    <ScrollView
      contentContainerStyle={styles.screenContainer}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
    >
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Quay lại"
          onPress={() => { if (isRecording || isRecordingStarting) void cancelRecording().then(goBack); else goBack(); }}
          style={styles.backBtn}
        >
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Thêm bức vẽ của bé</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Chụp hoặc tải lên bức vẽ</Text>
        <Text style={styles.headingSubtitle}>
          Bức vẽ của bé {selectedChild.name} có thể là tranh trên giấy, sổ tay hay bất cứ đâu. Mọi nét vẽ đều đặc biệt!
        </Text>
      </View>

      {/* Drawing Preview Card with Cat drawing */}
      <View style={styles.drawingCardWrap}>
        {selectedDrawing ? (
          <Image source={{ uri: selectedDrawing.uri }} style={{ width: '100%', height: 180 }} resizeMode="contain" />
        ) : (
          <CatDrawingArtwork height={180} />
        )}
      </View>

      <View style={styles.actionGridRow}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={selectedDrawing ? 'Chọn ảnh khác' : 'Chọn ảnh'}
          activeOpacity={0.9}
          onPress={handlePickImage}
          style={[styles.halfBtn, { flex: 1, backgroundColor: colors.blue }]}
        >
          <Ionicons name="images" size={24} color={colors.white} />
          <Text style={styles.halfBtnText}>{selectedDrawing ? 'Chọn ảnh khác' : 'Chọn ảnh'}</Text>
        </TouchableOpacity>
      </View>

      <View style={{ marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#DBEAFE' }}>
        <Text style={{ fontSize: 15, fontWeight: '900', color: colors.textHeading }}>Lời kể (không bắt buộc)</Text>
        <Text style={{ fontSize: 12, color: colors.textSoft, lineHeight: 17, marginTop: 4 }}>
          Ảnh là bắt buộc. Bạn có thể kể bằng giọng nói, nhập chữ hoặc bỏ qua lời kể.
        </Text>
        <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
          {([
            ['none', 'Không thêm'],
            ['text', 'Nhập chữ'],
            ['audio', 'Ghi âm'],
          ] as const).map(([mode, label]) => (
            <TouchableOpacity
              key={mode}
              accessibilityRole="radio"
              accessibilityLabel={label}
              accessibilityState={{ selected: narrationMode === mode }}
              disabled={Boolean(workflowBusy) || isRecording || isRecordingStarting}
              onPress={() => setNarrationMode(mode)}
              style={{ flex: 1, minHeight: 48, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: narrationMode === mode ? colors.blue : '#FFFFFF', borderWidth: 1, borderColor: narrationMode === mode ? colors.blue : '#CBD5E1' }}
            >
              <Text style={{ fontSize: 11, fontWeight: '800', color: narrationMode === mode ? colors.white : colors.textBody }}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {narrationMode === 'text' && (
          <TextInput
            value={narrationText}
            onChangeText={setNarrationText}
            editable={!workflowBusy && !isRecording && !isRecordingStarting}
            placeholder="Ví dụ: Con mèo đang đi tìm hoa..."
            placeholderTextColor="#94A3B8"
            multiline
            maxLength={2000}
            style={{ minHeight: 86, marginTop: 10, padding: 12, borderRadius: 12, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#BFDBFE', color: colors.textBody, textAlignVertical: 'top', fontSize: 13 }}
          />
        )}
        {narrationMode === 'audio' && (
          <View style={{ marginTop: 10, alignItems: 'center' }}>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={isRecording ? 'Dừng ghi âm' : isRecordingStarting ? 'Đang mở micro' : 'Bắt đầu ghi âm'}
              accessibilityState={{ busy: isRecording || isRecordingStarting, disabled: isRecordingStarting }}
              disabled={isRecordingStarting}
              onPress={() => void (isRecording ? stopRecording() : startRecording())}
              style={{ minWidth: 180, minHeight: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: isRecording ? '#DC2626' : colors.greenDeep }}
            >
              <Text style={{ color: colors.white, fontWeight: '900' }}>
                {isRecording ? 'Dừng ghi âm' : isRecordingStarting ? 'Đang mở micro…' : 'Bắt đầu ghi âm'}
              </Text>
            </TouchableOpacity>
            <Text style={{ marginTop: 8, fontSize: 12, color: colors.textSoft }}>
              {selectedNarrationAudio ? `Đã có bản ghi (${Math.round((selectedNarrationAudio.durationMs || 0) / 1000)} giây)` : 'Có thể ghi tối đa 3 phút'}
            </Text>
          </View>
        )}
      </View>

      <Kid3DButton
        title={workflowBusy === 'Tải ảnh' ? 'Đang kiểm tra ảnh...' : workflowBusy === 'Tải lời kể' ? 'Đang lưu lời kể...' : 'Gửi ảnh & tiếp tục'}
        color="blue"
        size="lg"
        disabled={!selectedDrawing || !!workflowBusy || isRecording || isRecordingStarting || (narrationMode === 'text' && !narrationText.trim()) || (narrationMode === 'audio' && !selectedNarrationAudio)}
        onPress={async () => {
          const imageAlreadyAdmitted = admission?.decision === 'ADMITTED';
          if ((!imageAlreadyAdmitted && !(await uploadDrawing())) || !(await uploadNarration())) return;
          nav(narrationMode === 'none' ? 'ai_processing' : 'transcript_review');
        }}
      />

      {workflowNotice && <Text style={{ color: colors.greenDeep, textAlign: 'center', marginTop: 10 }}>{workflowNotice}</Text>}

      {/* Tips Box */}
      <View style={styles.tipsBox}>
        <Text style={styles.tipsHeading}>💡 Một số gợi ý:</Text>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Chọn ảnh rõ, đủ sáng và không quá 5 MB</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Chỉ dùng tranh vẽ, không dùng ảnh có khuôn mặt trẻ em</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="checkmark-circle" size={16} color={colors.greenDeep} />
          <Text style={styles.tipText}>Ảnh chỉ được dùng để tạo gợi ý trong phiên này</Text>
        </View>
      </View>
    </ScrollView>
    </KeyboardAvoidingView>
  );
};

// ==========================================
// 6. VOICE RECORDING (Image 2 - Screen 6)
// ==========================================
export const VoiceScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const {
    navigate,
    goBack,
    selectedChild,
    isRecording,
    isRecordingStarting,
    toggleRecording,
    voiceDuration,
    selectedNarrationAudio,
    cancelRecording,
    uploadNarration,
  } = useAppContext();
  const nav = onNavigate || navigate;

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleFinishVoice = async () => {
    if (isRecording || !selectedNarrationAudio) return;
    if (await uploadNarration()) nav('transcript_review');
  };

  return (
    <ScrollView contentContainerStyle={styles.screenContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Quay lại"
          onPress={() => { if (isRecording || isRecordingStarting) void cancelRecording().then(goBack); else goBack(); }}
          style={styles.backBtn}
        >
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.screenHeaderTitle}>Kể chuyện bằng giọng nói</Text>
        <View style={{ width: 30 }} />
      </View>

      <View style={styles.headingBox}>
        <Text style={styles.headingTitle}>Giờ hãy kể về bức vẽ của bé {selectedChild.name} nhé!</Text>
        <Text style={styles.headingSubtitle}>
          Bé muốn nhân vật của mình làm gì? Hãy kể bất cứ điều gì. Chúng tôi sẽ biến giọng nói thành một câu chuyện thật sống động!
        </Text>
      </View>

      {/* Girl Mascot with Mic matching Image 2 Screen 6 */}
      <View style={styles.centerIllustration}>
        <VoiceGirlMicIllustration height={160} />
      </View>

      {/* Waveform Card */}
      <View style={[styles.waveformCard, { backgroundColor: '#FFFFFF', borderColor: '#BAE6FD' }]}>
        <Image
          source={require('../../assets/images/voice_waveform.png')}
          style={{ width: '92%', height: 42, resizeMode: 'contain', marginVertical: 6 }}
        />
        <Text style={[styles.waveformTimer, isRecording && { color: '#EF4444' }]}>
          {isRecordingStarting ? 'Đang mở micro…' : `${isRecording ? 'Đang ghi âm...  ' : ''}${formatTime(voiceDuration)} / 03:00`}
        </Text>
      </View>

      {/* Recording Controls */}
      <View style={styles.recordControlsRow}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={isRecording ? 'Dừng ghi âm' : isRecordingStarting ? 'Đang mở micro' : selectedNarrationAudio ? 'Ghi lại lời kể' : 'Bắt đầu kể'}
          accessibilityState={{ busy: isRecording || isRecordingStarting, disabled: isRecordingStarting }}
          disabled={isRecordingStarting}
          onPress={toggleRecording}
          style={styles.mainRecordBtn}
        >
          <Ionicons name={isRecording ? 'stop' : 'mic'} size={28} color={colors.white} />
        </TouchableOpacity>

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Hủy ghi âm"
          onPress={() => void cancelRecording().then(goBack)}
          style={styles.auxRecordBtn}
        >
          <Ionicons name="close" size={20} color={colors.textLight} />
          <Text style={styles.auxRecordText}>Hủy</Text>
        </TouchableOpacity>
      </View>
      {isRecordingStarting && (
        <Text style={styles.recordingLabel}>Đang xin quyền và mở micro…</Text>
      )}
      {isRecording && (
        <Text style={[styles.recordingLabel, { color: '#EF4444', fontWeight: '700' }]}>
          Đang ghi âm... Chạm nút đỏ để dừng
        </Text>
      )}
      {!isRecording && !isRecordingStarting && !selectedNarrationAudio && (
        <Text style={styles.recordingLabel}>Chạm nút micro để bắt đầu kể</Text>
      )}
      {!isRecording && selectedNarrationAudio && (
        <View style={styles.actionBottom}>
          <Kid3DButton
            title="Dùng lời kể này"
            color="blue"
            size="lg"
            onPress={() => void handleFinishVoice()}
          />
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  loginScreen: {
    flex: 1,
    backgroundColor: '#FBF4E8',
  },
  loginBackground: {
    flex: 1,
  },
  loginBackgroundImage: {
    resizeMode: 'cover',
  },
  loginScroll: {
    flex: 1,
  },
  loginScreenContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 14,
    paddingBottom: 28,
    position: 'relative',
  },
  loginDoodles: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  loginDoodleSun: {
    position: 'absolute',
    top: 2,
    left: 0,
    width: 60,
    height: 64,
    opacity: 0.72,
  },
  loginDoodleCloud: {
    position: 'absolute',
    top: 152,
    left: -12,
    width: 78,
    height: 64,
    opacity: 0.48,
  },
  loginDoodleHeart: {
    position: 'absolute',
    top: 164,
    right: 8,
    width: 28,
    height: 34,
    opacity: 0.68,
  },
  loginDoodleStar: {
    position: 'absolute',
    top: 282,
    right: 8,
    width: 50,
    height: 34,
    opacity: 0.72,
  },
  loginDoodleLeavesLeft: {
    position: 'absolute',
    bottom: 6,
    left: -2,
    width: 44,
    height: 64,
    opacity: 0.58,
  },
  loginDoodleLeavesRight: {
    position: 'absolute',
    bottom: 4,
    right: -2,
    width: 46,
    height: 70,
    opacity: 0.58,
  },
  loginBrandHeader: {
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 0,
    zIndex: 2,
  },
  loginLogoWrap: {
    width: '100%',
    alignItems: 'center',
    position: 'relative',
  },
  loginLogoImage: {
    maxWidth: 280,
  },
  loginMascotStage: {
    height: 118,
    marginTop: -2,
    position: 'relative',
    zIndex: 1,
    alignItems: 'center',
  },
  loginMascotImage: {
    position: 'absolute',
    left: '50%',
    bottom: -30,
    width: 165,
    height: 161,
    marginLeft: -82.5,
    zIndex: 2,
  },
  loginCard: {
    width: '100%',
    borderRadius: 30,
    borderWidth: 1,
    borderColor: '#F0DCC0',
    backgroundColor: '#FFFDF7',
    paddingHorizontal: 20,
    paddingTop: 38,
    paddingBottom: 20,
    zIndex: 3,
    shadowColor: '#7A5B42',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.14,
    shadowRadius: 18,
    elevation: 5,
  },
  loginCardAccent: {
    position: 'absolute',
    width: 42,
    height: 4,
    borderRadius: 4,
    opacity: 0.68,
  },
  loginCardAccentYellow: {
    top: 16,
    left: 14,
    backgroundColor: '#F6C84C',
    transform: [{ rotate: '-22deg' }],
  },
  loginCardAccentPink: {
    top: 17,
    right: 14,
    backgroundColor: '#F5A7B8',
    transform: [{ rotate: '22deg' }],
  },
  loginCardAccentBlue: {
    bottom: 16,
    left: 14,
    backgroundColor: '#75B8E8',
    transform: [{ rotate: '24deg' }],
  },
  loginCardAccentGreen: {
    bottom: 16,
    right: 14,
    backgroundColor: '#8BCB8A',
    transform: [{ rotate: '-24deg' }],
  },
  loginTitle: {
    fontSize: 25,
    lineHeight: 32,
    fontWeight: '900',
    color: '#4A2A16',
    textAlign: 'center',
    marginBottom: 8,
  },
  loginSubtitle: {
    fontSize: 14,
    lineHeight: 21,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 21,
  },
  loginLabel: {
    fontSize: 14,
    fontWeight: '900',
    color: '#4A2A16',
    marginBottom: 7,
  },
  loginInputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 54,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: '#D8D9DD',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
    marginBottom: 16,
  },
  loginFieldIcon: {
    width: 22,
    height: 20,
    opacity: 0.9,
  },
  loginFieldIconFocused: {
    opacity: 1,
  },
  loginLockIcon: {
    width: 23,
    height: 25,
  },
  loginInputWrapFocused: {
    borderColor: '#6EA8FF',
    backgroundColor: '#FBFDFF',
  },
  loginInput: {
    flex: 1,
    minHeight: 52,
    paddingHorizontal: 10,
    paddingVertical: 0,
    color: '#1F2937',
    fontSize: 14,
  },
  loginPasswordToggle: {
    width: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loginEyeIcon: {
    width: 23,
    height: 20,
    opacity: 0.92,
  },
  loginPrimaryButton: {
    minHeight: 56,
    borderRadius: 18,
    backgroundColor: '#2684F4',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
    overflow: 'hidden',
    shadowColor: '#1D4ED8',
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.2,
    shadowRadius: 9,
    elevation: 4,
  },
  loginPrimaryButtonTexture: {
    ...StyleSheet.absoluteFillObject,
    opacity: 0.88,
    resizeMode: 'contain',
  },
  loginButtonPressed: {
    opacity: 0.88,
    transform: [{ scale: 0.985 }],
  },
  loginButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    zIndex: 1,
  },
  loginPrimaryText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '900',
  },
  loginDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginVertical: 16,
  },
  loginDividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#DCCFBF',
  },
  loginDividerText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#8A8F98',
  },
  loginGoogleButton: {
    minHeight: 54,
    borderRadius: 17,
    borderWidth: 1.4,
    borderColor: '#4D8FF4',
    backgroundColor: '#FFFDF8',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    overflow: 'hidden',
  },
  loginGoogleButtonTexture: {
    ...StyleSheet.absoluteFillObject,
    opacity: 0.32,
    resizeMode: 'contain',
  },
  loginGoogleText: {
    color: '#2563EB',
    fontSize: 15,
    fontWeight: '900',
  },
  illustratedLoginCanvas: {
    width: '100%',
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: '#FFF8E9',
  },
  illustratedLoginOverlay: {
    ...StyleSheet.absoluteFillObject,
  },
  illustratedFormStack: {
    position: 'absolute',
    zIndex: 2,
    overflow: 'visible',
  },
  illustratedTitle: {
    position: 'absolute',
    color: '#31180C',
    fontFamily: 'MaliBold',
    fontWeight: '700',
    textAlign: 'center',
    includeFontPadding: false,
  },
  illustratedLabel: {
    position: 'absolute',
    color: '#2F1A0F',
    fontFamily: 'MaliSemiBold',
    fontWeight: '600',
    includeFontPadding: false,
  },
  illustratedFlowLabel: {
    color: '#2F1A0F',
    fontFamily: 'MaliSemiBold',
    fontWeight: '600',
    includeFontPadding: false,
  },
  illustratedField: {
    position: 'relative',
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: '#CBD5E1',
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
    paddingHorizontal: 13,
  },
  illustratedFieldFocused: {
    borderColor: '#3B82F6',
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
  },
  illustratedFieldError: {
    borderColor: '#D45E4C',
    backgroundColor: 'rgba(255, 248, 246, 0.98)',
  },
  illustratedFieldIcon: {
    width: 22,
    height: 20,
    opacity: 0.95,
  },
  illustratedLockIcon: {
    width: 23,
    height: 25,
  },
  illustratedInput: {
    flex: 1,
    minWidth: 0,
    height: '100%',
    paddingHorizontal: 10,
    paddingVertical: 0,
    color: '#334155',
    fontFamily: 'ItimRegular',
    fontWeight: '400',
  },
  illustratedPasswordToggle: {
    width: 30,
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  illustratedEyeIcon: {
    width: 23,
    height: 20,
    opacity: 0.94,
  },
  illustratedPrimaryButton: {
    width: '100%',
    borderRadius: 22,
    backgroundColor: '#2E80ED',
    borderWidth: 1.2,
    borderColor: '#1D6DDA',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
    overflow: 'hidden',
    shadowColor: '#1D4ED8',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 2,
  },
  illustratedButtonText: {
    color: '#FFFFFF',
    fontFamily: 'MaliBold',
    fontWeight: '700',
  },
  illustratedFieldErrorText: {
    width: '100%',
    color: '#B74436',
    fontFamily: 'ItimRegular',
    fontWeight: '400',
    textAlign: 'left',
    includeFontPadding: false,
  },
  illustratedErrorSlot: {
    width: '100%',
    justifyContent: 'flex-start',
  },
  illustratedPasswordHeaderRow: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 2,
  },
  illustratedForgotLink: {
    color: '#2563EB',
    fontFamily: 'ItimRegular',
    fontWeight: '400',
    textDecorationLine: 'underline',
  },
  illustratedDivider: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 12,
    marginBottom: 8,
  },
  illustratedDividerCompact: {
    marginTop: 8,
    marginBottom: 8,
    gap: 8,
  },
  illustratedDividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#D9CBB9',
  },
  illustratedDividerText: {
    color: '#6B7280',
    fontFamily: 'ItimRegular',
    fontWeight: '400',
  },
  illustratedGoogleButton: {
    width: '100%',
    minHeight: 48,
    borderRadius: 18,
    borderWidth: 1.2,
    borderColor: '#C9D2E3',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 12,
  },
  illustratedGoogleButtonUnavailable: {
    opacity: 0.72,
  },
  illustratedGoogleText: {
    color: '#1D4ED8',
    fontFamily: 'MaliBold',
    fontWeight: '700',
  },
  illustratedRegistrationRow: {
    width: '100%',
    minHeight: 24,
    marginTop: 8,
    marginBottom: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    transform: [{ translateY: -6 }],
  },
  illustratedRegistrationRowCompact: {
    minHeight: 20,
    marginTop: 8,
    marginBottom: 2,
  },
  illustratedRegistrationCopy: {
    color: '#64748B',
    fontFamily: 'ItimRegular',
    fontWeight: '400',
  },
  illustratedRegistrationLink: {
    color: '#2563EB',
    fontFamily: 'MaliSemiBold',
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  illustratedAuthNotice: {
    width: '100%',
    color: '#A05A2C',
    fontFamily: 'ItimRegular',
    textAlign: 'center',
    includeFontPadding: false,
    marginBottom: 8,
  },
  authFlowOverlay: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 20,
    backgroundColor: 'rgba(49, 24, 12, 0.28)',
  },
  authFlowOverlayContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  authFlowCard: {
    width: '100%',
    maxWidth: 360,
    alignSelf: 'center',
    borderRadius: 28,
    borderWidth: 1.2,
    borderColor: '#E8C77A',
    backgroundColor: '#FFF8E9',
    paddingHorizontal: 22,
    paddingVertical: 22,
    shadowColor: '#5B3018',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.18,
    shadowRadius: 16,
    elevation: 6,
  },
  authFlowHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  authFlowTitle: {
    flex: 1,
    color: '#31180C',
    fontFamily: 'MaliBold',
    fontSize: 25,
    lineHeight: 31,
    textAlign: 'center',
  },
  authFlowClose: {
    position: 'absolute',
    right: 0,
    top: 0,
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8E8C9',
  },
  authFlowDescription: {
    marginTop: 8,
    marginBottom: 18,
    color: '#46566D',
    fontFamily: 'ItimRegular',
    fontSize: 15,
    lineHeight: 21,
    textAlign: 'center',
  },
  authFlowLabel: {
    marginBottom: 6,
    color: '#2F1A0F',
    fontFamily: 'MaliSemiBold',
    fontSize: 15,
    lineHeight: 19,
  },
  authFlowInputWrap: {
    minHeight: 50,
    marginBottom: 14,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: '#CBD5E1',
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
  },
  authFlowInput: {
    flex: 1,
    minWidth: 0,
    height: '100%',
    paddingHorizontal: 10,
    paddingVertical: 0,
    color: '#334155',
    fontFamily: 'ItimRegular',
    fontSize: 15,
  },
  authFlowPrimaryButton: {
    minHeight: 50,
    marginTop: 4,
    borderRadius: 20,
    backgroundColor: '#2E80ED',
    borderWidth: 1.2,
    borderColor: '#1D6DDA',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    shadowColor: '#1D4ED8',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 2,
  },
  authFlowPrimaryText: {
    color: '#FFFFFF',
    fontFamily: 'MaliBold',
    fontSize: 16,
  },
  authFlowNotice: {
    marginTop: 10,
    color: '#A05A2C',
    fontFamily: 'ItimRegular',
    fontSize: 13,
    lineHeight: 18,
    textAlign: 'center',
  },
  authFlowBackLink: {
    alignSelf: 'center',
    marginTop: 16,
    paddingVertical: 4,
  },
  authFlowBackText: {
    color: '#2563EB',
    fontFamily: 'MaliSemiBold',
    fontSize: 14,
    textDecorationLine: 'underline',
  },
  centerContainer: {
    flexGrow: 1,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  screenContainer: {
    padding: 16,
    paddingBottom: 24,
    width: '100%',
    alignItems: 'stretch',
  },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  brandTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: colors.blue,
  },
  screenHeaderTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textHeading,
  },
  skipBtn: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textLight,
  },
  backBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headingBox: {
    alignItems: 'center',
    marginVertical: 6,
    textAlign: 'center',
  },
  headingTitle: {
    fontSize: 17,
    fontWeight: '900',
    color: colors.textHeading,
    textAlign: 'center',
    marginBottom: 4,
  },
  headingSubtitle: {
    fontSize: 12,
    color: colors.textSoft,
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 8,
  },
  centerIllustration: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 10,
    position: 'relative',
  },
  valuePropsList: {
    gap: 8,
    marginVertical: 10,
  },
  valuePropCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: 10,
  },
  valueIconOrb: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  valuePropText: {
    flex: 1,
    fontSize: 12,
    fontWeight: '700',
    color: colors.textBody,
    lineHeight: 16,
  },
  actionBottom: {
    marginTop: 14,
    marginBottom: 6,
  },
  dashboardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  greetingTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: colors.textHeading,
  },
  greetingSub: {
    fontSize: 11,
    color: colors.textSoft,
    marginTop: 2,
    maxWidth: 240,
  },
  headerIcons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  bellBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  notifDot: {
    position: 'absolute',
    top: 6,
    right: 7,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.coral,
  },
  avatarBorder: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.blueSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.blue,
  },
  createStoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF08A',
    borderColor: '#FACC15',
    borderWidth: 1.5,
    borderRadius: radius.lg,
    padding: 14,
    marginBottom: 16,
    gap: 12,
    ...shadows.card,
  },
  createIconOrb: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  createStoryTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: colors.yellowDeep,
  },
  createStorySub: {
    fontSize: 11,
    fontWeight: '600',
    color: '#854D0E',
    marginTop: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    marginTop: 6,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '900',
    color: colors.textHeading,
  },
  sectionLink: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.blueDeep,
  },
  recentStoriesRow: {
    gap: 12,
    paddingBottom: 6,
  },
  storyCard: {
    width: 170,
    backgroundColor: colors.white,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 10,
    ...shadows.card,
  },
  robotStoryBox: {
    height: 85,
    borderRadius: radius.sm,
    backgroundColor: '#F0FDF4',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  robotStoryTag: {
    position: 'absolute',
    bottom: 4,
    fontSize: 9,
    fontWeight: '800',
    color: '#15803D',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
  },
  storyCardTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 6,
  },
  storyCardDate: {
    fontSize: 9,
    color: colors.textLight,
    marginTop: 2,
  },
  todayActivityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
    borderWidth: 1,
    borderRadius: radius.md,
    padding: 12,
    marginTop: 4,
    marginBottom: 10,
  },
  todaySunOrb: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  todayActTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#92400E',
  },
  todayActSub: {
    fontSize: 10,
    color: '#B45309',
    marginTop: 2,
  },
  bottomNav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.white,
    paddingVertical: 8,
    width: '100%',
  },
  navItem: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
  },
  navText: {
    fontSize: 10,
    color: colors.textLight,
    fontWeight: '600',
  },
  profilesRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginVertical: 12,
  },
  profileItem: {
    alignItems: 'center',
    padding: 6,
  },
  profileItemSelected: {
    transform: [{ scale: 1.05 }],
  },
  avatarCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.lineSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  avatarSelected: {
    borderColor: colors.blue,
    backgroundColor: colors.blueSoft,
    ...shadows.card,
  },
  addKidCircle: {
    borderStyle: 'dashed',
    borderColor: colors.line,
    borderWidth: 2,
    backgroundColor: colors.white,
  },
  kidName: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 6,
  },
  kidAge: {
    fontSize: 10,
    color: colors.textSoft,
  },
  formSectionTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
    marginTop: 8,
    marginBottom: 6,
  },
  ageList: {
    gap: 8,
    marginBottom: 10,
  },
  ageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 10,
  },
  ageCardSelected: {
    borderColor: colors.blue,
    backgroundColor: colors.blueSoft,
  },
  ageTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textHeading,
  },
  ageTitleSelected: {
    color: colors.blueDeep,
  },
  ageDesc: {
    fontSize: 10,
    color: colors.textSoft,
    marginTop: 2,
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1.5,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleSelected: {
    borderColor: colors.blueDeep,
  },
  radioInnerDot: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
    backgroundColor: colors.blueDeep,
  },
  drawingCardWrap: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 12,
    alignItems: 'center',
    marginVertical: 10,
    overflow: 'visible',
    ...shadows.card,
  },
  drawingBubble: {
    backgroundColor: '#FEF9C3',
    borderColor: '#FDE047',
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginBottom: 8,
  },
  drawingBubbleText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#854D0E',
  },
  actionGridRow: {
    flexDirection: 'row',
    gap: 10,
    marginVertical: 8,
  },
  halfBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: radius.md,
    gap: 6,
    ...shadows.card,
  },
  halfBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.white,
  },
  tipsBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 10,
    marginTop: 8,
    gap: 4,
  },
  tipsHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
    marginBottom: 2,
  },
  tipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tipText: {
    fontSize: 10,
    color: colors.textSoft,
  },
  bubbleVoiceWrapper: {
    backgroundColor: '#FEF08A',
    borderColor: '#FACC15',
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginBottom: 6,
    position: 'relative',
  },
  bubbleVoiceText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#854D0E',
  },
  bubblePointer: {
    position: 'absolute',
    bottom: -5,
    left: '50%',
    marginLeft: -5,
    width: 0,
    height: 0,
    borderLeftWidth: 5,
    borderRightWidth: 5,
    borderTopWidth: 5,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: '#FACC15',
  },
  waveformCard: {
    backgroundColor: '#F0F9FF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    padding: 12,
    alignItems: 'center',
    marginVertical: 10,
  },
  waveformBars: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 50,
    gap: 4,
  },
  waveBar: {
    width: 4,
    borderRadius: 2,
  },
  waveformTimer: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.blueDeep,
    marginTop: 8,
  },
  recordControlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginVertical: 8,
  },
  auxRecordBtn: {
    alignItems: 'center',
    gap: 2,
    minWidth: 54,
  },
  auxRecordText: {
    fontSize: 10,
    color: colors.textSoft,
    fontWeight: '600',
  },
  mainRecordBtn: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#EF4444',
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.card,
    borderWidth: 3,
    borderColor: '#FEE2E2',
  },
  recordInnerSquare: {
    width: 22,
    height: 22,
    borderRadius: 4,
    backgroundColor: colors.white,
  },
  recordingLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textLight,
    textAlign: 'center',
    marginTop: 4,
  },
  quoteCard: {
    backgroundColor: colors.white,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    marginVertical: 4,
    ...shadows.card,
  },
  quoteText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textBody,
  },
});
