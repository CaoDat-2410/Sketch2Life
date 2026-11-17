import { adminApiRequest, adminBe1Request, adminOrganizationId } from "./be1Client";

export interface Be1Organization {
  contract: "Be1OrganizationV1";
  organization_id: string;
  display_name: string;
}

export interface Be1ManagedProfile {
  child_id: string;
  class_id: string;
  display_name: string;
  age_months: number;
}

export interface Be1ConsentStatus {
  consent_id: string;
  child_id: string;
  purpose_ref: string;
  state: string;
  effective: boolean;
}

export interface ParentGroup {
  contract: "ParentGroupV1";
  parent_group_id: string;
  organization_id: string;
  display_name: string;
  state: "ACTIVE" | "ARCHIVED";
  created_at: string;
}

export interface ParentGroupPage {
  contract: "ParentGroupPageV1";
  items: ParentGroup[];
  next_cursor: string | null;
}

const organizationPath = () =>
  "/organizations/" + encodeURIComponent(adminOrganizationId());

const lessonLibraryOrganizationPath = () =>
  "/lesson-library/v1" + organizationPath();

const withSignal = (signal?: AbortSignal): RequestInit =>
  signal ? { signal } : {};

export const managerBusinessService = {
  organization: (signal?: AbortSignal) =>
    adminBe1Request<Be1Organization>(organizationPath(), withSignal(signal)),

  profiles: (classId: string, signal?: AbortSignal) =>
    adminBe1Request<{ contract: string; items: Be1ManagedProfile[] }>(
      organizationPath() + "/classes/" + encodeURIComponent(classId) + "/profiles",
      withSignal(signal),
    ),

  consents: (classId: string, signal?: AbortSignal) =>
    adminBe1Request<{ contract: string; items: Be1ConsentStatus[] }>(
      organizationPath() + "/classes/" + encodeURIComponent(classId) + "/consents",
      withSignal(signal),
    ),

  parentGroups: (cursor?: string, signal?: AbortSignal) => {
    const query = new URLSearchParams({ limit: "50" });
    if (cursor) query.set("cursor", cursor);
    return adminApiRequest<ParentGroupPage>(
      lessonLibraryOrganizationPath() + "/parent-groups?" + query.toString(),
      withSignal(signal),
    );
  },

  createParentGroup: (displayName: string, idempotencyKey: string) =>
    adminApiRequest<ParentGroup>(lessonLibraryOrganizationPath() + "/parent-groups", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        contract: "CreateParentGroupRequestV1",
        display_name: displayName,
      }),
    }),
};
