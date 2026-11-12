import { be1Request, organizationId } from './be1Client'

export interface ManagedProfile {
  child_id: string
  class_id: string
  display_name: string
  age_months: number
}

export const profileService = {
  listForClass: async (classId: string) => {
    const organization = organizationId()
    const result = await be1Request<{ items: ManagedProfile[] }>(
      `/organizations/${encodeURIComponent(organization)}/classes/${encodeURIComponent(classId)}/profiles`,
    )
    return result.items
  },
}
