# C2c — library/generation/composition preparation, not durable completion

2026-10-18; parent b06b8a8 (08 code checkpoint16712de); approved revision1 unchanged.
Direct owner request continues08 in this chat, not the original12 goal.

## Delivered owned surface

- Pure MediaProfile/MediaBlob/DecodedMedia terms, all bounds supplied explicitly.
  No default production codecs/duration/size/dimensions/audio/TTS/model/provider.
- Candidate ports LibraryResolver, VideoGenerator, LibraryComposer,
  VideoSourceResolver, MediaProfileResolver, MediaDecoder/MediaValidator and
  RenderAuthority; no default implementation of authority/providers/decoder.
- VideoMediaPipeline selects exactly pinned reviewed_library/generate/compose_library.
  Missing implementation is explicit unsupported, no automatic alternate strategy.
  Library path needs no generation model or raw script load; still pending final
  Teacher review, with current publication/recall/rights/profile/audience duties
  at resolver/authority boundary. No extra mandatory script approval introduced.
- Generate consumes exact upstream bundle/script pin; compose verifies/adopts
  library input before forwarding it. Catalog/content hash and actual media-byte
  hash are separate namespaces, not assumed equal.
- Original operation key binds schema/pin (including policy epoch)/job/attempt/
  strategy. Stable through progress revisions/restart of SAME attempt, changes
  for a different attempt or lineage. Actual external dedup/adoption remains open.
- Native value revalidation, nonempty immutable bytes, size BEFORE hashing/decode,
  exact SHA256; complete decoder result must match source/profile/container/codec/
  dimensions/duration/frame count/audio rules. No trust in MIME/provider-success/
  metadata-only probe. Decoder actual runtime/resource limits remain adapter duty.
- Current authority checks around source/library/provider/validation work; no DB
  transaction held across external calls. These checks detect intervening changes
  but DO NOT replace held completion fences or prevent every external-side race.
- Return PreparedVideoMedia only: no artifact, persisted success, review approval,
  playback URL, exposure grant, job mutation or session advancement. P3 MUST
  independently accept/quarantine with current guards and atomic foundation bridge.
- Raw script/media/capability excluded from ordinary repr output. Provider-specific
  diagnostic mapping/copy registration/cleanup belongs to later edge/worker work.

## Local evidence / actual-runtime limits

73 new explicitly fixture decoder/provider/authority cases; cumulative329 own.
Broad1764 PASS (own329 +1435 existing), source unchanged across636 backend inventory
files. Ruff/Mypy14 owned source files PASS. Evidence E05 has exact receipts.

Read-only Get-Command ffmpeg,ffprobe found no executable in PATH. No install/search
for credentials/start service/model call. Test payload explicitly NOT a real
video. Actual full-decode and generation evidence NOT_RUN, not inferred from mocks.
Prepared PostgreSQL11 still collection only. Runtime profile/rights/adoption
choices are still D01–D06, not decided by passing these tests.

## Next owned work

P3 worker/attempt/status/failure/finalization composition, atomic accept/quarantine
and actual provider-copy hooks. Actual foundation bridge CR08-01 remains open;
do not finalize by sequential job and video commits. Real07/BE1/current definitions/
library/provider/decoder bindings not supplied by this component. P4 consolidated
runner and source-bound external test package; P5 actual runtime after separate
approval. Whole08 NOT_DONE, no production route activation.
