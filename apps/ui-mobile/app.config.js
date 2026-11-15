const fs = require('node:fs');
const path = require('node:path');

function readRootEnv() {
  let directory = path.resolve(__dirname);
  let envPath = '';
  while (directory !== path.dirname(directory)) {
    const hasProjectMarkers = fs.existsSync(path.join(directory, '.git'))
      && fs.existsSync(path.join(directory, 'compose.yaml'));
    const candidate = path.join(directory, '.env');
    if (hasProjectMarkers && fs.existsSync(candidate)) {
      envPath = candidate;
      break;
    }
    directory = path.dirname(directory);
  }
  if (!envPath) return {};
  const values = {};
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (!match || match[1].startsWith('#')) continue;
    let value = match[2];
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

module.exports = ({ config }) => {
  const rootEnv = readRootEnv();
  const appEnvironment = process.env.SKETCH2LIFE_ENV || rootEnv.SKETCH2LIFE_ENV || 'local';
  const apiBaseUrl = process.env.SKETCH2LIFE_MOBILE_API_BASE_URL
    || rootEnv.SKETCH2LIFE_MOBILE_API_BASE_URL
    || '';
  const firebaseApiKey = process.env.VITE_FIREBASE_API_KEY || rootEnv.VITE_FIREBASE_API_KEY || '';
  const firebaseProjectId = process.env.VITE_FIREBASE_PROJECT_ID || rootEnv.VITE_FIREBASE_PROJECT_ID || '';
  const firebaseAppId = process.env.VITE_FIREBASE_APP_ID || rootEnv.VITE_FIREBASE_APP_ID || '';
  const authEmulatorUrl = process.env.VITE_FIREBASE_AUTH_EMULATOR_URL
    || rootEnv.VITE_FIREBASE_AUTH_EMULATOR_URL
    || (appEnvironment === 'local' ? 'http://localhost:9099' : '');
  if (apiBaseUrl) process.env.EXPO_PUBLIC_API_URL = apiBaseUrl;
  if (firebaseApiKey) process.env.EXPO_PUBLIC_FIREBASE_API_KEY = firebaseApiKey;
  if (firebaseProjectId) process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID = firebaseProjectId;
  if (firebaseAppId) process.env.EXPO_PUBLIC_FIREBASE_APP_ID = firebaseAppId;
  if (authEmulatorUrl) {
    process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL = authEmulatorUrl;
  }
  return {
    ...config,
    extra: {
      ...config.extra,
      parentPublicConfig: {
        apiKey: firebaseApiKey,
        authDomain: process.env.VITE_FIREBASE_AUTH_DOMAIN || rootEnv.VITE_FIREBASE_AUTH_DOMAIN || '',
        projectId: firebaseProjectId,
        appId: firebaseAppId,
        authEmulatorUrl,
        apiBaseUrl,
        googleWebClientId: process.env.SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID || rootEnv.SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID || '',
        googleAndroidClientId: process.env.SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID || rootEnv.SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID || '',
      },
    },
  };
};
