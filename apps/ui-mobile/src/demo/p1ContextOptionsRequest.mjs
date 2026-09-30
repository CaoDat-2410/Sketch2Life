export function buildP1ContextOptionsRequest({
  ageMonths,
  childProfile,
  candidateActivityIds,
  supervisionConfirmedActivityIds,
}) {
  const tagsConfirmed = childProfile.preference_tags_confirmed === true;
  return {
    contract_name: 'P1ContextOptionsRequestV2',
    contract_version: '2.0',
    age_months: ageMonths,
    candidate_activity_ids: candidateActivityIds,
    child_profile: {
      contract_name: 'ChildLearningProfileContextV2',
      contract_version: '2.0',
      profile_declared_by: childProfile.profile_declared_by,
      profile_recorded_at: childProfile.profile_recorded_at,
      preference_tags_confirmed: tagsConfirmed,
      interests: tagsConfirmed ? childProfile.interests : [],
      dislikes: tagsConfirmed ? childProfile.dislikes : [],
      readiness_ids: childProfile.readiness_ids,
      available_material_option_ids: childProfile.available_material_option_ids,
      learning_support_ids: childProfile.learning_support_ids,
    },
    adult_participating: childProfile.adult_participating === true,
    caregiver_participating: childProfile.caregiver_participating === true,
    supervision_confirmed_activity_ids: supervisionConfirmedActivityIds,
  };
}
