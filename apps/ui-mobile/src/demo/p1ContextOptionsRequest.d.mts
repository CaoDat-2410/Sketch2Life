import type { ChildLearningProfileInput } from './api';

export interface P1ContextOptionsRequestV2 {
  contract_name: 'P1ContextOptionsRequestV2';
  contract_version: '2.0';
  age_months: number;
  candidate_activity_ids: string[];
  child_profile: {
    contract_name: 'ChildLearningProfileContextV2';
    contract_version: '2.0';
    profile_declared_by: ChildLearningProfileInput['profile_declared_by'];
    profile_recorded_at: string;
    preference_tags_confirmed: boolean;
    interests: string[];
    dislikes: string[];
    readiness_ids: string[] | null;
    available_material_option_ids: string[] | null;
    learning_support_ids: ChildLearningProfileInput['learning_support_ids'];
  };
  adult_participating: boolean;
  caregiver_participating: boolean;
  supervision_confirmed_activity_ids: string[];
}

export declare function buildP1ContextOptionsRequest(input: {
  ageMonths: number;
  childProfile: ChildLearningProfileInput;
  candidateActivityIds: string[];
  supervisionConfirmedActivityIds: string[];
}): P1ContextOptionsRequestV2;
