import type { ParentApiPort, ProfileCreateInput, ProfileUpdateInput } from '../ports/ParentPorts';
import { ParentApplicationError } from '../ParentApplicationError';
import { CHILD_AGE_RANGE_MESSAGE, isSupportedChildAge } from '../../domain/profileRules';

export class ParentProfileUseCases {
  constructor(private readonly api: ParentApiPort) {}

  getConsentPolicy() { return this.api.getConsentPolicy(); }
  listProfiles() { return this.api.listProfiles(); }
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
