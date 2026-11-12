export function buildP1ContextRequest({ sessionId, expectedSessionVersion, context }) {
  const underThree = typeof context.age_months === 'number' && context.age_months < 36;
  const usesContextualCandidates = context.contextual_candidate_flow === true;
  const usesCompleteActivityDiscovery = context.complete_activity_discovery_flow === true;
  const {
    caregiver_participating: caregiverParticipating,
    contextual_candidate_flow: _contextualCandidateFlow,
    complete_activity_discovery_flow: _completeActivityDiscoveryFlow,
    ...contextFields
  } = context;
  return {
    ...contextFields,
    contract_name: usesCompleteActivityDiscovery
      ? 'P1ContextV4'
      : usesContextualCandidates
      ? 'P1ContextV3'
      : underThree ? 'P1ContextV2' : 'P1ContextV1',
    contract_version: usesCompleteActivityDiscovery
      ? '4.0'
      : usesContextualCandidates ? '3.0' : underThree ? '2.0' : '1.0',
    session_id: sessionId,
    expected_session_version: expectedSessionVersion,
    gate_a_confirmed: true,
    ...(usesContextualCandidates && !usesCompleteActivityDiscovery
      ? {candidate_selection_mode: 'CONTEXTUAL_SHORTLIST'}
      : {}),
    ...(usesCompleteActivityDiscovery
      ? {
          candidate_selection_mode: 'COMPLETE_TOPIC_AGE_LIST',
          discovery_policy: 'TOPIC_AGE_SAFETY_DISCOVERY_V1',
          caregiver_participating: caregiverParticipating === true,
        }
      : underThree
      ? { caregiver_participating: caregiverParticipating === true }
      : {}),
  };
}
