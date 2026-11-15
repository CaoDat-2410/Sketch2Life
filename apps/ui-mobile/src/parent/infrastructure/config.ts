import Constants from 'expo-constants';
import { Platform } from 'react-native';

type PublicConfig = {
  apiKey?: string;
  authDomain?: string;
  projectId?: string;
  appId?: string;
  authEmulatorUrl?: string;
  apiBaseUrl?: string;
  googleWebClientId?: string;
  googleAndroidClientId?: string;
};

const expoExtra = (Constants.expoConfig?.extra ?? {}) as { parentPublicConfig?: PublicConfig };
const publicConfig = expoExtra.parentPublicConfig ?? {};
const runtimeApiBaseUrl = process.env.EXPO_PUBLIC_API_URL?.trim() ?? '';
const rawApiBaseUrl = (runtimeApiBaseUrl || publicConfig.apiBaseUrl?.trim() || '').replace(/\/+$/, '');
const runtimeFirebaseApiKey = process.env.EXPO_PUBLIC_FIREBASE_API_KEY?.trim() ?? '';
const runtimeFirebaseProjectId = process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID?.trim() ?? '';
const runtimeFirebaseAppId = process.env.EXPO_PUBLIC_FIREBASE_APP_ID?.trim() ?? '';
const androidApiBaseUrl = Platform.OS === 'android'
  ? rawApiBaseUrl.replace(/^http:\/\/(localhost|127\.0\.0\.1)(?=[:/]|$)/i, 'http://10.0.2.2')
  : rawApiBaseUrl;
const runtimeAuthEmulatorUrl = process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL?.trim() ?? '';
const rawAuthEmulatorUrl = (runtimeAuthEmulatorUrl || publicConfig.authEmulatorUrl?.trim() || '').replace(/\/+$/, '');
const androidAuthEmulatorUrl = Platform.OS === 'android'
  ? rawAuthEmulatorUrl.replace(/^http:\/\/(localhost|127\.0\.0\.1)(?=[:/]|$)/i, 'http://10.0.2.2')
  : rawAuthEmulatorUrl;

function safeOrigin(value: string): string {
  return value.match(/^https?:\/\/[^/]+/i)?.[0] ?? 'unset';
}

if (__DEV__) {
  console.info('parent_runtime_config', {
    platform: Platform.OS,
    apiOrigin: safeOrigin(androidApiBaseUrl),
    authEmulatorOrigin: safeOrigin(androidAuthEmulatorUrl),
    authEmulatorConfigured: Boolean(androidAuthEmulatorUrl),
      firebaseProjectId: runtimeFirebaseProjectId || publicConfig.projectId || 'unset',
      firebaseApiKeyConfigured: Boolean(runtimeFirebaseApiKey || publicConfig.apiKey),
      firebaseAppIdConfigured: Boolean(runtimeFirebaseAppId || publicConfig.appId),
  });
}

export const parentConfig = Object.freeze({
  firebaseApiKey: runtimeFirebaseApiKey || publicConfig.apiKey?.trim() || '',
  firebaseAppId: runtimeFirebaseAppId || publicConfig.appId?.trim() || '',
  firebaseAuthEmulatorUrl: androidAuthEmulatorUrl,
  apiBaseUrl: androidApiBaseUrl,
  googleWebClientId: publicConfig.googleWebClientId?.trim() ?? '',
  googleAndroidClientId: publicConfig.googleAndroidClientId?.trim() ?? '',
});
