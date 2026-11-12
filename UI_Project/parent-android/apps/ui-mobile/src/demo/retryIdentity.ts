export interface ErrorOutcome {
  code?: unknown;
  statusCode?: unknown;
}

export class PendingIdempotencyKeys {
  private readonly pending = new Map<string, string>();

  get(scope: string, createKey: () => string): string {
    const current = this.pending.get(scope);
    if (current) return current;
    const created = createKey();
    this.pending.set(scope, created);
    return created;
  }

  settle(scope: string, retainForRetry: boolean): void {
    if (!retainForRetry) this.pending.delete(scope);
  }
}

export function outcomeMayHaveCommitted(error: unknown): boolean {
  if (typeof error !== 'object' || error === null) return false;
  const value = error as ErrorOutcome;
  const code = typeof value.code === 'string' ? value.code : '';
  const statusCode = typeof value.statusCode === 'number' ? value.statusCode : -1;
  return code === 'NETWORK_ERROR'
    || code === 'REQUEST_TIMEOUT'
    || code === 'INVALID_RESPONSE'
    || statusCode === 0
    || statusCode === 408
    || statusCode >= 500;
}

export async function withPendingIdempotencyKey<T>(
  cache: PendingIdempotencyKeys,
  scope: string,
  createKey: () => string,
  operation: (idempotencyKey: string) => Promise<T>,
): Promise<T> {
  const key = cache.get(scope, createKey);
  try {
    const result = await operation(key);
    cache.settle(scope, false);
    return result;
  } catch (error) {
    cache.settle(scope, outcomeMayHaveCommitted(error));
    throw error;
  }
}
