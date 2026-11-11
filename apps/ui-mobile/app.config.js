const fs = require('node:fs');
const path = require('node:path');

function readRootEnv() {
  const envPath = path.resolve(__dirname, '../../.env');
  if (!fs.existsSync(envPath)) return {};
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
  return {
    ...config,
    extra: {
      ...config.extra,
      parentPublicConfig: {
        apiKey: process.env.VITE_FIREBASE_API_KEY || rootEnv.VITE_FIREBASE_API_KEY || '',
        authDomain: process.env.VITE_FIREBASE_AUTH_DOMAIN || rootEnv.VITE_FIREBASE_AUTH_DOMAIN || '',
        projectId: process.env.VITE_FIREBASE_PROJECT_ID || rootEnv.VITE_FIREBASE_PROJECT_ID || '',
        appId: process.env.VITE_FIREBASE_APP_ID || rootEnv.VITE_FIREBASE_APP_ID || '',
        apiBaseUrl: process.env.SKETCH2LIFE_MOBILE_API_BASE_URL || rootEnv.SKETCH2LIFE_MOBILE_API_BASE_URL || '',
        googleWebClientId: process.env.SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID || rootEnv.SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID || '',
        googleAndroidClientId: process.env.SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID || rootEnv.SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID || '',
      },
    },
  };
};
