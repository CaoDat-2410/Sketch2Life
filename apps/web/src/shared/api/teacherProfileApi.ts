import { BackendApiError } from "./backendApi";
import { pageQuery } from "./cursorPages";
import { request, visibleAscii } from "./teacherHttp";

export interface Be1ProfileAgeBandV1 {
  band_version: number;
  band_code: "AGE_36_71" | "AGE_72_107" | "AGE_108_120";
}

export interface Be1ProfileRevisionV1 {
  contract: "Be1ProfileRevisionV1";
  child_id: string;
  profile_revision_id: string;
  revision_no: number;
  display_name: string;
  age_months: number;
  age_band: Be1ProfileAgeBandV1 | null;
  structured_interests: string[];
  revision_hash: string;
  created_at: string;
}

export interface Be1ProfileRevisionPageV1 {
  contract: "Be1ProfileRevisionPageV1";
  items: Be1ProfileRevisionV1[];
  next_cursor: string | null;
}

export interface Be1ProfileEditResultV1 {
  contract: "Be1ProfileEditResultV1";
  child_id: string;
  profile_revision_id: string;
  revision_no: number;
  revision_hash: string;
}

export interface Be1SupportNeedsV1 {
  contract: "Be1SupportNeedsV1";
  child_id: string;
  revision: number;
  category: string | null;
  note: string | null;
}

export interface Be1SupportNeedsWriteV1 {
  contract: "Be1SupportNeedsWriteV1";
  child_id: string;
  revision: number;
}

export interface ProfileEditRequestV1 {
  expected_revision: number;
  display_name?: string;
  age_months?: number;
  structured_interests?: string[];
}

export interface SupportNeedsPutRequestV1 {
  expected_revision: number;
  category: string | null;
  note: string | null;
}

const enc = encodeURIComponent;
const profilePrefix = (organizationId: string, classId: string, childId: string) =>
  `/api/be1/v1/organizations/${enc(organizationId)}/classes/${enc(classId)}/profiles/${enc(childId)}`;

function idempotencyHeaders(key: string): Record<string, string> {
  if (!visibleAscii.test(key)) {
    throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  }
  return { "Idempotency-Key": key };
}

function invalidRequest(message: string): BackendApiError {
  return new BackendApiError(message, "INVALID_REQUEST", 400);
}

function profileEditBody(input: ProfileEditRequestV1): ProfileEditRequestV1 {
  if (!Number.isInteger(input.expected_revision) || input.expected_revision < 1) {
    throw invalidRequest("Phiên bản hồ sơ không hợp lệ.");
  }
  const body: ProfileEditRequestV1 = { expected_revision: input.expected_revision };
  let changedFields = 0;
  for (const field of ["display_name", "age_months", "structured_interests"] as const) {
    if (!Object.prototype.hasOwnProperty.call(input, field)) continue;
    const value = input[field];
    if (value === null || value === undefined) throw invalidRequest("Thông tin hồ sơ không hợp lệ.");
    if (field === "display_name") body.display_name = value as string;
    if (field === "age_months") body.age_months = value as number;
    if (field === "structured_interests") body.structured_interests = value as string[];
    changedFields += 1;
  }
  if (changedFields === 0) throw invalidRequest("Hãy thay đổi ít nhất một trường của hồ sơ.");
  return body;
}

function supportNeedsBody(input: SupportNeedsPutRequestV1): SupportNeedsPutRequestV1 {
  if (
    !Number.isInteger(input.expected_revision)
    || input.expected_revision < 0
    || input.expected_revision > 2_147_483_647
    || !Object.prototype.hasOwnProperty.call(input, "category")
    || !Object.prototype.hasOwnProperty.call(input, "note")
    || (input.category !== null && typeof input.category !== "string")
    || (input.note !== null && typeof input.note !== "string")
  ) throw invalidRequest("Thông tin nhu cầu hỗ trợ không hợp lệ.");
  return {
    expected_revision: input.expected_revision,
    category: input.category,
    note: input.note,
  };
}

async function responseData<T>(path: string, init: RequestInit): Promise<T> {
  const result = await request<T>(path, init);
  if (!result.data) throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", 502);
  return result.data;
}

export const teacherProfileApi = {
  /** One demand-loaded page; the screen asks for the next page only after a user action. */
  listProfileRevisions: (
    organizationId: string,
    classId: string,
    childId: string,
    cursor?: string,
  ): Promise<Be1ProfileRevisionPageV1> => responseData(
    `${profilePrefix(organizationId, classId, childId)}/revisions${pageQuery({ limit: 100, cursor })}`,
    { method: "GET", cache: "no-store" },
  ),

  getProfileRevision: (
    organizationId: string,
    classId: string,
    childId: string,
    profileRevisionId: string,
  ): Promise<Be1ProfileRevisionV1> => responseData(
    `${profilePrefix(organizationId, classId, childId)}/revisions/${enc(profileRevisionId)}`,
    { method: "GET", cache: "no-store" },
  ),

  editProfile: async (
    organizationId: string,
    classId: string,
    childId: string,
    input: ProfileEditRequestV1,
    key: string,
  ): Promise<Be1ProfileEditResultV1> => responseData(
    profilePrefix(organizationId, classId, childId),
    {
      method: "PATCH",
      headers: idempotencyHeaders(key),
      body: JSON.stringify(profileEditBody(input)),
      cache: "no-store",
    },
  ),

  getSupportNeeds: (
    organizationId: string,
    classId: string,
    childId: string,
  ): Promise<Be1SupportNeedsV1> => responseData(
    `${profilePrefix(organizationId, classId, childId)}/support-needs`,
    { method: "GET", cache: "no-store" },
  ),

  putSupportNeeds: async (
    organizationId: string,
    classId: string,
    childId: string,
    input: SupportNeedsPutRequestV1,
    key: string,
  ): Promise<Be1SupportNeedsWriteV1> => responseData(
    `${profilePrefix(organizationId, classId, childId)}/support-needs`,
    {
      method: "PUT",
      headers: idempotencyHeaders(key),
      body: JSON.stringify(supportNeedsBody(input)),
      cache: "no-store",
    },
  ),
};
