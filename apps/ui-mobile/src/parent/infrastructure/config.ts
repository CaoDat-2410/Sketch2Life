import Constants from 'expo-constants';
import { Platform } from 'react-native';

type PublicConfig = {
  apiKey?: string;
  authDomain?: string;
  projectId?: string;
  appId?: string;
  apiBaseUrl?: string;
  googleWebClientId?: string;
  googleAndroidClientId?: string;
};

const expoExtra = (Constants.expoConfig?.extra ?? {}) as { parentPublicConfig?: PublicConfig };
const publicConfig = expoExtra.parentPublicConfig ?? {};
const runtimeApiBaseUrl = process.env.EXPO_PUBLIC_API_URL?.trim() ?? '';
const rawApiBaseUrl = (runtimeApiBaseUrl || publicConfig.apiBaseUrl?.trim() || '').replace(/\/+$/, '');
const androidApiBaseUrl = Platform.OS === 'android'
  ? rawApiBaseUrl.replace(/^http:\/\/(localhost|127\.0\.0\.1)(?=[:/]|$)/i, 'http://10.0.2.2')
  : rawApiBaseUrl;
const rawFirebaseAuthEmulatorUrl = process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL?.trim() ?? '';
const validFirebaseAuthEmulatorUrl = (() => {
  if (typeof __DEV__ === 'undefined' || !__DEV__ || !rawFirebaseAuthEmulatorUrl) return '';
  const match = /^http:\/\/(localhost|127\.0\.0\.1|10\.0\.2\.2):(\d+)\/?$/i.exec(rawFirebaseAuthEmulatorUrl);
  if (!match) return '';
  const port = Number(match[2]);
  if (!Number.isInteger(port) || port < 1 || port > 65535) return '';
  return `http://${match[1].toLowerCase()}:${port}`;
})();
const androidFirebaseAuthEmulatorUrl = Platform.OS === 'android'
  ? validFirebaseAuthEmulatorUrl.replace(/^http:\/\/(localhost|127\.0\.0\.1)(?=[:/]|$)/i, 'http://10.0.2.2')
  : validFirebaseAuthEmulatorUrl;

export const parentConfig = Object.freeze({
  firebaseApiKey: publicConfig.apiKey?.trim() ?? '',
  apiBaseUrl: androidApiBaseUrl,
  firebaseAuthEmulatorUrl: androidFirebaseAuthEmulatorUrl,
  googleWebClientId: publicConfig.googleWebClientId?.trim() ?? '',
  googleAndroidClientId: publicConfig.googleAndroidClientId?.trim() ?? '',
});
