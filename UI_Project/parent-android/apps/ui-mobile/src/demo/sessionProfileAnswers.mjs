export function resetSessionBoundProfileAnswers(profile) {
  return {
    ...profile,
    adult_participating: null,
    caregiver_participating: null,
    readiness_ids: null,
    available_material_option_ids: null,
  };
}
