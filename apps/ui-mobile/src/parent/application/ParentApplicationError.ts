export class ParentApplicationError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly requestId?: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = 'ParentApplicationError';
  }
}
