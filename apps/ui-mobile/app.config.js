const { readRootEnv } = require('./config/rootEnv');

module.exports = ({ config }) => {
  const rootEnv = readRootEnv(__dirname);
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
