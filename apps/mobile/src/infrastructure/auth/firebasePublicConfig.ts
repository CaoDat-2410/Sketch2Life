declare const process: {
  env: Record<string, string | undefined>;
};

/** Public client settings are compiled from the single repository-root .env. */
export const firebasePublicConfig = Object.freeze({
  apiKey: process.env.VITE_FIREBASE_API_KEY ?? "",
  authDomain: process.env.VITE_FIREBASE_AUTH_DOMAIN ?? "",
  projectId: process.env.VITE_FIREBASE_PROJECT_ID ?? "",
  appId: process.env.VITE_FIREBASE_APP_ID ?? "",
  apiBaseUrl: process.env.SKETCH2LIFE_MOBILE_API_BASE_URL ?? "",
});
