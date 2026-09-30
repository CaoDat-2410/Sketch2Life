export interface SessionBoundProfileAnswers {
  adult_participating: boolean | null;
  caregiver_participating: boolean | null;
  readiness_ids: string[] | null;
  available_material_option_ids: string[] | null;
}

export declare function resetSessionBoundProfileAnswers<
  T extends SessionBoundProfileAnswers,
>(profile: T): T;
