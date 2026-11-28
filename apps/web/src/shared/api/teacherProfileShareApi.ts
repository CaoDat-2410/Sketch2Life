import { BackendApiError, createIdempotencyKey } from "./backendApi";
import { data, enc, request, write } from "./teacherHttp";

export type SharedProfileField = "DISPLAY_NAME" | "AGE_BAND" | "INTERESTS_SUMMARY";
export interface ParentShareLink {
  contract: "Be1ParentShareLinkV1";
  share_grant_id: string;
  child_id: string;
  state: "ACTIVE";
  granted_fields: SharedProfileField[];
  accepted_at: string;
  expires_at: string;
  revision: number;
}
export interface ParentSharedProfile {
  contract: "Be1ParentSharedProfileV1";
  share_grant_id: string;
  child_id: string;
  granted_fields: SharedProfileField[];
  expires_at: string;
  fields: {
    display_name?: string | null;
    age_band?: { band_ref: string; band_version: number } | null;
    interests_summary?: string | null;
  };
}

const record = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object" && !Array.isArray(value));
const string = (value: unknown): value is string => typeof value === "string";
const fieldSet = new Set<SharedProfileField>(["DISPLAY_NAME", "AGE_BAND", "INTERESTS_SUMMARY"]);
const validFields = (value: unknown): value is SharedProfileField[] => Array.isArray(value)
  && value.every((item): item is SharedProfileField => typeof item === "string" && fieldSet.has(item as SharedProfileField))
  && new Set(value).size === value.length;

export function isParentShareLink(value: unknown): value is ParentShareLink {
  return record(value) && value.contract === "Be1ParentShareLinkV1" && string(value.share_grant_id)
    && string(value.child_id) && value.state === "ACTIVE" && validFields(value.granted_fields)
    && string(value.accepted_at) && string(value.expires_at) && Number.isInteger(value.revision) && Number(value.revision) > 0;
}

export function isParentSharedProfile(value: unknown): value is ParentSharedProfile {
  if (!record(value) || value.contract !== "Be1ParentSharedProfileV1" || !string(value.share_grant_id)
    || !string(value.child_id) || !validFields(value.granted_fields) || !string(value.expires_at) || !record(value.fields)) return false;
  const fields = value.fields;
  if (Object.keys(fields).some((key) => !["display_name", "age_band", "interests_summary"].includes(key))) return false;
  if ("display_name" in fields && fields.display_name !== null && !string(fields.display_name)) return false;
  if ("interests_summary" in fields && fields.interests_summary !== null && !string(fields.interests_summary)) return false;
  if ("age_band" in fields && fields.age_band !== null && (!record(fields.age_band) || !string(fields.age_band.band_ref)
    || !Number.isInteger(fields.age_band.band_version) || Number(fields.age_band.band_version) < 1)) return false;
  const expected = new Set(value.granted_fields as SharedProfileField[]);
  const actual = new Set<string>();
  if ("display_name" in fields) actual.add("DISPLAY_NAME");
  if ("age_band" in fields) actual.add("AGE_BAND");
  if ("interests_summary" in fields) actual.add("INTERESTS_SUMMARY");
  return [...actual].every((field) => expected.has(field as SharedProfileField));
}

function classProfilePath(organizationId: string, classId: string, childId: string): string {
  return `/api/be1/v1/organizations/${enc(organizationId)}/classes/${enc(classId)}/profiles/${enc(childId)}`;
}

export const teacherProfileShareApi = {
  accept: async (organizationId: string, classId: string, childId: string, invitationCode: string, key = createIdempotencyKey()): Promise<ParentShareLink> => {
    if (!/^[A-Za-z0-9_-]{16,64}$/.test(invitationCode)) throw new BackendApiError("Mã chia sẻ không hợp lệ.", "INVALID_REQUEST", 400);
    const value = await write<unknown>(`${classProfilePath(organizationId, classId, childId)}/parent-share/accept`, "POST", key, { invitation_code: invitationCode });
    if (!isParentShareLink(value) || value.child_id !== childId) throw new BackendApiError("Dịch vụ trả về trạng thái chia sẻ không hợp lệ.", "INVALID_RESPONSE", 502);
    return value;
  },

  getSharedProfile: async (organizationId: string, classId: string, childId: string): Promise<ParentSharedProfile> => {
    const value = data(await request<unknown>(`${classProfilePath(organizationId, classId, childId)}/parent-share`));
    if (!isParentSharedProfile(value) || value.child_id !== childId) throw new BackendApiError("Dịch vụ trả về thông tin chia sẻ không hợp lệ.", "INVALID_RESPONSE", 502);
    return value;
  },
};
