export function buildP1ContextRequest({ sessionId, expectedSessionVersion, context }) {
  const underThree = typeof context.age_months === 'number' && context.age_months < 36;
  const usesContextualCandidates = context.contextual_candidate_flow === true;
  const {
    caregiver_participating: caregiverParticipating,
    contextual_candidate_flow: _contextualCandidateFlow,
    ...contextFields
  } = context;
  return {
    ...contextFields,
    contract_name: usesContextualCandidates
      ? 'P1ContextV3'
      : underThree ? 'P1ContextV2' : 'P1ContextV1',
    contract_version: usesContextualCandidates ? '3.0' : underThree ? '2.0' : '1.0',
    session_id: sessionId,
    expected_session_version: expectedSessionVersion,
    gate_a_confirmed: true,
    ...(usesContextualCandidates
      ? {candidate_selection_mode: 'CONTEXTUAL_SHORTLIST'}
      : {}),
    ...(underThree
      ? { caregiver_participating: caregiverParticipating === true }
      : {}),
  };
}
