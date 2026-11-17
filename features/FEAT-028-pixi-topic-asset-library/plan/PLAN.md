# FEAT-028 Pixi topic asset library plan

- Status: APPROVED
- Plan revision: 2
- Implementation status: IN_PROGRESS
- Visual asset status: GENERATED / REVIEW_PENDING; each sprite still requires separate visual review
- Target branch: `codex/feat-018-contract-plan`

## Goal

Give future UI/Pixi scenes stable, approved IDs for common child-drawing themes and a repeatable path for long-tail themes without manual web searching. Supplemental assets harmonize with the drawing (flat 2D, palette/outline/shape/detail profile) while leaving the original visible, immutable, and authoritative.

A finite static set cannot cover every imaginable topic. Deliver a curated starter catalog plus deterministic resolution and a governed authoring-time expansion workflow; unknown topics safely fall back instead of being fabricated or fetched at runtime.

## Scope

- Audit the Pixi loader, FEAT-018's 20 golden scenes/frozen contracts, FEAT-004 preservation, current asset directories, and review gate.
- Define a versioned catalog with stable semantic IDs, localized aliases/tags, category, dimensions/anchor/safe bounds, compatible style profile, hash/version, lineage, source/generator, license, and review state.
- Author at least 60 individually addressable flat-2D assets, at least five in each family: (1) sky/weather; (2) land/water/outdoor environments; (3) plants/flowers/trees; (4) animals (mammals, birds, insects, reptiles, aquatic); (5) people/roles/clothing; (6) homes/buildings/places; (7) vehicles/travel; (8) food/fruit/vegetables; (9) everyday/classroom/household objects; (10) art/craft/play/Montessori materials; (11) fantasy/underwater/space; (12) motion marks/non-semantic effects.
- Define a locally derived style profile: palette, outline/edge character, silhouette complexity, shape language, texture/detail, and contrast. It may tune/select a supplement but never reconstruct or replace the child's art.
- Add deterministic offline resolution by semantic ID/alias + profile. Return a typed miss and preserve source-art fallback; no runtime network lookup or generation.
- Define authoring-time long-tail expansion: normalize the adult/child-confirmed topic, create/source an isolated supplement from a synthetic/style-profile brief, record provenance/license/hash, visually review, and publish an immutable catalog version. ImageGen/open-license sources are authoring-only; never send real child images to them.
- Map all 20 FEAT-018 golden-scene themes to catalog entries or explicit source-only fallback and report gaps; do not change scene/activity selection.
- Keep renderer/UI consumption behind a reviewed adapter. Do not silently change `PixiArtAssetManifestV1`, `ArtAnimationPlanV1`, or bridge protocol. If new references are needed, propose a versioned addendum and stop at the FEAT-018 contract-review gate before implementing that boundary.
- Follow `assets/generated/` → visual review → `assets/approved/` → `assets/applied/`. Runtime uses approved/applied assets only. Decide SVG/PNG/WebP or mixed derivatives only after security, visual quality, load-time, and memory evidence are recorded in an ADR.

## Steps

1. **Inventory:** document loader capabilities, 20 pilot topics, coverage/licensing gaps, and contract boundaries; keep scope additive to FEAT-004/018.
2. **Catalog/profile design:** define manifest, ID/tag rules, style fields, resolver outcomes, fallback, size/dimension limits, and safe format policy; record architecture choices in an ADR before locking them.
3. **Author starter pack:** produce 60+ isolated assets under `assets/generated/` using ImageGen or sources with redistribution rights. Avoid trademarks/copyrighted characters, real child data, and unclear licenses. Record provenance and SHA-256 per asset.
4. **Review/publication:** check style, legibility, category, crop/anchor, license and provenance for every asset. Rejected assets remain non-runtime. Only reviewed items may move to approved/applied.
5. **Resolver/fixtures:** implement offline resolution and typed miss/fallback; cover all families and at least 10 synthetic long-tail prompts. No provider/network access from Pixi/mobile.
6. **Coverage/performance/handoff:** audit 20 themes, test deterministic resolution/source preservation, measure bundle/load/memory, document stable resolver IDs/API for later UI, and attach evidence.

## Acceptance criteria

- [ ] At least 60 individually addressable approved starter assets, with five or more per family; each runtime entry has stable ID/version, hash, category/tags, bounds/anchor, compatible style profile, provenance, and valid license/source.
- [ ] A catalog validator rejects duplicate IDs, missing/invalid hashes, malformed metadata, unapproved runtime entries, unsafe/out-of-budget assets, and incomplete provenance/license.
- [ ] Offline deterministic resolution maps known IDs/aliases to approved entries; identical catalog/profile input returns identical asset ID/version. No runtime web/provider lookup.
- [ ] At least 10 synthetic long-tail cases cover reuse, multi-part composition, and catalog-miss/authoring queue; no semantic claim silently changes the adult-confirmed topic.
- [ ] Each of the 20 FEAT-018 golden topics has a mapping or explicit source-only fallback; no activity/objective identity or frozen contract changes silently.
- [ ] Style adaptation harmonizes supplements without obscuring, replacing, or mutating the original; source IDs/version/hash stay traceable.
- [ ] Every asset has a visual review decision, origin/license or generator/prompt version/time, and SHA-256 before it enters approved/applied/runtime.
- [ ] Runtime works offline from approved local assets, has safe miss/fallback, and introduces no provider credentials, remote URLs, child-media upload, or unapproved generated reference into Pixi/mobile.
- [ ] Format, performance limits, and renderer/catalog adapter are verified against existing contracts or recorded in an approved ADR/contract addendum before integration.
- [ ] Feature-local evidence includes taxonomy coverage, validator/resolver tests, visual review sheets, source-preservation checks, and measured load/memory results with environment/limitations.

## Risks and mitigations

- **Unbounded themes:** 60 reusable assets plus semantic composition and a governed long-tail authoring path; unknowns retain the original and use typed fallback.
- **Style mismatch/source replacement:** local bounded style profile, separate supplement layers, synthetic visual fixtures; original remains immutable.
- **Rights/privacy:** reject unclear licenses; record per-asset lineage; synthetic data only; never put real child media in Git/evidence or send it externally.
- **Unsafe formats/performance:** constrain dimensions/bytes/vector features/texture count; lazy-load packs; measure actual bundle/load/memory before setting budgets.
- **Frozen-contract drift:** independent catalog boundary; reviewed, versioned addendum required before FEAT-018 runtime wiring.

## Verification plan

- Validate uniqueness, hashes, provenance/license, state gates, safe bounds, and malformed/missing topics.
- Test deterministic resolution across all 12 families, aliases/locales, 10 long-tail cases, and source-only fallback.
- Verify original source ID/version/hash is unchanged when supplements are added; test missing/corrupt/unapproved assets.
- Run Pixi typecheck/tests and contract/bridge compatibility checks; do not alter frozen versions without an approved addendum.
- Render visual QA sheets across representative source-style profiles; obtain owner visual approval before promotion.
- Benchmark representative pack size, load time, decoded memory and bundle impact; mark unsupported measures NOT_MEASURED.
- Run `python tools/validate_repository_security.py` before commit/push and repository validators where pre-existing blockers allow; record unrelated findings.

## Evidence plan

Store the inventory/gap matrix, catalog/license report, generation manifest/hash list, review decisions, test logs, source-preservation report, performance metrics, and UI handoff under this feature's `evidence/`. Use synthetic fixtures only; no real child media or credentials.

Implementation may proceed for this approved revision. Visual files remain individually gated: generate only under this feature's `assets/generated/`; do not reference/copy to approved/applied/runtime before a separate visual approval record.

## Revision 2 amendment — broader topic coverage and AI asset-selection context

This amendment expands and supersedes the starter-pack and resolver requirements above. The original child drawing and adult-confirmed topic remain authoritative. “All topics” is handled through broad reusable coverage plus a typed no-match/authoring path; no finite static pack claims exhaustive coverage.

### Added scope

- Add 12 flat-2D atlas packs (six isolated, individually addressable sprites each; 72 additional sprites, 144 total including the existing 72) for dinosaurs/prehistory, farm animals, wild animals, ocean life, insects/small creatures, music/instruments, sports/outdoor play, construction/tools, home/kitchen objects, clothing/accessories, science/technology, and celebrations/seasons/creative play. This is a broad common-topic tranche, not a guarantee that every possible child topic is pre-drawn.
- Publish a versioned AI-facing descriptor for every catalog sprite, including canonical EN/VI labels, localized aliases/synonyms, a concise visual description, semantic category/topic tags, visual role (subject/environment/prop/effect), intended use and composition, likely confusions/exclusions, style compatibility, atlas/frame bounds, provenance/hash/license, and review/runtime eligibility.
- Build a deterministic, offline top-K candidate-context builder from the adult-confirmed topic label/tags and approved catalog entries. The AI receives only the confirmed text and compact descriptions for eligible candidates—not the source image, free-form child data, or the full catalog. Its structured response may contain only candidate asset IDs; a backend validator rejects unknown, duplicate, unapproved, incompatible, or out-of-context IDs. Zero eligible/matching candidates yields a typed miss, preserves original child art, and creates an authoring-time queue item.
- Keep this selector internal to the backend/catalog boundary. Do not add fields to frozen FEAT-018 renderer/mobile/bridge contracts, change Gate A/B, add provider calls, or connect pending visuals to runtime. A later runtime integration requires a reviewed versioned contract addendum and separate visual approvals.
- Use transparent, deterministic metadata matching as the baseline. Embeddings/vector databases are out of scope unless a later ADR demonstrates a need.

### Added acceptance criteria

- [ ] Twelve additional topic atlases contain six distinct, crop-safe sprites each; full catalog has at least 144 stable sprite IDs and every entry has complete AI-facing descriptors and provenance.
- [ ] Catalog/schema validation rejects duplicate IDs, missing descriptions/tags/aliases/frame bounds, hash or provenance errors, invalid review state, and runtime exposure of any non-approved item.
- [ ] Candidate context is deterministic, bounded to top-K, localized for EN/VI, grounded only in adult-confirmed labels/tags, and filters to approved assets before creating the model-facing context.
- [ ] The prompt/output schema instructs the model to select only supplied IDs, not infer or alter the child's topic, and return a typed no-match when the candidates do not fit. Backend validation independently enforces the allowlist and review/style/role constraints.
- [ ] Synthetic tests cover exact labels, Vietnamese/English synonyms, ambiguous/confusable terms, compositional topics, unapproved-only matches, malicious/unknown IDs, duplicate picks, and long-tail no-match; no real child data or live provider call is needed.
- [ ] No changes are made to frozen FEAT-018 contract versions or Pixi/mobile runtime references. Existing and newly generated sprites remain REVIEW_PENDING until separate visual approval.

Revision 2 implementation scope is approved from the project owner's explicit follow-up request on 2026-09-17 to add broader topic assets and provide AI with asset information for correct topic-based selection. The exact boundary and safeguards above make that request executable; they do not approve any visual asset or contract change.
