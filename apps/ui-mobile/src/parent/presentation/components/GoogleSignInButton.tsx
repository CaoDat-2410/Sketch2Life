import React, { useEffect, useRef } from 'react';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { Notice, PrimaryButton } from './ui';

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
      <>
        <PrimaryButton label="Tiếp tục với Google" busy={busy} disabled onPress={() => undefined} />
        <Notice text="Google Sign-In chưa cấu hình. Điền SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID và SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID trong .env gốc." tone="warning" />
      </>
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
      onError('Google chưa trả về ID token. Kiểm tra OAuth client và redirect URI.');
      return;
    }
    void onIdToken(idToken);
  }, [onError, onIdToken, response]);

  useEffect(() => {
    if (response?.type !== 'error') return;
    const message = response.params.error_description;
    onError(typeof message === 'string' ? message : 'Không đăng nhập được bằng Google.');
  }, [onError, response]);

  return (
    <>
      <PrimaryButton
        label="Tiếp tục với Google"
        busy={busy}
        disabled={!request}
        onPress={() => void promptAsync()}
      />
    </>
  );
}
