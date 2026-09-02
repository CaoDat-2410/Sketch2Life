# Phase 3 - Asset Library and Cache-first Resolver

## Responsibility

`AssetLibrary` owns deterministic lookup of reviewed asset metadata. `CacheFirstResolver` owns the policy decision: reuse a valid reviewed asset before selecting a generation path.

## Lookup identity

An asset is eligible only when all four values match the request:

- `objective_id`;
- objective `version`;
- `locale`;
- `age_band`.

The asset contract also requires `review_status = REVIEWED`.

## Runtime behavior

```text
LearningObjective
  -> AssetLibrary.find_reviewed()
      -> matching reviewed asset: ResolverResult(HIT, generation_required=false)
      -> no matching asset: ResolverResult(MISS, generation_required=true)
```

The resolver does not call a model or generator. This makes the cache policy deterministic and keeps generation provider-neutral for the next phase.

## Verification cases

- Matching butterfly objective returns the reviewed video asset.
- Unknown objective returns `MISS` with `NO_REVIEWED_ASSET`.
- Version mismatch returns `MISS`.
- A `HIT` result explicitly carries `generation_required=false`.

## Boundary note

File existence and MP4 decoding belong to the later FFmpeg media-validation phase. The library currently resolves metadata so the same code can later be backed by object storage without changing the resolver policy.
