import { adminBe1Request, adminOrganizationId } from './be1Client'

export interface Be1Class {
  class_id: string
  display_name: string
  state: 'active' | 'inactive'
}

export interface AdminAssignment {
  role: 'school_admin' | 'teacher' | 'guide' | 'observer'
  class_id: string | null
}

export const classService = {
  currentAssignments: async () => {
    const organization = adminOrganizationId()
    return adminBe1Request<{ contract: 'Be1AdultAssignmentsV1'; assignments: AdminAssignment[] }>(
      `/organizations/${encodeURIComponent(organization)}/me`,
    )
  },
  listClasses: async () => {
    const organization = adminOrganizationId()
    const result = await adminBe1Request<{ items: Be1Class[] }>(
      `/organizations/${encodeURIComponent(organization)}/classes`,
    )
    return result.items
  },
  createClass: async (displayName: string) => {
    const organization = adminOrganizationId()
    return adminBe1Request<{ contract: 'Be1ClassV1'; class_id: string; display_name: string }>(
      `/organizations/${encodeURIComponent(organization)}/classes`,
      { method: 'POST', body: JSON.stringify({ display_name: displayName }) },
    )
  },
}
