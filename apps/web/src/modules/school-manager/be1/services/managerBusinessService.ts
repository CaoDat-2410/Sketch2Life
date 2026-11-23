import { CURSOR_PAGE_LIMIT, collectCursorPages, pageQuery } from "../../../../shared/api/cursorPages";
import { adminApiRequest, adminBe1Request, adminOrganizationId } from "./be1Client";

export interface Be1Organization {
  contract: "Be1OrganizationV1";
  organization_id: string;
  display_name: string;
}

/** T-7a (SRS l.2586): the School Manager reads a count of active profiles, never profile contents. */
export interface Be1ClassRosterSummary {
  contract: "Be1ClassRosterSummaryV1";
  class_id: string;
  active_profile_count: number;
}

/** T-7a: the Manager consent item carries no child reference and no purpose. */
export interface Be1ManagerConsentStatus {
  consent_id: string;
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

  /** A09 count summary; any other body (for example a Teacher list with names) is refused, never shown. */
  rosterSummary: async (classId: string, signal?: AbortSignal): Promise<Be1ClassRosterSummary> => {
    const body = await adminBe1Request<Partial<Be1ClassRosterSummary> & { contract?: string }>(
      organizationPath() + "/classes/" + encodeURIComponent(classId) + "/profiles",
      withSignal(signal),
    );
    const count = body.active_profile_count;
    if (body.contract !== "Be1ClassRosterSummaryV1" || typeof count !== "number" || !Number.isInteger(count) || count < 0) {
      throw new Error("BE1 trả roster không đúng contract tóm tắt cho School Manager.");
    }
    return { contract: "Be1ClassRosterSummaryV1", class_id: String(body.class_id ?? classId), active_profile_count: count };
  },

  /** A10, every page; only the Manager item fields are kept. */
  consents: async (classId: string, signal?: AbortSignal): Promise<Be1ManagerConsentStatus[]> => {
    const { items } = await collectCursorPages<Be1ManagerConsentStatus>((cursor) =>
      adminBe1Request<{ items: Be1ManagerConsentStatus[]; next_cursor: string | null }>(
        organizationPath() + "/classes/" + encodeURIComponent(classId) + "/consents" + pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor }),
        withSignal(signal),
      ),
    );
    return items.map((item) => ({ consent_id: item.consent_id, state: item.state, effective: item.effective === true }));
  },

  parentGroups: (cursor?: string, signal?: AbortSignal) => {
    // SRS 21.1: cursor paging with the server default page size (25); no limit is sent.
    const query = new URLSearchParams();
    if (cursor) query.set("cursor", cursor);
    const queryString = query.toString();
    return adminApiRequest<ParentGroupPage>(
      lessonLibraryOrganizationPath() + "/parent-groups" + (queryString ? "?" + queryString : ""),
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
