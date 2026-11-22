import { BackendApiError } from "../../../shared/api/backendApi";

export type RunUploadPurpose = "RUN_ARTWORK" | "RUN_AUDIO";
const types: Record<RunUploadPurpose, Record<string, string>> = {
  RUN_ARTWORK: { jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", webp: "image/webp" },
  RUN_AUDIO: { wav: "audio/wav", mp4: "audio/mp4", m4a: "audio/mp4" },
};
export function runFileMediaType(file: File, purpose: RunUploadPurpose): string {
  const ext = file.name.toLowerCase().split(".");
  const mediaType = ext.length > 1 ? types[purpose][ext[ext.length - 1]] : undefined;
  if (!mediaType) throw new BackendApiError("", "UNSUPPORTED_MEDIA_TYPE", 415);
  if (file.size < 1 || file.size > (purpose === "RUN_AUDIO" ? 20_000_000 : 20 * 1024 * 1024)) throw new BackendApiError("", purpose === "RUN_AUDIO" ? "AUDIO_TOO_LARGE" : "MEDIA_TOO_LARGE", 413);
  return mediaType;
}
export function cleanIdea(value: string): string | null {
  const text = value.trim();
  return text && Array.from(text).length <= 500 ? text : null;
}
export function inputActions(run: { run_state: string; context_confirmed: boolean; context_snapshot_sha256: string | null; understanding_revision: number | null; candidate: unknown }) {
  const input = ["INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW"].includes(run.run_state);
  return { artwork: input, idea: input, transcript: input, context: ["INPUT_PROCESSING", "SUBJECT_REVIEW", "PREPARATION_REVIEW"].includes(run.run_state) && !run.context_confirmed && !!run.context_snapshot_sha256, subject: run.run_state === "SUBJECT_REVIEW" && !!run.candidate && run.understanding_revision !== null };
}
