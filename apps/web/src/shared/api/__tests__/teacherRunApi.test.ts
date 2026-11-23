import { afterEach, describe, expect, it, vi } from "vitest";
import { teacherRunApi } from "../teacherRunApi";

afterEach(() => { vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; });

describe("Teacher run API", () => {
  it("uses strong conditional revisions and a key for selection and projection", async () => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    const fetcher = vi.fn(async () => ({ ok: true, status: 200, headers: new Headers(), text: async () => "{}" }) as Response);
    vi.stubGlobal("fetch", fetcher);
    await teacherRunApi.confirmSelection("occ", "selection", 4, "hash", "key-1");
    await teacherRunApi.projectionConfirm("occ", 5, "run", "generation", "key-2");
    const first = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    const second = fetcher.mock.calls[1] as unknown as [string, RequestInit];
    expect(new Headers(first[1].headers).get("If-Match")).toBe('"4"');
    expect(new Headers(first[1].headers).get("Idempotency-Key")).toBe("key-1");
    expect(JSON.parse(String(first[1].body))).toEqual({ expected_selection_sha256: "hash" });
    expect(new Headers(second[1].headers).get("If-Match")).toBe('"5"');
    expect(JSON.parse(String(second[1].body))).toEqual({ run_id: "run", generation_id: "generation", audience: "CLASS", use: "CLASS_PROJECTION" });
  });
  it("does not send a key or body when requesting a playback token", async () => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    const fetcher = vi.fn(async () => ({ ok: true, status: 200, headers: new Headers(), text: async () => "{}" }) as Response);
    vi.stubGlobal("fetch", fetcher);
    await teacherRunApi.projectionToken("occ");
    const [, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).has("Idempotency-Key")).toBe(false);
    expect(init.body).toBeUndefined();
  });

  it.each([5, 2])("carries current_version %s from video-generation stale responses", async currentVersion => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ code: "STALE_REVISION", message: "Thông tin đã thay đổi.", correlation_id: "corr", retryable: false, retry_after_seconds: null, field_errors: [], current_version: currentVersion }), { status: 409 }));
    vi.stubGlobal("fetch", fetcher);
    await expect(teacherRunApi.generateVideo("run", 4, "hash", undefined, "video-key")).rejects.toMatchObject({ code: "STALE_REVISION", status: 409, currentVersion });
  });
});

describe("sample run route contracts", () => {
 const lifecycle = {request_id:"req",lifecycle:{run_id:"run",run_state:"DELETE_PENDING",revision:2,version:1,lifecycle_request_ref:"ref",purge_state:"PENDING"}};
 const input = {profile_ref:{kind:"MANAGED_PROFILE" as const,id:"child"},occurrence_id:"occ",plan:{revision_no:1,plan_hash:"hash"},activity_id:"activity",selection_id:"sel",selection_sha256:"digest"};
 function mock(body: unknown = lifecycle, status=200) {window.sketch2lifeAuth={getIdToken:async()=>"token"}; const fetcher=vi.fn(async()=>({ok:status===200,status,headers:new Headers({ETag:'"etag"'}),text:async()=>JSON.stringify(body)}) as Response); vi.stubGlobal("fetch",fetcher); return fetcher;}
 function check(fetcher: ReturnType<typeof mock>, path: string, method: string, key: string | null, body?: unknown, conditional?: [string,string]) {const [url,init]=fetcher.mock.calls[0] as unknown as [string,RequestInit]; expect(url.endsWith(path)).toBe(true);expect(init.method ?? "GET").toBe(method); const headers=new Headers(init.headers);expect(headers.get("Authorization")).toBe("Bearer token"); expect(headers.get("Idempotency-Key")).toBe(key); if(conditional) expect(headers.get(conditional[0])).toBe(conditional[1]); expect(init.body === undefined ? undefined : JSON.parse(String(init.body))).toEqual(body);}
 it("draw POST has a key and empty body",async()=>{const f=mock({selection_id:"sel"});expect(await teacherRunApi.draw("occ","draw-key")).toEqual({selection_id:"sel"});check(f,"/v1/lesson-occurrences/occ/child-selections","POST","draw-key",{});});
 it("selection GET sends conditional header and preserves 304",async()=>{const f=mock(null,304);expect(await teacherRunApi.getSelection("occ","sel",'"old"')).toEqual({data:null,etag:'"etag"',notModified:true});check(f,"/v1/lesson-occurrences/occ/child-selections/sel","GET",null,undefined,["If-None-Match",'"old"']);});
 it("confirmation POST quotes revision and sends hash",async()=>{const f=mock({state:"CONFIRMED"});expect(await teacherRunApi.confirmSelection("occ","sel",3,"hash","confirm-key")).toEqual({state:"CONFIRMED"});check(f,"/v1/lesson-occurrences/occ/child-selections/sel/confirmation","POST","confirm-key",{expected_selection_sha256:"hash"},["If-Match",'"3"']);});
 it("create POST sends exact teacher input and returns lifecycle",async()=>{const f=mock();expect(await teacherRunApi.create(input,"create-key")).toEqual(lifecycle);check(f,"/v1/story-runs","POST","create-key",input);});
 it("active GET returns null or lifecycle with no key",async()=>{const f=mock({request_id:"req",story_run:null});expect(await teacherRunApi.active()).toEqual({request_id:"req",story_run:null});check(f,"/v1/story-runs/active/current","GET",null);f.mockResolvedValueOnce({ok:true,status:200,headers:new Headers(),text:async()=>JSON.stringify(lifecycle)} as Response);expect(await teacherRunApi.active()).toEqual(lifecycle);});
 it("run GET sends If-None-Match and returns lifecycle",async()=>{const f=mock();expect((await teacherRunApi.get("run",'"old"')).data).toEqual(lifecycle);check(f,"/v1/story-runs/run","GET",null,undefined,["If-None-Match",'"old"']);});
 it("cancel POST sends revision and returns lifecycle",async()=>{const f=mock();expect(await teacherRunApi.cancel("run",4,"cancel-key")).toEqual(lifecycle);check(f,"/v1/story-runs/run/cancel","POST","cancel-key",{expected_revision:4});});
});
