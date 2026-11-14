import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton, TextButton, palette } from '../components/ui';
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
};

type AuthMode = 'signin' | 'signup' | 'recovery';

export function AuthScreen({ busy, error, googleAndroidClientId, googleWebClientId, onSignIn, onSignUp, onReset, onGoogleSignIn }: Props): React.JSX.Element {
  const [mode, setMode] = useState<AuthMode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [feedback, setFeedback] = useState('');
  const [feedbackTone, setFeedbackTone] = useState<'error' | 'info'>('info');
  const isRecovery = mode === 'recovery';

  function changeMode(nextMode: AuthMode): void {
    setFeedback('');
    setFeedbackTone('info');
    setMode(nextMode);
  }

  function submitAuthentication(): void {
    if (__DEV__) console.info('parent_auth_submit_pressed');
    void (mode === 'signup' ? onSignUp(email, password) : onSignIn(email, password));
  }

  function submitRecovery(): void {
    setFeedback('');
    void onReset(email)
      .then(() => {
        setFeedbackTone('info');
        setFeedback('Nếu địa chỉ hợp lệ, hướng dẫn sẽ được gửi. Màn hình không tiết lộ trạng thái đăng ký.');
      })
      .catch((cause: unknown) => {
        setFeedbackTone('error');
        setFeedback(safeParentIdentityErrorMessage(cause));
      });
  }

  return (
    <ScreenFrame
      title={isRecovery ? 'Khôi phục tài khoản' : mode === 'signup' ? 'Tạo tài khoản phụ huynh' : 'Chào mừng trở lại'}
      subtitle={isRecovery ? 'Nhận hướng dẫn đặt lại mật khẩu qua email.' : 'Dành cho người lớn cùng đồng hành với trẻ.'}
      step={isRecovery ? undefined : 'PHỤ HUYNH'}
      onBack={isRecovery ? () => changeMode('signin') : undefined}
      backDisabled={busy}
    >
      {isRecovery ? (
        <>
          <Card style={styles.recoveryCard}>
            <Text style={styles.eyebrow}>TÀI KHOẢN PHỤ HUYNH</Text>
            <Text style={styles.cardTitle}>Đặt lại mật khẩu</Text>
            <Text style={styles.helperText}>Nhập email đã dùng để đăng ký.</Text>
            <Field
              label="Email"
              value={email}
              onChangeText={setEmail}
              placeholder="ten@email.com"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
            {error ? <Notice text={error} tone="error" /> : null}
            <PrimaryButton label="Gửi hướng dẫn khôi phục" busy={busy} disabled={!email.trim()} onPress={submitRecovery} />
            <TextButton label="Quay lại đăng nhập" disabled={busy} onPress={() => changeMode('signin')} />
          </Card>
          <Notice
            text={feedback || 'Nếu địa chỉ hợp lệ, hướng dẫn sẽ được gửi. Màn hình không tiết lộ trạng thái đăng ký.'}
            tone={feedback ? feedbackTone : 'info'}
          />
        </>
      ) : (
        <>
          <Card style={styles.introCard}>
            <Text style={styles.eyebrow}>Sketch2Life · Phụ huynh</Text>
            <Text style={styles.cardTitle}>Một bức vẽ, một hành trình khám phá.</Text>
            <Text style={styles.helperText}>{mode === 'signup' ? 'Tạo tài khoản để tiếp tục với hồ sơ gia đình.' : 'Đăng nhập để tiếp tục với hồ sơ gia đình.'}</Text>
          </Card>
          <Card style={styles.formCard}>
            <Field
              label="Email"
              value={email}
              onChangeText={setEmail}
              placeholder="ten@email.com"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
            <Field
              label="Mật khẩu"
              value={password}
              onChangeText={setPassword}
              placeholder="Nhập mật khẩu"
              secureTextEntry
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
            />
            {error ? <Notice text={error} tone="error" /> : feedback ? <Notice text={feedback} tone={feedbackTone} /> : null}
            <PrimaryButton
              label={mode === 'signin' ? 'Đăng nhập' : 'Tạo tài khoản phụ huynh'}
              busy={busy}
              disabled={!email.trim() || password.length < 6}
              onPress={submitAuthentication}
            />
            {mode === 'signin' ? (
              <>
                <SecondaryButton label="Tạo tài khoản phụ huynh" disabled={busy} onPress={() => changeMode('signup')} />
                <View style={styles.recoveryLinks}>
                  <Text style={styles.linkPrompt}>Quên mật khẩu?</Text>
                  <TextButton label="Khôi phục tài khoản" disabled={busy} onPress={() => changeMode('recovery')} />
                </View>
              </>
            ) : (
              <TextButton label="Đăng nhập" disabled={busy} onPress={() => changeMode('signin')} />
            )}
            <View style={styles.divider} />
            <GoogleSignInButton
              busy={busy}
              googleAndroidClientId={googleAndroidClientId}
              googleWebClientId={googleWebClientId}
              onIdToken={onGoogleSignIn}
              onError={() => setFeedback('Chưa thể đăng nhập bằng Google. Hãy thử lại hoặc dùng email.')}
            />
          </Card>
          {mode === 'signin' ? <Notice text="Đăng nhập bằng tài khoản phụ huynh đã xác thực." tone="info" /> : null}
        </>
      )}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  introCard: { backgroundColor: palette.white, gap: 9 },
  formCard: { backgroundColor: palette.white, gap: 12 },
  recoveryCard: { backgroundColor: palette.white, gap: 11 },
  eyebrow: { color: palette.ink, fontSize: 10, lineHeight: 14, fontWeight: '900', letterSpacing: 0.5, flexShrink: 1 },
  cardTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flexShrink: 1 },
  helperText: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  recoveryLinks: { alignItems: 'center', gap: 0 },
  linkPrompt: { color: palette.muted, fontSize: 11, lineHeight: 15, textAlign: 'center', flexShrink: 1 },
  divider: { height: 1, backgroundColor: palette.disabledSurface },
});
