import type {
  ParentActionIdentity,
  ParentApiPort,
  ProfileCreateInput,
  ProfileUpdateInput,
} from '../ports/ParentPorts';
import type {
  ParentProfileCreateV1,
  ParentProfilePatchV1,
  ParentProfileRecordV1,
  ParentProfileViewV1,
} from '../../domain/types';
import { ParentApplicationError } from '../ParentApplicationError';
import { CHILD_AGE_RANGE_MESSAGE, isSupportedChildAge } from '../../domain/profileRules';

export type ParentProfilePatchOutcomeV1 =
  | { status: 'UPDATED'; profile: ParentProfileViewV1 }
  | { status: 'STALE'; profile: ParentProfileRecordV1 };

export class ParentProfileUseCases {
  constructor(private readonly api: ParentApiPort) {}

  getConsentPolicy() { return this.api.getConsentPolicy(); }
  listProfiles() { return this.api.listProfiles(); }
  listPageV1(limit?: number, cursor?: string | null) { return this.api.listProfilesV1(limit, cursor); }
  getV1(profileId: string) { return this.api.getProfileV1(profileId); }
  createV1(input: ParentProfileCreateV1, actionIdentity: ParentActionIdentity) {
    this.assertValidProfile(input.age_months, input.display_name);
    return this.api.createProfileV1(input, actionIdentity);
  }
  async patchV1(profileId: string, input: ParentProfilePatchV1, actionIdentity: ParentActionIdentity): Promise<ParentProfilePatchOutcomeV1> {
    this.assertValidProfile(input.age_months, input.display_name);
    try {
      const profile = await this.api.patchProfileV1(profileId, input, actionIdentity);
      return { status: 'UPDATED', profile };
    } catch (error) {
      if (!(error instanceof ParentApplicationError) || error.code !== 'STALE_REVISION') throw error;
      try {
        const profile = await this.api.getProfileV1(profileId);
        return { status: 'STALE', profile };
      } catch {
        throw error;
      }
    }
  }
  requestDeletionV1(profileId: string, actionIdentity: ParentActionIdentity) {
    return this.api.requestProfileDeletionV1(profileId, actionIdentity);
  }
  create(input: ProfileCreateInput) {
    this.assertValidProfile(input.age_months, input.display_name);
    return this.api.createProfile(input);
  }
  revise(profileId: string, input: ProfileUpdateInput) {
    this.assertValidProfile(input.age_months, input.display_name);
    return this.api.updateProfile(profileId, input);
  }
  grantAuthorization(profileId: string, policyVersion: string) {
    return this.api.grantAuthorization(profileId, policyVersion);
  }
  revokeAuthorization(profileId: string) { return this.api.revokeAuthorization(profileId); }
  archive(profileId: string) { return this.api.archiveProfile(profileId); }

  private assertValidProfile(ageMonths: number, displayName: string): void {
    if (!isSupportedChildAge(ageMonths)) {
      throw new ParentApplicationError('PARENT_PROFILE_AGE_INVALID', CHILD_AGE_RANGE_MESSAGE);
    }
    if (!displayName.trim()) {
      throw new ParentApplicationError('PARENT_PROFILE_NAME_REQUIRED', 'Nhập tên gọi cho hồ sơ.');
    }
  }
}
