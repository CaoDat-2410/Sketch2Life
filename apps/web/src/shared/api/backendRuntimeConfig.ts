export interface BackendRuntimeConfig {
  apiBaseUrl?: string;
  organizationId?: string;
}

export function resolveBackendRuntimeConfig(
  env: Record<string, string | undefined>,
  injected: Partial<BackendRuntimeConfig> = {},
): BackendRuntimeConfig {
  return {
    apiBaseUrl: injected.apiBaseUrl || env.VITE_SKETCH2LIFE_API_BASE_URL || env.VITE_BE1_BASE_URL,
    organizationId: injected.organizationId || env.VITE_SKETCH2LIFE_ORGANIZATION_ID || env.VITE_BE1_ORGANIZATION_ID,
  };
}
