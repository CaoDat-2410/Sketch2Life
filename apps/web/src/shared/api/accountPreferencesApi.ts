import { BackendApiError, backendRequest, createIdempotencyKey } from "./backendApi";

export type AccountPreferences = {
  locale: "vi-VN" | "en-US";
  email_notifications: boolean;
  revision: number;
};

export type UpdateAccountPreferences = Pick<AccountPreferences, "locale" | "email_notifications"> & {
  expected_revision: number;
};

const PREFERENCES_PATH = "/api/platform-admin/v1/preferences";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parsePreferences(value: unknown): AccountPreferences {
  if (!isRecord(value)
    || (value.locale !== "vi-VN" && value.locale !== "en-US")
    || typeof value.email_notifications !== "boolean"
    || !Number.isInteger(value.revision)
    || (value.revision as number) < 0) {
    throw new BackendApiError("Dịch vụ trả về dữ liệu cài đặt không hợp lệ.", "INVALID_RESPONSE", 502);
  }
  return {
    locale: value.locale,
    email_notifications: value.email_notifications,
    revision: value.revision as number,
  };
}

export async function getPreferences(): Promise<AccountPreferences> {
  return parsePreferences(await backendRequest<unknown>(PREFERENCES_PATH));
}

export async function updatePreferences(input: UpdateAccountPreferences): Promise<AccountPreferences> {
  const result = await backendRequest<unknown>(PREFERENCES_PATH, {
    method: "PUT",
    headers: { "Idempotency-Key": createIdempotencyKey() },
    body: JSON.stringify(input),
  });
  return parsePreferences(result);
}
