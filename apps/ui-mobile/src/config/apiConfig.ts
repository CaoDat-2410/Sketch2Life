/**
 * API Configuration for Sketch2Life Mobile App
 * Leader can easily change API_BASE_URL to point to their backend server.
 */

export const API_CONFIG = {
  // Base URL for the backend API
  // When running locally on the same machine or via emulator/tunnel:
  // - Local dev machine: 'http://localhost:8000/api'
  // - Android Emulator: 'http://10.0.2.2:8000/api'
  // - LAN / Expo Go on phone: 'http://<YOUR_LOCAL_IP>:8000/api' (e.g. 'http://192.168.1.15:8000/api')
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api',

  // Master switch for Mock vs Real API:
  // Set to 'false' when the backend server is up and running!
  // Defaults to 'true' so the app works seamlessly out-of-the-box for UI review and testing.
  USE_MOCK_API: true,

  // Request timeout in milliseconds
  TIMEOUT_MS: 15000,

  // Common headers
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
};
