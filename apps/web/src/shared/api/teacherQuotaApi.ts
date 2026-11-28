import { BackendApiError } from "./backendApi";
import { data, enc, request } from "./teacherHttp";

export interface TeacherQuotaAllocation {
  allocation_id: string;
  teacher_ref: string;
  available_units: number;
  active: boolean;
  revision: number;
  updated_at: string | null;
}

export interface TeacherVideoQuota {
  allocation: TeacherQuotaAllocation | null;
  organization_quota_owner: "ORGANIZATION";
}

function invalidResponse(): BackendApiError {
  return new BackendApiError("Không đọc được số dư quota.", "INVALID_RESPONSE", 200);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function parseQuota(value: unknown): TeacherVideoQuota {
  if (!isRecord(value) || value.organization_quota_owner !== "ORGANIZATION") throw invalidResponse();
  if (value.allocation === null) return { allocation: null, organization_quota_owner: "ORGANIZATION" };
  if (!isRecord(value.allocation)) throw invalidResponse();
  const item = value.allocation;
  if (typeof item.allocation_id !== "string" || !item.allocation_id
    || typeof item.teacher_ref !== "string" || !item.teacher_ref
    || !Number.isInteger(item.available_units)
    || typeof item.active !== "boolean"
    || !Number.isInteger(item.revision)
    || !(item.updated_at === null || (typeof item.updated_at === "string" && Number.isFinite(Date.parse(item.updated_at))))) {
    throw invalidResponse();
  }
  return {
    allocation: {
      allocation_id: item.allocation_id,
      teacher_ref: item.teacher_ref,
      available_units: Number(item.available_units),
      active: item.active,
      revision: Number(item.revision),
      updated_at: item.updated_at as string | null,
    },
    organization_quota_owner: "ORGANIZATION",
  };
}

export const teacherQuotaApi = {
  getMyVideoQuota: async (organizationId: string): Promise<TeacherVideoQuota> => {
    if (!organizationId.trim()) throw new BackendApiError("Chưa cấu hình tổ chức.", "INVALID_REQUEST", 400);
    const result = await request<unknown>(`/api/be1/v1/organizations/${enc(organizationId)}/video-quota/me`);
    return parseQuota(data(result));
  },
};
