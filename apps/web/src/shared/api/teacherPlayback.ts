import { apiBaseUrl, BackendApiError } from "./backendApi";
import { authorizedHeaders } from "./teacherHttp";
import { teacherRunApi } from "./teacherRunApi";

const PART = 4 * 1024 * 1024;
const MAX = 100 * 1024 * 1024;

/** Read an owner-view grant entirely in memory; the grant never becomes a media URL. */
export async function readTeacherPlayback(runId: string, signal: AbortSignal, getGrant: () => Promise<{ token: string; stream_path: string }> = async () => (await teacherRunApi.ownerToken(runId)).playback): Promise<Blob> {
  const path = `/v1/story-runs/${encodeURIComponent(runId)}/playback`;
  const grant = async () => {
    const playback = await getGrant();
    if (playback.stream_path !== path) throw new BackendApiError("", "INVALID_RESPONSE", 502);
    return playback.token;
  };
  let token = await grant();
  let refreshed = false;
  let offset = 0;
  let total: number | undefined;
  let whole = false;
  const chunks: BlobPart[] = [];
  async function boundedBytes(response: Response): Promise<Uint8Array> {
    if (!response.body) return new Uint8Array(await response.arrayBuffer());
    const reader = response.body.getReader(); const parts: Uint8Array[] = []; let size = 0;
    while (true) { const part = await reader.read(); if (part.done) break; size += part.value.byteLength; if (size > MAX) { await reader.cancel(); throw new BackendApiError("", "PLAYBACK_TOO_LARGE", 413); } parts.push(part.value); }
    const result = new Uint8Array(size); let position = 0; for (const part of parts) { result.set(part, position); position += part.byteLength; } return result;
  }
  while (total === undefined || offset < total) {
    if (signal.aborted) throw new DOMException("Playback stopped", "AbortError");
    const headers = await authorizedHeaders();
    headers.set("X-Playback-Token", token);
    if (!whole) headers.set("Range", `bytes=${offset}-${offset + PART - 1}`);
    const response = await fetch(`${apiBaseUrl()}${path}`, { headers, signal });
    if (response.status === 401 && !refreshed) { token = await grant(); refreshed = true; continue; }
    if (response.status === 416 && total !== undefined && offset === total) break;
    if (response.status !== 200 && response.status !== 206) throw new BackendApiError("", "PLAYBACK_FAILED", response.status);
    const length = Number(response.headers.get("Content-Length"));
    if (response.status === 206) {
      const match = /^bytes (\d+)-(\d+)\/(\d+)$/.exec(response.headers.get("Content-Range") ?? "");
      if (!match) { if (whole || (Number.isFinite(length) && length > MAX)) throw new BackendApiError("", "INVALID_RESPONSE", 502); whole = true; chunks.length = 0; offset = 0; total = undefined; continue; }
      const start = Number(match[1]); const end = Number(match[2]); const size = Number(match[3]);
      if (start !== offset || end < start || size > MAX || end >= size || (total !== undefined && size !== total)) throw new BackendApiError("", "INVALID_RESPONSE", 502);
      total = size;
      const bytes = await boundedBytes(response);
      if (bytes.byteLength !== end - start + 1) throw new BackendApiError("", "INVALID_RESPONSE", 502);
      chunks.push(bytes as BlobPart); offset += bytes.byteLength;
    } else {
      if (Number.isFinite(length) && length > MAX) throw new BackendApiError("", "PLAYBACK_TOO_LARGE", 413);
      const bytes = await boundedBytes(response);
      if (bytes.byteLength > MAX) throw new BackendApiError("", "PLAYBACK_TOO_LARGE", 413);
      return new Blob([bytes as BlobPart], { type: "video/mp4" });
    }
  }
  return new Blob(chunks, { type: "video/mp4" });
}
