export function buildP1ActivitySuggestionsRequest({ ageMonths, childProfile }) {
  const tagsConfirmed = childProfile.preference_tags_confirmed === true;
  return {
    contract_name: 'P1ActivitySuggestionsRequestV1',
    contract_version: '1.0',
    age_months: ageMonths,
    child_profile: {
      contract_name: 'ConfirmedChildPreferencesV1',
      contract_version: '1.0',
      profile_declared_by: childProfile.profile_declared_by,
      profile_recorded_at: childProfile.profile_recorded_at,
      preference_tags_confirmed: tagsConfirmed,
      interests: tagsConfirmed ? childProfile.interests : [],
      dislikes: tagsConfirmed ? childProfile.dislikes : [],
    },
    adult_participating: childProfile.adult_participating === true,
    caregiver_participating: childProfile.caregiver_participating === true,
  };
}
