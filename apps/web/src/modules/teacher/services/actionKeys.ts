import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";

/** Reuses a key only while the same action is eligible for retry. */
export class ActionKeys {
  private readonly keys = new Map<string, string>();

  key(...fingerprint: unknown[]): string {
    const signature = JSON.stringify(fingerprint);
    let key = this.keys.get(signature);
    if (!key) {
      key = createIdempotencyKey();
      this.keys.set(signature, key);
    }
    return key;
  }

  settled(fingerprint: unknown[], error?: unknown): void {
    if (!error || (error instanceof BackendApiError && error.status >= 400 && error.status < 500)) {
      this.keys.delete(JSON.stringify(fingerprint));
    }
  }
}
