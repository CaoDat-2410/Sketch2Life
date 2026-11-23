import { afterEach, describe, expect, it, vi } from "vitest";
import { teacherRunApi } from "../teacherRunApi";
import { teacherOccurrenceApi } from "../teacherOccurrenceApi";
import { readTeacherPlayback } from "../teacherPlayback";

const input = { profile_ref: { kind: "MANAGED_PROFILE" as const, id: "child" }, occurrence_id: "occ", plan: { revision_no: 1, plan_hash: "hash" }, activity_id: "act", selection_id: "sel", selection_sha256: "digest" };
type Case = [string, () => Promise<unknown>, string, string, unknown, string | null, [string, string]?];
const cases: Case[] = [
  ["selection POST", () => teacherRunApi.draw("occ", "key"), "/v1/lesson-occurrences/occ/child-selections", "POST", {}, "key"],
  ["selection GET", () => teacherRunApi.getSelection("occ", "sel", '"2"'), "/v1/lesson-occurrences/occ/child-selections/sel", "GET", undefined, null, ["If-None-Match", '"2"']],
  ["selection confirmation", () => teacherRunApi.confirmSelection("occ", "sel", 2, "hash", "key"), "/v1/lesson-occurrences/occ/child-selections/sel/confirmation", "POST", { expected_selection_sha256: "hash" }, "key", ["If-Match", '"2"']],
  ["create", () => teacherRunApi.create(input, "key"), "/v1/story-runs", "POST", input, "key"],
  ["active current", () => teacherRunApi.active(), "/v1/story-runs/active/current", "GET", undefined, null],
  ["run GET", () => teacherRunApi.get("run", '"2"'), "/v1/story-runs/run", "GET", undefined, null, ["If-None-Match", '"2"']],
  ["cancel", () => teacherRunApi.cancel("run", 2, "key"), "/v1/story-runs/run/cancel", "POST", { expected_revision: 2 }, "key"],
  ["assets", () => teacherRunApi.attachArtwork("run", "upl_id", 2, "key"), "/v1/story-runs/run/assets", "POST", { asset_ref: "upl_id", expected_run_revision: 2 }, "key"],
  ["idea", () => teacherRunApi.idea("run", { expected_run_revision: 2, text: "idea" }, "key"), "/v1/story-runs/run/idea", "POST", { expected_run_revision: 2, text: "idea" }, "key"],
  ["transcript", () => teacherRunApi.transcript("run"), "/v1/story-runs/run/transcript", "GET", undefined, null],
  ["transcript confirmation", () => teacherRunApi.confirmTranscript("run", 2, "hash", "key"), "/v1/story-runs/run/transcript-confirmation", "POST", { expected_transcript_revision: 2, transcript_sha256: "hash", confirmed: true }, "key"],
  ["context confirmation", () => teacherRunApi.confirmContext("run", 2, "hash", "key"), "/v1/story-runs/run/context-confirmation", "POST", { expected_context_revision: 2, context_snapshot_sha256: "hash", confirmed: true }, "key"],
  ["subject confirmation", () => teacherRunApi.confirmSubject("run", 2, "tree", "key"), "/v1/story-runs/run/subject-confirmation", "POST", { expected_understanding_revision: 2, confirmed_subject: "tree" }, "key"],
  ["story rewrites", () => teacherRunApi.rewrite("run", 2, "hash", "hint", "key"), "/v1/story-runs/run/story-rewrites", "POST", { expected_story_revision: 2, expected_story_sha256: "hash", hint: "hint" }, "key"],
  ["script confirmation", () => teacherRunApi.confirmStory("run", 2, "hash", "key"), "/v1/story-runs/run/script-confirmation", "POST", { expected_revision: 2, story_sha256: "hash" }, "key"],
  ["video generations", () => teacherRunApi.generateVideo("run", 2, "hash", "OTHER", "key"), "/v1/story-runs/run/video-generations", "POST", { expected_revision: 2, story_sha256: "hash", quality_reason_code: "OTHER" }, "key"],
  ["job GET", () => teacherOccurrenceApi.getJob("job", '"2"'), "/v1/jobs/job", "GET", undefined, null, ["If-None-Match", '"2"']],
  ["video unsuitable", () => teacherRunApi.unsuitable("run", 2, "generation", "OTHER", "key"), "/v1/story-runs/run/video-unsuitable", "POST", { expected_revision: 2, generation_id: "generation", reason_code: "OTHER" }, "key"],
  ["complete", () => teacherRunApi.complete("run", 2, "key"), "/v1/story-runs/run/complete", "POST", { expected_revision: 2 }, "key"],
  ["owner playback token", () => teacherRunApi.ownerToken("run"), "/v1/story-runs/run/playback-token", "POST", undefined, null],
  ["projection confirmation", () => teacherRunApi.projectionConfirm("occ", 2, "run", "gen", "key"), "/v1/lesson-occurrences/occ/projection-confirmation", "POST", { run_id: "run", generation_id: "gen", audience: "CLASS", use: "CLASS_PROJECTION" }, "key", ["If-Match", '"2"']],
  ["projection token", () => teacherRunApi.projectionToken("occ"), "/v1/lesson-occurrences/occ/projection-playback-token", "POST", undefined, null],
];
afterEach(() => { vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; });
describe("C0 route contracts", () => {
  it.each(cases)("C0 %s", async (_name, call, path, method, body, key, conditional) => { window.sketch2lifeAuth = { getIdToken: async () => "bearer" }; const fetcher = vi.fn(async () => new Response("{}", { status: 200 })); vi.stubGlobal("fetch", fetcher); await call(); const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit]; expect(url.endsWith(path)).toBe(true); expect(init.method ?? "GET").toBe(method); const headers = new Headers(init.headers); expect(headers.get("Authorization")).toBe("Bearer bearer"); expect(headers.get("Idempotency-Key")).toBe(key); expect(init.body === undefined ? undefined : JSON.parse(String(init.body))).toEqual(body); if (conditional) expect(headers.get(conditional[0])).toBe(conditional[1]); if (conditional?.[0] !== "If-Match") expect(headers.has("If-Match")).toBe(false); });
  it("C0 stream GET carries bearer, playback token and range without a key or body", async () => { window.sketch2lifeAuth = { getIdToken: async () => "bearer" }; const fetcher = vi.fn(async () => new Response(new Uint8Array([1]), { status: 200 })); vi.stubGlobal("fetch", fetcher); await readTeacherPlayback("run", new AbortController().signal, async () => ({ token: "grant", stream_path: "/v1/story-runs/run/playback" })); const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit]; const h = new Headers(init.headers); expect(url.endsWith("/v1/story-runs/run/playback")).toBe(true); expect(init.method ?? "GET").toBe("GET"); expect(init.body).toBeUndefined(); expect(h.get("Idempotency-Key")).toBeNull(); expect(h.get("Authorization")).toBe("Bearer bearer"); expect(h.get("X-Playback-Token")).toBe("grant"); expect(h.get("Range")).toBe("bytes=0-4194303"); });
});
