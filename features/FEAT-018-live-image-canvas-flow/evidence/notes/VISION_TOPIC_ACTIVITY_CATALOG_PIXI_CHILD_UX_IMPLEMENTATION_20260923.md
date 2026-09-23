# Vision/topic/activity catalog, Pixi and child UX implementation evidence

Date: 2026-09-23
Feature: `FEAT-018-live-image-canvas-flow`
Branch: `codex/feat-018-contract-plan`
Plan: `plan/VISION_TOPIC_ACTIVITY_CATALOG_PIXI_CHILD_UX_PLAN.md`

## Scope completed

- Loaded the curated V2 semantic catalog in the real HTTP composition root.
- Added an additive, backend-owned recommendation read model capped at three prioritized cards.
- Required every displayed activity to pass semantic continuity and the existing strict P1 fit path.
- Revalidated the exact adult-selected card before downstream ExperienceSpec/Gate B work.
- Localized and deduplicated topic claims, including `bird`, `branch`, `leaf`, `perching` and
  `bird on branch`, without overwriting raw provenance.
- Added one shared bounded Qwen quality-repair path; schema repair and semantic-quality repair
  cannot stack and the request remains capped at two generations.
- Replaced normal BaoVC inline technical errors with a friendly recovery modal and shortened
  child-facing copy. Activity cards/detail use Vietnamese titles, reasons and material labels.
- Fixed Pixi payload serialization so optional values are omitted instead of sent as `null`; the
  original image remains the recovery surface when the renderer cannot start.

## Verification

Executed without Lightning, Qwen provider, ASR provider, video generation or external network:

```text
backend/.venv/Scripts/python.exe -m pytest \
  backend/tests/unit/test_qwen_vision_adapter.py \
  backend/tests/unit/test_lightning_vision_v2_server.py \
  backend/tests/unit/test_topic_activity_matching.py \
  backend/tests/contract/test_live_image_demo_api.py -q
76 passed

npx tsc --noEmit                         PASS
packages/art-renderer: npm test         8 passed
tools/validate_repository_security.py   REPOSITORY_SECURITY_VALID
tools/validate_architecture.py          ARCHITECTURE_VALID
git diff --check                         PASS
```

The owner still performs the final Android emulator/live Lightning smoke under the approved
approximately 25-credit ceiling. No provider request was triggered by Codex.

## Preserved boundaries

Image remains required; narration can be audio, typed text or absent. Gate A/Gate B stay adult
controlled. Runtime state remains process-local, with the existing adapter seams for future auth
and durable save. Video remains out of scope. Unrelated FEAT-026 files were not modified.

## Final acceptance-gap closure

The follow-up review found and closed the remaining in-scope demo gaps:

- normal workflow notices and actions no longer expose backend/provider/Gate/ExperienceSpec/Pixi
  terminology;
- global and renderer error modals now offer bounded recovery actions;
- a renderer failure keeps the selected original drawing visible and can remount the WebView on an
  explicit retry;
- safety and caregiver guidance are collapsed under `Dành cho người lớn`;
- narration and feedback inputs use keyboard avoidance, primary controls meet the 48px target, and
  critical selection/rating controls expose accessibility roles, labels and selected state;
- feedback starts with unrated scores, removes the remaining English label, and no longer claims
  durable profile persistence;
- a non-primary reviewed activity selection is contract-tested without a second Vision call;
- the TypeScript renderer schema now tests the exact source-only launch shape with omitted optional
  values and rejects a `null` optional field;
- the bird/branch/leaf/perching regression now verifies Vietnamese localization, canonical leaf
  deduplication and a complete Vietnamese topic.

Final offline verification:

```text
focused backend unit/contract suite       PASS (77 tests)
full backend test collection              PASS to 100% (configured skips only)
mobile TypeScript                         PASS
mobile UI copy/recovery guard             UI_COPY_AND_RECOVERY_VALID
art-renderer tests                         PASS (9 tests)
art-renderer TypeScript                    PASS
Ruff / changed backend modules            PASS
Mypy / changed backend services           PASS
architecture validator                     ARCHITECTURE_VALID
repository security validator              REPOSITORY_SECURITY_VALID
git diff --check                           PASS
```

`validate_harness.py` continues to report only the pre-existing, unrelated FEAT-026 missing
`evidence/raw` and `evidence/metrics` paths. FEAT-026 remains untouched.

## Local runtime restart and Android smoke

- Declared `expo-asset` as a direct mobile dependency because Metro cannot rely on the package's
  previous transitive installation; the lockfile was updated offline.
- Restarted the local API on `127.0.0.1:8000`; `/health` returned
  `{"status":"ok","service":"sketch2life-api"}`.
- Restarted Expo Metro on port `8081`, restored ADB reverse mappings for ports `8000` and `8081`,
  and relaunched `com.sketch2life.mobile/.MainActivity` on the Android emulator.
- Metro rebuilt and produced an Android bundle with 968 modules. The emulator reached onboarding,
  dashboard and image/text-narration capture; the text input retained the intended layout while
  focused.
- The final Android log scan contained no fatal exception, React Native JavaScript error, missing
  bundle error, `TypeError` or `ReferenceError`.

This smoke did not submit a live Lightning/Qwen request and therefore consumed no provider credit.
