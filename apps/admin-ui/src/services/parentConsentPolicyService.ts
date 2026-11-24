import { adminApiRequest } from './be1Client'

export type ParentConsentPolicyState = 'DRAFT' | 'ACTIVE' | 'RETIRED'

export interface ParentConsentPolicy {
  policy_id: string
  policy_version: string
  purpose_code: string
  consent_text: string
  consent_text_sha256: string
  state: ParentConsentPolicyState
  created_by: string
  created_at: string
  activated_by: string | null
  activated_at: string | null
}

interface PolicyListEnvelope {
  request_id: string
  active_policy_id: string | null
  policies: ParentConsentPolicy[]
}

interface PolicyEnvelope {
  request_id: string
  policy: ParentConsentPolicy
}

const BASE_PATH = '/platform-admin/v1/parent-consent-policies'

export const parentConsentPolicyService = {
  list(): Promise<PolicyListEnvelope> {
    return adminApiRequest<PolicyListEnvelope>(BASE_PATH)
  },

  createDraft(input: { policy_version: string; consent_text: string }): Promise<PolicyEnvelope> {
    return adminApiRequest<PolicyEnvelope>(BASE_PATH, {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },

  activate(policyId: string): Promise<PolicyEnvelope> {
    return adminApiRequest<PolicyEnvelope>(`${BASE_PATH}/${encodeURIComponent(policyId)}/activate`, {
      method: 'POST',
    })
  },
}
