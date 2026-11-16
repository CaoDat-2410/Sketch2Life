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

export const parentConfig = Object.freeze({
  firebaseApiKey: publicConfig.apiKey?.trim() ?? '',
  apiBaseUrl: androidApiBaseUrl,
  googleWebClientId: publicConfig.googleWebClientId?.trim() ?? '',
  googleAndroidClientId: publicConfig.googleAndroidClientId?.trim() ?? '',
});
