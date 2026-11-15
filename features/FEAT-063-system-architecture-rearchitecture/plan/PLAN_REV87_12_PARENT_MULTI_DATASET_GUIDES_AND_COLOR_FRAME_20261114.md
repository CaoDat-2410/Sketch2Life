# Rev87.12 — Parent multi-dataset SVG guides and color reveal

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** APPROVED by the owner's direct request to connect the accepted guide sequence to Parent UI, add simple licensed SVG subjects from additional datasets, and show the original color illustration at the final step.<br>
**SRS authority:** FEAT-063 v2.7-draft; target requirements §§1–31 remain unchanged; §32 is append-only as-built evidence.

## Objective

Make the accepted source-path guide usable in the Parent drawing flow for several clear, child-friendly subjects, while retaining exact source geometry and a vivid color reference. The current chicken sequence is preserved. Add a small, curated Noto Emoji SVG pack and resolve supported Parent topics to the corresponding source-derived guide before any Qwen/Modal fallback. On the final guide step, keep the completed line drawing visible and show the original full-color source illustration in the same final screen.

This work does not turn the guide into the child's own artwork. The mandatory drawing capture still follows the optional guide. No profile, age, child image, voice or child identity is supplied to the guide source resolver.

## Dataset research and selection

1. **Arcadia Science Free Organism Illustration Library v1.0 — retain the current Gallus source.** It is CC0 and provides vector organism illustrations, but the library is intended for science communication and many drawings are detailed. Keep it for full-body organism references where the anatomy is clear; do not treat the library as a child stroke-order dataset. Preserve the already pinned source file and exact-path guide.
2. **Google Noto Emoji SVGs — add a small candidate pack.** The official repository provides color SVG resources and identifies the SVG artwork as Apache-2.0. The colored, cartoon-like assets are closer to the intended child experience and contain self-contained full-color source artwork. Select only entries that pass the local sanitizer, simple-path budget, recognizability and 4–8-stage review. Pin the upstream repository revision and every source-file SHA; include the SVG license text and visible source credits in product legal/about material.
3. **OpenMoji — evaluated, deferred.** It provides both color and black SVGs with a consistent, simplified style, but its graphics use CC BY-SA 4.0. Avoid adding ShareAlike-derived guide files to this first pack until product/legal confirms the intended distribution treatment.
4. **Twemoji — evaluated, deferred for the first implementation.** Its colorful artwork is suitable for children and SVG files are available, but graphics use CC BY 4.0 and require attribution. Noto is the lower-friction first source; keep Twemoji as a follow-on provider once the catalog's attribution surface is settled.

Candidate Noto subjects: butterfly (`U+1F98B`), turtle (`U+1F422`), chick (`U+1F425`), tropical fish (`U+1F420`), tulip (`U+1F337`), and red apple (`U+1F34E`). Do not include a candidate just to meet a count. The accepted initial pack is the subset that passes these gates after source download and render review:

- At most 32 source paths per asset; no unsupported SVG features after the existing sanitizer.
- Four to eight progressive stages, each adding a coherent recognizable part; every source path appears exactly once.
- At most six newly revealed paths in an ordinary stage; split a stage if necessary.
- The final line drawing is recognizable and the separate original-color image is clear at phone size.
- Preserve exact source path `d` data; do not generate replacement animal geometry or silently simplify the source.

## Implementation scope

### 1. Pinned source pack and resolver

- Download only the selected small SVG files and their official license from the upstream repositories; no whole-repository or whole-dataset vendoring.
- Add a manifest for each selected subject with upstream commit/tag, source URL, source SHA-256, license identifier/URL, normalized Vietnamese topic aliases, source path inventory, stage grouping and Vietnamese instructions.
- Preserve upstream SVG bytes. Store stage order separately; validate source hash, manifest hash, exact path identity, complete one-time assignment and stage/path limits at load time.
- Keep the current Arcadia V7 path unchanged. Add the Noto provider as a separate infrastructure adapter with a typed source-derived response. Do not label Noto output as AI-generated or dispatch Modal for a pinned subject.
- Unsupported topics continue through existing catalog/Qwen behavior; failures still do not block capture.

### 2. Parent UI

- Connect supported topics selected in the existing Parent topic/lesson flow to the source-derived guide response, with the optional guide switch and capture skip behavior unchanged.
- Render earlier paths as completed, the current stage as a progressive line, and future paths hidden.
- On the final step, show the completed line image and the original full-color source image together on the same screen. Keep the line image visible; do not put the colored illustration underneath the drawing steps. Include short Vietnamese labels and source credit where required.
- Reset stage state when topic/guide changes and preserve the current source-color toggle only where it does not hide the final color panel.

### 3. Governance and provenance

- Keep all imported sources under `deployment/modal/srs_v23/data/` with source files, license, provenance manifest and integrity hashes.
- Record the choice of provider and all candidates that failed curation; do not auto-publish assets or create educator/curator approvals.
- Add a feature evidence folder containing real route responses, rendered stages, final-color screen/render, hashes, source attribution, checks and precise limits.
- Append as-built details to SRS §32 and update FEAT-063 context, decisions, source register, evidence index and status. Do not modify target requirements §§1–31.

## Acceptance criteria

- [ ] At least three non-chicken Noto subjects pass the agreed path budget and are reachable through the real Parent route; each is an actual upstream SVG, not a fixture or newly generated substitute.
- [ ] Source/license/revision/hash provenance is retained, and license text/required attribution is present.
- [ ] Every imported source is sanitized; tests prove path hashes/IDs match the pinned source, all paths appear once, and each guide has 4–8 valid ordered stages within the path budget.
- [ ] The Parent flow resolves pinned sources before the AI fallback, renders strokes progressively, keeps capture optional-guide behavior nonblocking, and never sends child information to this source resolver.
- [ ] Final-step UI shows both the completed line guide and the original full-color illustration without obscuring the line guide.
- [ ] Visual review confirms each selected image is recognizable, comfortably simple for a 3–10 age range, and distinguishable from the prior child-drawing-like output.
- [ ] SRS §§1–31 are byte-for-byte unchanged by this plan's SRS update; §32 and feature records accurately distinguish local route checks from Android/Firebase E2E.

## Non-goals and limits

- No video generation, FLUX, AI generation for pinned guide geometry, Modal deployment/inference, model training, full Noto/Twemoji/OpenMoji import, or public catalog publication.
- No database migration, account/consent/profile/seed changes, child data, `.env` or secret changes, or shared-service restart.
- No commit, push or merge.
- A focused local route/render result is not Android/Firebase E2E. Full end-to-end verification is reported only if it is explicitly performed.

## Sources reviewed

- Arcadia Science, Free Organism Illustration Library v1.0: https://zenodo.org/records/17203578
- Noto Emoji repository and SVG license: https://github.com/googlefonts/noto-emoji and https://github.com/googlefonts/noto-emoji/blob/main/svg/LICENSE
- OpenMoji repository/license: https://github.com/hfg-gmuend/openmoji
- Twemoji repository/license: https://github.com/twitter/twemoji
