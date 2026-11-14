import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { Card, Field, Notice, PrimaryButton, SecondaryButton, palette } from '../components/ui';
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

export function AuthScreen({ busy, error, googleAndroidClientId, googleWebClientId, onSignIn, onSignUp, onReset, onGoogleSignIn }: Props): React.JSX.Element {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [feedback, setFeedback] = useState('');
  const [feedbackTone, setFeedbackTone] = useState<'success' | 'error'>('success');
  return (
    <View style={{ flex: 1, backgroundColor: palette.background, justifyContent: 'center', padding: 20 }}>
      <View style={{ width: '100%', maxWidth: 440, alignSelf: 'center', gap: 18 }}>
        <View style={{ gap: 8 }}>
          <Text style={{ fontSize: 16, color: palette.blue, fontWeight: '800', letterSpacing: 0.7 }}>SKETCH2LIFE</Text>
          <Text style={{ color: palette.ink, fontSize: 30, fontWeight: '800', lineHeight: 36 }}>Một bức vẽ,{ '\n' }một hành trình khám phá.</Text>
          <Text style={{ color: palette.muted, fontSize: 15, lineHeight: 22 }}>Dành cho người lớn cùng đồng hành với trẻ.</Text>
        </View>
        <Card>
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <SecondaryButton label="Đăng nhập" onPress={() => setMode('signin')} disabled={mode === 'signin'} />
            <SecondaryButton label="Tạo tài khoản" onPress={() => setMode('signup')} disabled={mode === 'signup'} />
          </View>
          <Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" />
          <Field label="Mật khẩu" value={password} onChangeText={setPassword} secureTextEntry autoComplete={mode === 'signin' ? 'current-password' : 'new-password'} />
          {error ? <Notice text={error} tone="error" /> : feedback ? <Notice text={feedback} tone={feedbackTone} /> : null}
          <PrimaryButton label={mode === 'signin' ? 'Đăng nhập' : 'Tạo tài khoản phụ huynh'} busy={busy} disabled={!email.trim() || password.length < 6} onPress={() => { if (__DEV__) console.info('parent_auth_submit_pressed'); void (mode === 'signin' ? onSignIn(email, password) : onSignUp(email, password)); }} />
          {mode === 'signin' ? <Text onPress={() => {
            setFeedback('');
            if (!email.trim()) { setFeedbackTone('error'); setFeedback('Nhập email để nhận liên kết đặt lại mật khẩu.'); return; }
            void onReset(email)
              .then(() => { setFeedbackTone('success'); setFeedback('Nếu email đã đăng ký, hướng dẫn đặt lại mật khẩu sẽ được gửi tới hộp thư.'); })
              .catch((cause: unknown) => { setFeedbackTone('error'); setFeedback(safeParentIdentityErrorMessage(cause)); });
          }} accessibilityRole="button" style={{ color: palette.blue, textAlign: 'center', fontWeight: '700', minHeight: 44, textAlignVertical: 'center', padding: 8 }}>Quên mật khẩu?</Text> : <Text style={{ color: palette.muted, fontSize: 12, lineHeight: 18 }}>Tài khoản được tạo trên Firebase Authentication và backend Sketch2Life.</Text>}
          <View style={{ height: 1, backgroundColor: palette.disabledSurface }} />
          <GoogleSignInButton busy={busy} googleAndroidClientId={googleAndroidClientId} googleWebClientId={googleWebClientId} onIdToken={onGoogleSignIn} onError={() => { setFeedbackTone('error'); setFeedback('Chưa thể đăng nhập bằng Google. Hãy thử lại hoặc dùng email.'); }} />
        </Card>
      </View>
    </View>
  );
}
