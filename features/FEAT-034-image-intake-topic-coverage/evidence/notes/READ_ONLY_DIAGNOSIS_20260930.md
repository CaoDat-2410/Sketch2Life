# Read-only diagnosis — 2026-09-30

## Scope and limits

Inspected repository code and loaded the checked-in catalog using the local backend virtual environment. No application code, catalog row, running backend/frontend/emulator, provider, or user media was modified/read. The attached screenshot does not expose the exact VLM tags, selected-image MIME/size/dimensions, or request diagnostics, so the individual image failure and exact runtime giraffe payload cannot be proven from this screenshot alone.

## Image intake

- `apps/ui-mobile/src/context/AppContext.tsx` uses the system image picker (`launchImageLibraryAsync`), rejects picker metadata above 5,000,000 bytes, and only accepts metadata normalized to PNG/JPEG. Unsupported files get a PNG/JPEG message; the native picker exception path is generic.
- `apps/ui-mobile/src/context/workflowSafety.ts` explicitly recognizes only PNG/JPEG.
- Backend `/v1/sessions/{session_id}/media/image` reads at most 5,000,001 bytes. `Feat018AdmissionLimits` accepts only static PNG/JPEG containers, one frame, at most 5,000,000 bytes, 4,000,000 pixels, and longest edge 4,096.
- Therefore “some photos work, some do not” is consistent with unsupported WebP/HEIC/HEIF, byte/dimension/frame limits, metadata disagreement, corrupt files, or URI access failure. Without that selected asset's safe metadata/reason code, the precise cause remains undetermined.

## Giraffe / Montessori recommendation

- `semantic_activity_resolver.py::_concept_ids` maps selected animal terms, but its explicit label tokens omit `hươu cao cổ` and `giraffe`. If the confirmed anchor carries no broader recognized animal tag, the scene is unclassified for activity matching.
- The same resolver intentionally skips `AGE_BASELINE_FALLBACK` in complete discovery. That avoids unrelated activities, but an unmapped subject can consequently produce a zero-result list even when appropriate general animal activities exist.
- The suggestion endpoint requests `limit=None` and uses the complete-discovery path. This matches the full-list product decision and shows the empty state is downstream of semantic matching/eligibility, not a top-three UI truncation.
- A read-only catalog load produced 300 templates/profiles total: 100 MVP records plus 200 curated variants across 50 activity families. The active animal-concept subset has 24 age variants across six family IDs. Count is not evidence of relevance/quality.
- Current curated expansion data gives broad animal observation/classification/movement rows `ANIMAL_BUTTERFLY`, while the butterfly family also includes broad `ANIMAL_GENERIC`; this is a concrete mapping-quality issue to review, because it can create both false negatives and irrelevant matches.

## Reproduction commands

```powershell
rg -n "def _concept_ids|AGE_BASELINE_FALLBACK|complete_discovery=True|limit=None" backend/src/sketch2life/application/services/semantic_activity_resolver.py backend/src/sketch2life/application/services/supervised_flow.py
backend/.venv/Scripts/python.exe -X utf8 -c "import sys,json; from pathlib import Path; sys.path.insert(0,str(Path('backend/src').resolve())); from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library; from sketch2life.infrastructure.catalog.curated_catalog import load_curated_catalog_v2; from sketch2life.infrastructure.catalog.activity_semantics_v2 import load_activity_semantic_catalog_v2; root=Path('.').resolve(); p=load_p1_template_library(root,include_mvp=True,include_expansion=True); c=load_curated_catalog_v2(root); s=load_activity_semantic_catalog_v2(root,include_expansion=True); animals=[v for v in c.variants if {'ANIMAL_GENERIC','ANIMAL_BUTTERFLY','ANIMAL_MOVEMENT'} & set(v.concept_ids)]; print(json.dumps({'templates':len(p.templates),'curated_families':len({v.activity_family_id for v in c.variants}),'curated_variants':len(c.variants),'semantic_profiles':len(s.profiles),'animal_family_count':len({v.activity_family_id for v in animals}),'animal_variants':len(animals)}))"
```

## Interpretation

First correct and exhaustively validate the full catalog mapping and animal aliases; do not bulk-add activities merely because the zero-result state appeared. The owner's selected plan keeps the full safe/age/topic list visible and lets AI highlight three. AI ranking remains secondary to deterministic eligibility and must not hide the list when it is slow or unavailable.
