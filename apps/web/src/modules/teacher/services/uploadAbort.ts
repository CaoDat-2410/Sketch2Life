// FEAT-066 C4 (package Draft 4, section 4): abort an upload session with the current revision.
// The server answers DELETE with 202 (aborted or already aborted), 409 STALE_REVISION (the
// revision moved), 410 UPLOAD_SESSION_EXPIRED or 409 UPLOAD_SESSION_STATE_CONFLICT (closed).
import { BackendApiError, backendApi, createIdempotencyKey, type LessonUploadSession } from "../../../shared/api/backendApi";

export interface AbortKeyRecord {
  abortKey?: string;
  abortRevision?: number;
}

export type AbortOutcome =
  | { kind: "aborted"; session: LessonUploadSession }
  | { kind: "closed"; session: LessonUploadSession | null }
  | { kind: "completed"; session: LessonUploadSession };

/** Return the stored key when it was made for this revision, else a new one (one key per command). */
export function abortKeyFor(record: AbortKeyRecord | null, revision: number): string {
  if (record?.abortKey && record.abortRevision === revision) return record.abortKey;
  return createIdempotencyKey();
}

function isClosed(cause: unknown): boolean {
  return cause instanceof BackendApiError && (
    cause.status === 410 || cause.code === "UPLOAD_SESSION_EXPIRED" || cause.code === "UPLOAD_SESSION_STATE_CONFLICT"
  );
}

function isStale(cause: unknown): boolean {
  return cause instanceof BackendApiError && cause.status === 409 && cause.code === "STALE_REVISION";
}

/**
 * Abort with the session's current revision. `knownRevision` is used only right after create;
 * otherwise the status is read first. A stale answer reads the status again and retries once with
 * a new key. `remember` lets the caller persist the key with the revision it was made for.
 */
export async function abortUploadWithRevision(
  uploadSessionId: string,
  options: {
    knownRevision?: number;
    record?: AbortKeyRecord | null;
    remember?: (key: string, revision: number) => void;
  } = {},
): Promise<AbortOutcome> {
  let revision = options.knownRevision;
  let record = options.record ?? null;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    if (revision === undefined) {
      const status = await backendApi.uploadSessionStatus(uploadSessionId);
      // A COMPLETED session is recovered by the caller, never cleared (review C4-IMPL-R1-05).
      if (status.state === "COMPLETED") return { kind: "completed", session: status };
      if (status.state !== "OPEN" && status.state !== "ABORTED") return { kind: "closed", session: status };
      revision = status.revision;
    }
    const key = abortKeyFor(record, revision);
    options.remember?.(key, revision);
    record = { abortKey: key, abortRevision: revision };
    try {
      const session = await backendApi.abortUploadSession(uploadSessionId, revision, key);
      return { kind: "aborted", session };
    } catch (cause) {
      if (isClosed(cause)) {
        const status = await backendApi.uploadSessionStatus(uploadSessionId).catch(() => null);
        if (status?.state === "COMPLETED") return { kind: "completed", session: status };
        return { kind: "closed", session: status };
      }
      if (isStale(cause) && attempt === 0) {
        revision = undefined;
        continue;
      }
      throw cause;
    }
  }
  throw new BackendApiError("Phiên tải lên vừa thay đổi. Vui lòng tải lại trạng thái rồi thử lại.", "STALE_REVISION", 409);
}
