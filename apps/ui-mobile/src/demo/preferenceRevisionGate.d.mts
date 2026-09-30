export declare const PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT: 1;

export interface PreferenceClassificationResult {
  interest_tags: Array<{ concept_id: string; label_vi: string; confidence: number }>;
  avoid_tags: Array<{ concept_id: string; label_vi: string; confidence: number }>;
}

export interface PreferenceClassificationProfilePatch {
  proposed_interest_tags: PreferenceClassificationResult['interest_tags'];
  proposed_avoid_tags: PreferenceClassificationResult['avoid_tags'];
  interests: string[];
  dislikes: string[];
  preference_tags_confirmed: false;
}

export declare function acceptPreferenceClassification(
  gate: PreferenceRevisionGate,
  submittedRevision: number,
  currentChildId: string,
  submittedChildId: string,
  classification: PreferenceClassificationResult,
): PreferenceClassificationProfilePatch | null;

export declare class PreferenceRevisionGate {
  advance(): number;
  current(): number;
  canClassify(): boolean;
  beginAttempt(revision: number): boolean;
  markClassified(revision: number): boolean;
  markFailed(revision: number): boolean;
  reset(): void;
}
