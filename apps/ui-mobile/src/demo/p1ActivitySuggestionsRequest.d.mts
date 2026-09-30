export declare function buildP1ActivitySuggestionsRequest(input: {
  ageMonths: number;
  childProfile: {
    profile_declared_by: 'CAREGIVER' | 'GUIDE';
    profile_recorded_at: string;
    preference_tags_confirmed: boolean;
    interests: string[];
    dislikes: string[];
    adult_participating: boolean | null;
    caregiver_participating: boolean | null;
  };
}): Record<string, unknown>;
