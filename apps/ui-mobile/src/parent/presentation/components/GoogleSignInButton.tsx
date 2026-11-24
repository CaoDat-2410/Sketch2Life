import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { authTokens } from './AuthVisuals';
import { Notice, palette } from './ui';

WebBrowser.maybeCompleteAuthSession();

type Props = {
  variant?: 'default' | 'auth';
  busy: boolean;
  googleAndroidClientId: string;
  googleWebClientId: string;
  onIdToken: (idToken: string) => Promise<void>;
  onError: (message: string) => void;
};

export function GoogleSignInButton({ variant = 'default', busy, googleAndroidClientId, googleWebClientId, onIdToken, onError }: Props): React.JSX.Element {
  const configured = Boolean(googleAndroidClientId && googleWebClientId);
  if (!configured) {
    return (
      <View style={styles.unavailableGroup}>
        <GoogleActionButton variant={variant} busy={busy} disabled onPress={() => undefined} />
        <Notice text="Google chưa được cấu hình cho ứng dụng này. Bạn có thể dùng email để tiếp tục." tone="warning" />
      </View>
    );
  }

  return (
    <ConfiguredGoogleSignInButton
      busy={busy}
      googleAndroidClientId={googleAndroidClientId}
      googleWebClientId={googleWebClientId}
      onIdToken={onIdToken}
      onError={onError}
      variant={variant}
    />
  );
}

function ConfiguredGoogleSignInButton({ variant = 'default', busy, googleAndroidClientId, googleWebClientId, onIdToken, onError }: Props): React.JSX.Element {
  const handledResponse = useRef<string>('');
  const [request, response, promptAsync] = Google.useIdTokenAuthRequest({
    androidClientId: googleAndroidClientId,
    webClientId: googleWebClientId,
    selectAccount: true,
  });

  useEffect(() => {
    if (!response || response.type !== 'success') return;
    const idToken = response.params.id_token ?? response.authentication?.idToken ?? '';
    const fingerprint = `${response.type}:${idToken.slice(-12)}`;
    if (handledResponse.current === fingerprint) return;
    handledResponse.current = fingerprint;
    if (!idToken) {
      onError('Chưa thể xác thực bằng Google. Hãy thử lại hoặc dùng email.');
      return;
    }
    void onIdToken(idToken);
  }, [onError, onIdToken, response]);

  useEffect(() => {
    if (response?.type !== 'error') return;
    onError('Chưa thể hoàn tất đăng nhập bằng Google. Hãy thử lại hoặc dùng email.');
  }, [onError, response]);

  return <GoogleActionButton
    variant={variant}
    busy={busy}
    disabled={!request}
    onPress={() => { void promptAsync().catch(() => onError('Chưa thể mở đăng nhập Google. Hãy thử lại hoặc dùng email.')); }}
  />;
}

function GoogleActionButton({ variant = 'default', busy, disabled = false, onPress }: { variant?: 'default' | 'auth'; busy: boolean; disabled?: boolean; onPress: () => void }): React.JSX.Element {
  const [focused, setFocused] = useState(false);
  const isDisabled = disabled || busy;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Tiếp tục với Google"
      accessibilityState={{ disabled: isDisabled, busy }}
      disabled={isDisabled}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      android_ripple={{ color: variant === 'auth' ? '#5B358720' : '#342E2820' }}
      style={({ pressed }) => [variant === 'auth' ? styles.authButton : styles.button, isDisabled && styles.disabledButton, pressed && !isDisabled && styles.pressed, focused && styles.focusRing]}
    >
      {busy ? <ActivityIndicator color={palette.disabledText} /> : <>
        <Ionicons name="logo-google" size={18} color={variant === 'auth' ? authTokens.plumDark : palette.ink} accessible={false} />
        <Text style={[variant === 'auth' ? styles.authButtonText : styles.buttonText, isDisabled && styles.disabledLabel]}>Tiếp tục với Google</Text>
      </>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  unavailableGroup: { gap: 8 },
  button: { width: '100%', minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 12, paddingVertical: 9, borderWidth: 1.8, borderColor: palette.outline, borderTopLeftRadius: 14, borderTopRightRadius: 16, borderBottomRightRadius: 13, borderBottomLeftRadius: 15, backgroundColor: palette.white },
  authButton: { width: '100%', minHeight: 54, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, paddingHorizontal: 14, paddingVertical: 9, borderWidth: 1.5, borderColor: authTokens.lavenderLine, borderRadius: 18, backgroundColor: authTokens.white },
  buttonText: { color: palette.ink, fontSize: 13, lineHeight: 18, fontWeight: '800', textAlign: 'center', flexShrink: 1 },
  authButtonText: { color: authTokens.plumDark, fontSize: 14, lineHeight: 19, fontWeight: '900', textAlign: 'center', flexShrink: 1 },
  disabledButton: { backgroundColor: palette.disabledSurface },
  disabledLabel: { color: palette.disabledText },
  pressed: { opacity: 0.72, transform: [{ scale: 0.985 }] },
  focusRing: { borderColor: authTokens.plum, borderWidth: 2.5 },
});
