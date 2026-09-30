export const PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT = 1;

export function acceptPreferenceClassification(
  gate,
  submittedRevision,
  currentChildId,
  submittedChildId,
  classification,
) {
  if (currentChildId !== submittedChildId || !gate.markClassified(submittedRevision)) {
    return null;
  }
  return {
    proposed_interest_tags: classification.interest_tags,
    proposed_avoid_tags: classification.avoid_tags,
    interests: classification.interest_tags.map((tag) => tag.concept_id),
    dislikes: classification.avoid_tags.map((tag) => tag.concept_id),
    preference_tags_confirmed: false,
  };
}

export class PreferenceRevisionGate {
  #revision = 0;
  #classifiedRevision = null;
  #attempts = 0;
  #inFlight = false;

  advance() {
    this.#revision += 1;
    this.#classifiedRevision = null;
    this.#attempts = 0;
    this.#inFlight = false;
    return this.#revision;
  }

  current() {
    return this.#revision;
  }

  canClassify() {
    return this.#classifiedRevision !== this.#revision
      && this.#attempts < PREFERENCE_CLASSIFICATION_ATTEMPT_LIMIT;
  }

  beginAttempt(revision) {
    if (revision !== this.#revision || !this.canClassify() || this.#inFlight) return false;
    this.#attempts += 1;
    this.#inFlight = true;
    return true;
  }

  markClassified(revision) {
    if (revision !== this.#revision || !this.#inFlight) return false;
    this.#inFlight = false;
    this.#classifiedRevision = revision;
    return true;
  }

  markFailed(revision) {
    if (revision !== this.#revision || !this.#inFlight) return false;
    this.#inFlight = false;
    return true;
  }

  reset() {
    this.#revision = 0;
    this.#classifiedRevision = null;
    this.#attempts = 0;
    this.#inFlight = false;
  }
}
