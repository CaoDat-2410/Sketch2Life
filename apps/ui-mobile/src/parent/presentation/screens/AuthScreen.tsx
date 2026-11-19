import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, ImageBackground, Keyboard, KeyboardAvoidingView, Platform, Pressable, StatusBar, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthButton, AuthField, AuthNotice, AuthTextButton, authTokens } from '../components/AuthVisuals';
import { GoogleSignInButton } from '../components/GoogleSignInButton';
import { safeParentIdentityErrorMessage } from '../navigation/workflowTypes';

type Props = {
  busy: boolean;
  error: string;
  googleAndroidClientId: string;
  googleWebClientId: string;
  onSignIn: (email: string, password: string) => Promise<void>;
  onSignUp: (email: string, password: string) => Promise<void>;
  onReset: (email: string) => Promise<void>;
  onGoogleSignIn: (idToken: string) => Promise<void>;
  onClearAuthError?: () => void;
};

type AuthMode = 'signin' | 'signup' | 'recovery';
type AuthFieldName = 'email' | 'password' | 'confirmPassword';
type AuthFieldErrors = Record<AuthFieldName, string>;

const emptyFieldErrors: AuthFieldErrors = { email: '', password: '', confirmPassword: '' };
const emptyTouchedFields: Record<AuthFieldName, boolean> = { email: false, password: false, confirmPassword: false };
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function AuthScreen({ busy, error, googleAndroidClientId, googleWebClientId, onSignIn, onSignUp, onReset, onGoogleSignIn, onClearAuthError }: Props): React.JSX.Element {
  const { width, height } = useWindowDimensions();
  const [mode, setMode] = useState<AuthMode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [confirmPasswordVisible, setConfirmPasswordVisible] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [feedbackTone, setFeedbackTone] = useState<'error' | 'info'>('info');
  const [fieldErrors, setFieldErrors] = useState<AuthFieldErrors>(emptyFieldErrors);
  const [touchedFields, setTouchedFields] = useState<Record<AuthFieldName, boolean>>(emptyTouchedFields);
  const [reduceMotion, setReduceMotion] = useState(false);
  const [keyboardEventVisible, setKeyboardEventVisible] = useState(false);
  const introOpacity = useRef(new Animated.Value(0)).current;
  const introY = useRef(new Animated.Value(18)).current;
  const unresizedViewport = useRef({ width, height });
  const isRecovery = mode === 'recovery';
  const isSignup = mode === 'signup';
  // Android can report an IME show event even when the emulator's IME has no visible area.
  // With adjustResize enabled, a real soft keyboard also reduces the app viewport.
  const keyboardVisible = Platform.OS === 'android'
    ? keyboardEventVisible && unresizedViewport.current.height - height > 80
    : keyboardEventVisible;
  const compact = keyboardVisible || height < 760;
  const contentWidth = Math.min(width * 0.9, 460);

  useEffect(() => {
    let mounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (mounted) setReduceMotion(enabled);
    });
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    return () => {
      mounted = false;
      subscription.remove();
    };
  }, []);

  useEffect(() => {
    const showSubscription = Keyboard.addListener('keyboardDidShow', (event) => {
      setKeyboardEventVisible(event.endCoordinates.height > 0);
    });
    const hideSubscription = Keyboard.addListener('keyboardDidHide', () => setKeyboardEventVisible(false));
    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  useEffect(() => {
    const viewport = unresizedViewport.current;
    if (width !== viewport.width || (!keyboardEventVisible && height >= viewport.height - 80)) {
      unresizedViewport.current = { width, height };
    }
  }, [width, height, keyboardEventVisible]);

  useEffect(() => {
    introOpacity.stopAnimation();
    introY.stopAnimation();
    if (reduceMotion) {
      introOpacity.setValue(1);
      introY.setValue(0);
      return;
    }
    introOpacity.setValue(0);
    introY.setValue(18);
    const animation = Animated.parallel([
      Animated.timing(introOpacity, { toValue: 1, duration: 360, useNativeDriver: true }),
      Animated.spring(introY, { toValue: 0, damping: 18, stiffness: 170, mass: 0.8, useNativeDriver: true }),
    ]);
    animation.start();
    return () => animation.stop();
  }, [introOpacity, introY, mode, reduceMotion]);

  function changeMode(nextMode: AuthMode): void {
    setFeedback('');
    setFeedbackTone('info');
    setFieldErrors(emptyFieldErrors);
    setTouchedFields(emptyTouchedFields);
    onClearAuthError?.();
    setPasswordVisible(false);
    setConfirmPasswordVisible(false);
    setConfirmPassword('');
    setMode(nextMode);
  }

  function emailError(value: string): string {
    const normalized = value.trim();
    if (!normalized) return 'Nhập email để tiếp tục.';
    return emailPattern.test(normalized) ? '' : 'Email chưa đúng định dạng.';
  }

  function passwordError(value: string): string {
    if (!value) return 'Nhập mật khẩu để tiếp tục.';
    return value.length >= 6 ? '' : 'Mật khẩu cần ít nhất 6 ký tự.';
  }

  function confirmPasswordError(value: string, passwordValue = password): string {
    if (!value) return 'Nhập lại mật khẩu để tiếp tục.';
    return value === passwordValue ? '' : 'Mật khẩu chưa khớp.';
  }

  function validateField(field: AuthFieldName): void {
    setTouchedFields((current) => ({ ...current, [field]: true }));
    setFieldErrors((current) => ({
      ...current,
      [field]: field === 'email'
        ? emailError(email)
        : field === 'password'
          ? passwordError(password)
          : confirmPasswordError(confirmPassword),
    }));
  }

  function validateForm(): boolean {
    const nextErrors: AuthFieldErrors = {
      email: emailError(email),
      password: isRecovery ? '' : passwordError(password),
      confirmPassword: isSignup ? confirmPasswordError(confirmPassword) : '',
    };
    setFieldErrors(nextErrors);
    setTouchedFields({
      email: true,
      password: !isRecovery,
      confirmPassword: isSignup,
    });
    return !Object.values(nextErrors).some(Boolean);
  }

  function handleEmailChange(value: string): void {
    setEmail(value);
    onClearAuthError?.();
    setFeedback('');
    if (touchedFields.email) setFieldErrors((current) => ({ ...current, email: emailError(value) }));
  }

  function handlePasswordChange(value: string): void {
    setPassword(value);
    onClearAuthError?.();
    setFeedback('');
    setFieldErrors((current) => ({
      ...current,
      password: touchedFields.password ? passwordError(value) : current.password,
      confirmPassword: touchedFields.confirmPassword ? confirmPasswordError(confirmPassword, value) : current.confirmPassword,
    }));
  }

  function handleConfirmPasswordChange(value: string): void {
    setConfirmPassword(value);
    onClearAuthError?.();
    setFeedback('');
    if (touchedFields.confirmPassword) setFieldErrors((current) => ({ ...current, confirmPassword: confirmPasswordError(value) }));
  }

  function submitAuthentication(): void {
    Keyboard.dismiss();
    onClearAuthError?.();
    setFeedback('');
    if (!validateForm()) return;
    if (__DEV__) console.info('parent_auth_submit_pressed');
    void (mode === 'signup' ? onSignUp(email, password) : onSignIn(email, password));
  }

  function submitRecovery(): void {
    Keyboard.dismiss();
    onClearAuthError?.();
    setFeedback('');
    if (!validateForm()) return;
    void onReset(email)
      .then(() => {
        setFeedbackTone('info');
        setFeedback('Nếu email hợp lệ, hướng dẫn sẽ được gửi đến bạn.');
      })
      .catch((cause: unknown) => {
        setFeedbackTone('error');
        setFeedback(safeParentIdentityErrorMessage(cause));
      });
  }

  const title = isRecovery ? 'Khôi phục mật khẩu' : mode === 'signup' ? 'Tạo tài khoản phụ huynh' : 'Đăng nhập phụ huynh';
  const subtitle = isRecovery ? 'Nhập email để nhận hướng dẫn.' : mode === 'signup' ? 'Lưu lại hành trình sáng tạo của bé.' : 'Tiếp tục quản lý hành trình của bé.';

  return (
    <ImageBackground
      source={require('../../../../assets/applied/login-cloud-adventure.png')}
      resizeMode="cover"
      imageStyle={styles.backgroundImage}
      style={styles.screen}
    >
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.keyboardView}>
          <View style={[styles.fixedContent, !isRecovery && !keyboardVisible && styles.fixedContentLoginLower, keyboardVisible && styles.fixedContentKeyboard, { maxWidth: contentWidth }]}>
            <Animated.View style={[styles.formCard, compact && styles.formCardCompact, keyboardVisible && styles.formCardKeyboard, { opacity: introOpacity, transform: [{ translateY: introY }] }] }>
              <View style={[styles.cardIntro, compact && styles.cardIntroCompact]}>
                <View style={styles.titleRow}>
                  <Text accessibilityRole="header" style={styles.title}>{title}</Text>
                </View>
                <Text style={styles.subtitle}>{subtitle}</Text>
              </View>

              {isRecovery ? (
                <View style={[styles.formStack, compact && styles.formStackCompact]}>
                  <AuthField
                    label="Email"
                    icon="mail-outline"
                    value={email}
                    onChangeText={handleEmailChange}
                    onBlur={() => validateField('email')}
                    error={fieldErrors.email}
                    placeholder="ten@email.com"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoComplete="email"
                    returnKeyType="done"
                  />
                  {error ? <AuthNotice text={error} tone="error" /> : null}
                  {feedback ? <AuthNotice text={feedback} tone={feedbackTone} /> : null}
                  <AuthButton label="Gửi hướng dẫn" busy={busy} disabled={busy} onPress={submitRecovery} icon="paper-plane-outline" />
                  <AuthTextButton label="Quay lại đăng nhập" disabled={busy} onPress={() => changeMode('signin')} />
                </View>
              ) : (
                <View style={[styles.formStack, compact && styles.formStackCompact]}>
                  <AuthField
                    label="Email"
                    icon="mail-outline"
                    value={email}
                    onChangeText={handleEmailChange}
                    onBlur={() => validateField('email')}
                    error={fieldErrors.email}
                    placeholder="ten@email.com"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoComplete="email"
                    returnKeyType="next"
                  />
                  <AuthField
                    label="Mật khẩu"
                    icon="lock-closed-outline"
                    value={password}
                    onChangeText={handlePasswordChange}
                    onBlur={() => validateField('password')}
                    error={fieldErrors.password}
                    placeholder="Tối thiểu 6 ký tự"
                    secureTextEntry={!passwordVisible}
                    autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                    returnKeyType="done"
                    right={
                      <Pressable
                        accessibilityRole="button"
                        accessibilityLabel={passwordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                        accessibilityState={{ selected: passwordVisible }}
                        hitSlop={10}
                        onPress={() => setPasswordVisible((visible) => !visible)}
                        style={styles.passwordToggle}
                      >
                        <Ionicons name={passwordVisible ? 'eye-off-outline' : 'eye-outline'} size={21} color={authTokens.muted} accessible={false} />
                      </Pressable>
                    }
                  />
                  {isSignup ? (
                    <AuthField
                      label="Nhập lại mật khẩu"
                      icon="lock-closed-outline"
                      value={confirmPassword}
                      onChangeText={handleConfirmPasswordChange}
                      onBlur={() => validateField('confirmPassword')}
                      error={fieldErrors.confirmPassword}
                      placeholder="Nhập lại mật khẩu"
                      secureTextEntry={!confirmPasswordVisible}
                      autoComplete="new-password"
                      returnKeyType="done"
                      right={
                        <Pressable
                          accessibilityRole="button"
                          accessibilityLabel={confirmPasswordVisible ? 'Ẩn xác nhận mật khẩu' : 'Hiện xác nhận mật khẩu'}
                          accessibilityState={{ selected: confirmPasswordVisible }}
                          hitSlop={10}
                          onPress={() => setConfirmPasswordVisible((visible) => !visible)}
                          style={styles.passwordToggle}
                        >
                          <Ionicons name={confirmPasswordVisible ? 'eye-off-outline' : 'eye-outline'} size={21} color={authTokens.muted} accessible={false} />
                        </Pressable>
                      }
                    />
                  ) : null}
                  {error ? <AuthNotice text={error} tone="error" /> : null}
                  {feedback ? <AuthNotice text={feedback} tone={feedbackTone} /> : null}
                  {mode === 'signin' ? (
                    <View style={styles.forgotRow}>
                      <AuthTextButton label="Quên mật khẩu?" disabled={busy} onPress={() => changeMode('recovery')} />
                    </View>
                  ) : null}
                  <AuthButton
                    label={mode === 'signin' ? 'Đăng nhập' : 'Tạo tài khoản'}
                    busy={busy}
                    disabled={busy}
                    onPress={submitAuthentication}
                    icon="arrow-forward"
                  />
                  {!keyboardVisible ? (
                    <>
                      <View style={styles.dividerRow}>
                        <View style={styles.dividerLine} />
                        <Text style={styles.dividerText}>hoặc</Text>
                        <View style={styles.dividerLine} />
                      </View>
                      <GoogleSignInButton
                        variant="auth"
                        busy={busy}
                        googleAndroidClientId={googleAndroidClientId}
                        googleWebClientId={googleWebClientId}
                        onIdToken={onGoogleSignIn}
                        onError={(message) => setFeedback(message)}
                      />
                    </>
                  ) : null}
                  <View style={styles.switchMode}>
                    <Text style={styles.switchPrompt}>{mode === 'signin' ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}</Text>
                    <AuthTextButton label={mode === 'signin' ? 'Tạo tài khoản' : 'Đăng nhập'} disabled={busy} onPress={() => changeMode(mode === 'signin' ? 'signup' : 'signin')} />
                  </View>
                </View>
              )}
            </Animated.View>
          </View>
        </KeyboardAvoidingView>
        {isRecovery ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Quay lại đăng nhập"
            accessibilityState={{ disabled: busy }}
            disabled={busy}
            hitSlop={8}
            onPress={() => changeMode('signin')}
            style={({ pressed }) => [styles.backButton, Platform.OS === 'android' && styles.backButtonAndroid, pressed && styles.backButtonPressed]}
          >
            <Ionicons name="arrow-back" size={20} color={authTokens.ink} accessible={false} />
          </Pressable>
        ) : null}
      </SafeAreaView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: authTokens.paper },
  backgroundImage: { width: '100%', height: '100%' },
  safeArea: { flex: 1 },
  keyboardView: { flex: 1 },
  fixedContent: { flex: 1, width: '100%', alignSelf: 'center', justifyContent: 'center', paddingHorizontal: 0 },
  fixedContentLoginLower: { transform: [{ translateY: 60 }] },
  fixedContentKeyboard: { justifyContent: 'flex-start', paddingTop: 12, paddingBottom: 8, gap: 8 },
  backButton: { position: 'absolute', left: 20, top: 8, zIndex: 3, width: 44, height: 44, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: authTokens.paper, borderWidth: 1, borderColor: authTokens.border },
  backButtonAndroid: { top: 8 },
  backButtonPressed: { opacity: 0.68, transform: [{ scale: 0.96 }] },
  formCard: { width: '100%', padding: 18, gap: 16, backgroundColor: '#FAF3EB', borderWidth: 1.5, borderColor: '#D8C5B4', borderRadius: 24, shadowColor: authTokens.ink, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.1, shadowRadius: 18, elevation: 4 },
  formCardCompact: { padding: 16, gap: 12, borderRadius: 20 },
  formCardKeyboard: { padding: 12, gap: 9 },
  cardIntro: { gap: 6, alignItems: 'center' },
  cardIntroCompact: { gap: 3 },
  titleRow: { width: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  title: { color: authTokens.plumDark, fontSize: 22, lineHeight: 28, fontWeight: '900', flex: 1, minWidth: 0, textAlign: 'center' },
  subtitle: { color: authTokens.body, fontSize: 13, lineHeight: 18, fontWeight: '600', flexShrink: 1, textAlign: 'center' },
  formStack: { gap: 11 },
  formStackCompact: { gap: 8 },
  passwordToggle: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', marginRight: -8 },
  forgotRow: { minHeight: 32, alignItems: 'flex-end', justifyContent: 'center', marginTop: -5, marginBottom: -2 },
  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginVertical: 2 },
  dividerLine: { flex: 1, height: 1, backgroundColor: authTokens.lavenderLine },
  dividerText: { color: authTokens.muted, fontSize: 12, lineHeight: 17, fontWeight: '800' },
  switchMode: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, flexWrap: 'wrap' },
  switchPrompt: { color: authTokens.body, fontSize: 13, lineHeight: 18, fontWeight: '600' },
});
