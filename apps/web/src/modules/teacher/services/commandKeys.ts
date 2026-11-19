// FEAT-066 C4 (SRS 21.1, 21.4): one Idempotency-Key per exact command. The signature holds the
// command, organization, target, the If-Match revision sent and the payload, so a retry of the
// same command reuses its key while a new revision or a changed payload gets a new key.
import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";

export function commandSignature(...parts: unknown[]): string {
  return JSON.stringify(parts);
}

export function keyForCommand(store: Map<string, string>, signature: string): string {
  let key = store.get(signature);
  if (!key) {
    key = createIdempotencyKey();
    store.set(signature, key);
  }
  return key;
}

/** True for a 409 STALE_REVISION answer (the target changed since it was loaded). */
export function isStaleRevision(cause: unknown): boolean {
  return cause instanceof BackendApiError && cause.status === 409 && cause.code === "STALE_REVISION";
}
