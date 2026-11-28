// The server names a sample run on the occurrence only after a class projection is confirmed
// (`sample_video.run_ref`). A run completed before that is findable only by its id, so this browser
// keeps the id per occurrence. It is an opaque id; the server still decides who may read the run.
const key = (occurrenceId: string) => `s2l.teacher.sample-run.${occurrenceId}`;

export function rememberSampleRun(occurrenceId: string, runId: string): void {
  try { window.localStorage.setItem(key(occurrenceId), runId); } catch { /* storage is optional */ }
}

export function recalledSampleRun(occurrenceId: string): string | null {
  try { return window.localStorage.getItem(key(occurrenceId)); } catch { return null; }
}
