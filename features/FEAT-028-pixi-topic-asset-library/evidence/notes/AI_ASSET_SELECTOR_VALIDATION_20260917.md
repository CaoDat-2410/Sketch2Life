# FEAT-028 internal AI asset-selector validation

- Evidence ID: EV-028-AI-01
- Plan revision/hash: 2 / SHA-256 D943333F8B268D7B8B1E87556677F867A445D73C5C87717C2F8C2F05CC62CCBA
- Date: 2026-09-17 (Asia/Saigon)
- Branch: codex/feat-018-contract-plan
- Internal prompt protocol: fe028-topic-asset-ranker-v1
- Prompt SHA-256: c0b46a1409798e8e1d8b8f2ca22077a2a804ebda0e970c764d654d5b05dbba84

## Commands and results

Run from backend/:

- .venv/Scripts/python.exe -m pytest tests/unit/test_pixi_topic_asset_candidates.py -q -p no:cacheprovider — PASS, 16 tests.
- .venv/Scripts/ruff.exe check src/sketch2life/contracts/schemas/pixi_topic_asset_selection.py src/sketch2life/application/services/pixi_topic_asset_candidates.py src/sketch2life/infrastructure/ai/pixi_topic_asset_prompt.py tests/unit/test_pixi_topic_asset_candidates.py — PASS.
- .venv/Scripts/python.exe -m mypy src/sketch2life/contracts/schemas/pixi_topic_asset_selection.py src/sketch2life/application/services/pixi_topic_asset_candidates.py src/sketch2life/infrastructure/ai/pixi_topic_asset_prompt.py --follow-imports=silent — PASS, no issues.

Tests cover catalog integrity, approved/rights-cleared gating, exact Vietnamese aliases, deterministic top-K, composition from multiple adult-confirmed labels, confusable cues, role/style filtering, Gate-A blocking, long-tail typed miss, media-free authoring proposal, malformed/duplicate/unknown model IDs, prompt minimization, and rejection of media-reference fields.

## Boundary and limitations

- The selection context is built only after an adult-confirmed topic and includes bounded labels, aliases, descriptions, tags, role, and confusable cues for eligible local entries. It does not include an image, path, hash, or frame geometry.
- Output parsing accepts only supplied candidate IDs; backend validation independently checks the shortlist, review status, and runtime eligibility. A no-match returns a typed authoring proposal that preserves original art and includes no child media or generation request.
- All repository visuals are currently pending review, so the real catalog correctly returns NO_APPROVED_ASSETS. Approved records used in tests are synthetic in-memory test states; no repository review status was changed.
- This revision implements the context/prompt and validator, not a live provider call. The new contract is backend-internal; no FEAT-018 public contract, mobile/Pixi code, or provider runtime was changed.

## Repository-wide checks

- tools/validate_harness.py --feature features/FEAT-028-pixi-topic-asset-library reports no FEAT-028 missing paths, but remains globally invalid because the pre-existing untracked FEAT-026 folder lacks evidence/raw and evidence/metrics. That folder was preserved.
- tools/validate_repository_security.py reports only the pre-existing untracked FEAT-026 external SRS PDF as publishable. An initial false positive on this selector's regex constant was fixed by renaming it; the selector is no longer reported. The FEAT-026 file was not altered.
