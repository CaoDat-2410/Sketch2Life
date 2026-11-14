import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { Notice, palette } from './ui';

WebBrowser.maybeCompleteAuthSession();

type Props = {
  busy: boolean;
  googleAndroidClientId: string;
  googleWebClientId: string;
  onIdToken: (idToken: string) => Promise<void>;
  onError: (message: string) => void;
};

export function GoogleSignInButton({ busy, googleAndroidClientId, googleWebClientId, onIdToken, onError }: Props): React.JSX.Element {
  const configured = Boolean(googleAndroidClientId && googleWebClientId);
  if (!configured) {
    return (
      <View style={styles.unavailableGroup}>
        <GoogleActionButton busy={busy} disabled onPress={() => undefined} />
        <Notice text="Đăng nhập bằng Google hiện chưa khả dụng. Bạn có thể dùng email để tiếp tục." tone="warning" />
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
    />
  );
}

function ConfiguredGoogleSignInButton({ busy, googleAndroidClientId, googleWebClientId, onIdToken, onError }: Props): React.JSX.Element {
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

  return <GoogleActionButton busy={busy} disabled={!request} onPress={() => void promptAsync()} />;
}

function GoogleActionButton({ busy, disabled = false, onPress }: { busy: boolean; disabled?: boolean; onPress: () => void }): React.JSX.Element {
  const [focused, setFocused] = useState(false);
  const isDisabled = disabled || busy;
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel="Tiếp tục với Google"
      accessibilityState={{ disabled: isDisabled, busy }}
      disabled={isDisabled}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      activeOpacity={0.86}
      style={[styles.button, isDisabled && styles.disabledButton, focused && styles.focusRing]}
    >
      {busy ? <ActivityIndicator color={palette.disabledText} /> : <>
        <Ionicons name="logo-google" size={18} color={palette.ink} accessible={false} />
        <Text style={[styles.buttonText, isDisabled && styles.disabledLabel]}>Tiếp tục với Google</Text>
      </>}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  unavailableGroup: { gap: 8 },
  button: { width: '100%', minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 12, paddingVertical: 9, borderWidth: 1.8, borderColor: palette.outline, borderTopLeftRadius: 14, borderTopRightRadius: 16, borderBottomRightRadius: 13, borderBottomLeftRadius: 15, backgroundColor: palette.white },
  buttonText: { color: palette.ink, fontSize: 13, lineHeight: 18, fontWeight: '800', textAlign: 'center', flexShrink: 1 },
  disabledButton: { backgroundColor: palette.disabledSurface },
  disabledLabel: { color: palette.disabledText },
  focusRing: { borderColor: palette.focus, borderWidth: 3 },
});
