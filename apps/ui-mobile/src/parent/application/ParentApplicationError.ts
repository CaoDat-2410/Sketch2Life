export type ParentSafeFieldError = {
  field: string;
  code: string;
};

export type ParentApplicationErrorMetadata = {
  correlationId?: string;
  retryable?: boolean;
  retryAfterSeconds?: number;
  currentVersion?: string | number;
  fieldErrors?: ParentSafeFieldError[];
};

export class ParentApplicationError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly requestId?: string,
    readonly status?: number,
    metadata: ParentApplicationErrorMetadata = {},
  ) {
    super(message);
    this.name = 'ParentApplicationError';
    this.correlationId = metadata.correlationId;
    this.retryable = metadata.retryable;
    this.retryAfterSeconds = metadata.retryAfterSeconds;
    this.currentVersion = metadata.currentVersion;
    this.fieldErrors = metadata.fieldErrors;
  }

  readonly correlationId?: string;
  readonly retryable?: boolean;
  readonly retryAfterSeconds?: number;
  readonly currentVersion?: string | number;
  readonly fieldErrors?: ParentSafeFieldError[];
}
