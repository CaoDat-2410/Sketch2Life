# EV-063-95 — Teacher SVG dataset-conditioned quality attempt

**Date:** 2026-11-13<br>
**Outcome:** FAILED before Qwen inference; no quality comparison is available.<br>
**Plan:** Rev85, SHA-256 F9F9399E197F4D5079D8E27FD32C36C6274626EE0831DE346F32E263FE6AB9C0.

## Dataset integration recorded

- Dataset: yoavf/svg-animal-illustrations, immutable revision d7ab3149308746a4b17e7cbee30f1f054f6c49df.
- The dataset card declares CC0-1.0; this is not an independent legal audit.
- The six-record source snapshot SHA-256 is 62E79601CF0E8709B71D7BCAFD323B09A9AED91F1304BF049091015C36660FEF.
- The three-record reference pack SHA-256 is C0E47DEB4ADEBB0ED2C7AA21A49955D20976F9F0A9C7F1B933FB3B779AC63A49; worker source SHA-256 at this observation is 0E429FE7F2C7E71DFCB4F9753773D549679C5790F612A8AE60747305F7EC331C.
- The pack contains dog/quadruped, cat/feline, and rabbit/lagomorph examples. Retrieval is intended to select no more than one local structural example; it does not copy an exemplar as the generated answer.

## Real UI/API attempt

- Used the existing local synthetic Teacher identity and the authenticated Teacher UI route. Input was the approved non-personal topic con hươu sao, age 60 months, style warm_storybook.
- Exactly one UI-triggered request was made. The API returned HTTP 502 with MODAL_WORKER_FAILED_TERMINAL, request ID 37bdb1ee-24a1-4de2-866b-8051acf77143. The response body is preserved in generated-svg-draft.json (SHA-256 29B07551119D2EDAE2181C050DE22CE5410A1B2139F67E0FA0FCD9DC10761FDD).
- Worker diagnostics place the failure in phase dataset_reference_selection: _select_teacher_svg_illustration_reference → _load_teacher_svg_illustration_reference_pack → _parse_teacher_svg_illustration. The parser raised MODAL_SVG_ILLUSTRATION_PATH_INVALID, wrapped as MODAL_SVG_REFERENCE_EXAMPLE_INVALID.
- Root cause: the loader validates every record in the reference pack before returning the selected quadruped example. The unrelated cat example prompet-sample-cat, path-026, has stroke_width=20; the unchanged worker schema/parser only permits values 1 through 12. Thus the full pack is rejected before the deer request can use its valid quadruped reference.
- The Qwen request did not reach model loading or inference. This was not a Qwen JSON-parser failure, model timeout, or SVG output quality-gate rejection. The request wall-clock duration and exact Modal credit charge were not preserved in the evidence, so neither is claimed here.
- No SVG response, PNG render, or generated-artifact screenshot exists. The saved JSON is an error response, not a generated SVG. The comparison against EV-063-94 therefore could not be performed, and no quality improvement is established.

## Runtime and cleanup boundary

- The single CPU Modal /health call returned HTTP 200 in 6.323 seconds and reported no GPU allocation or inference for that health call; the pinned Qwen3.5-9B revision was reported ready.
- The local API container rev79-parent-local-20261112-api-1 was healthy at the final Docker inspection. The local SVG generation flag was restored to false. The Teacher Vite process and browser session used for this attempt were closed.
- The shared Modal app remains deployed with min_containers=0; it was not stopped. A post-run modal container list query did not return within 30 seconds and was interrupted, so scale-to-zero was not independently confirmed in this observation.
- No test suite, retry, video request, .env edit, database reset, commit, or push was performed.

## Required correction before another live attempt

A new approved amendment is required because Rev85's single inference allowance was consumed and its failure rule prohibits retries. The bounded correction should remove the invalid cat exemplar from the active reference pack while preserving its raw source snapshot and documenting it as excluded, recompute the manifest/pack hashes and worker pin, and add a static pre-deploy validation that runs the same parser over every packaged exemplar. Only after a new plan/approval should the app be redeployed and one fresh real UI comparison be attempted. Do not relax the 1–12 stroke-width contract to accommodate the source sample.
