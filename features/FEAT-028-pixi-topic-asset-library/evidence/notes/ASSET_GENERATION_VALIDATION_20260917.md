# FEAT-028 starter atlas generation validation

- Evidence ID: EV-028-ASSET-01
- Related criteria: starter taxonomy, stable sprite IDs, provenance, transparent asset inputs, review gate
- Type: generated-asset/catalog validation
- Timestamp: 2026-09-17 14:36:37 Asia/Saigon
- Branch: codex/feat-018-contract-plan
- Plan revision/hash: 1 / SHA-256 6569E0E3417BB9B358368AA7F2FD0F663CBC036AC2E1D7130971A8AC52F14EC2

## Output

- 12 transparent PNG atlases, 1024x1536 each, 32-bit ARGB.
- 72 indexed sprite frames (six per atlas) across all 12 planned topic families; 72 unique stable IDs in asset-catalog.v1.json.
- Total PNG size: 18,247,840 bytes.
- Each atlas has a content SHA-256 in the catalog and full generator provenance/prompt brief in GENERATION_MANIFEST.md.
- Alpha spot-check: the top-left pixel of each PNG is alpha=0. This is not a full edge/halo visual certification.
- All 12 images and 72 frame entries remain REVIEW_PENDING, runtimeEligible=false. No asset was copied to approved/applied or referenced by runtime code.
- No external image source and no real child media was used; built-in ImageGen was used for authoring.

## Validation

Catalog validation command: python -c "import json,pathlib,hashlib; root=pathlib.Path('features/FEAT-028-pixi-topic-asset-library/assets/generated'); d=json.loads((root/'asset-catalog.v1.json').read_text(encoding='utf-8')); atlases=d['atlases']; ids=[s['id'] for a in atlases for s in a['sprites']]; assert len(atlases)==12 and len(ids)==72 and len(set(ids))==72; assert all(sorted(s['frameIndex'] for s in a['sprites'])==list(range(6)) for a in atlases); bad=[a['file'] for a in atlases if hashlib.sha256((root/a['file']).read_bytes()).hexdigest()!=a['sha256']]; assert not bad,bad; print(f'catalog_json=VALID atlases={len(atlases)} sprite_frames={len(ids)} unique_ids={len(set(ids))} sha256=PASS frame_maps=PASS')"

Result: catalog_json=VALID, 12 atlases, 72 frames, 72 unique IDs, all atlas hashes match, and each frame map contains indices 0 through 5.

Repository harness command: python tools/validate_harness.py --feature features/FEAT-028-pixi-topic-asset-library

Result: HARNESS_INVALID only because the pre-existing untracked FEAT-026-current-system-srs folder is missing evidence/raw and evidence/metrics. FEAT-028 reports no missing harness paths. The unrelated FEAT-026 data was not changed.

## Interpretation and remaining gate

The starter spritesheet/catalog structure is mechanically consistent and hash-verified. This does not certify visual quality, crop safety, or exact style match to a particular child's drawing. Project-owner visual review is still required for every atlas before any promotion or runtime use. The resolver/runtime adapter, local style-profile adaptation, and 20-golden-scene coverage audit remain unfinished implementation work.
