# Plan Rev87.11 — Arcadia-derived Parent SVG stroke guide

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** APPROVED by the owner's direct instruction: “đúng rồi, đi theo hướng đó đi, fix đi, nào chạy ra svg đc từ đó thì tính”.<br>
**Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned. Product targets in §§1–31 remain unchanged; §32 may receive implementation evidence only.

## 1. Problem and objective

The Parent `POST /api/parent/v1/ai/sketch-guides` path sends even the supported chicken topic to Qwen3.5 and asks it to invent SVG geometry. Repeated requests completed inference but failed the strict chicken anatomy gate. Raising the timeout cannot repair this geometry failure.

For the pinned Arcadia `Gallus gallus` source, build a deterministic, source-derived guide from the checked-in CC0 source and a separately versioned, human-authored stroke derivation. Return a real sanitized SVG draft through the Parent API and render it in the existing optional Parent guide screen. Keep Qwen as the existing fallback for unsupported topics. Do not create synthetic provider metadata, weaken any quality/safety gate, or make an AI call for the supported source-derived topic.

## 2. Product and technical boundaries

- Supported source-derived aliases are exactly the pinned manifest's Vietnamese/English chicken topics. No other animal/object may receive the chicken derivation.
- The original Arcadia SVG and its provenance file are immutable inputs. The derivation is a distinct, versioned artifact with exact source SHA-256, source element lineage, and a trace/simplification description. Do not return or directly copy the multicolor reference paths as the child guide.
- The returned guide remains private, ephemeral `DRAFT`, `review_required=true`, `persisted=false`; it contains no child profile, age, image, voice, account/run identifier, or other child data.
- Use 4–8 progressively revealed stages and at least 8 distinct open line paths for the chicken drawing. Preserve the existing sanitizer, schema limits, coverage rules, source/topic checks, and chicken anatomy/topology gate. The derivation validator is additive and may be stricter; no existing AI gate is relaxed.
- Use a truthful versioned Parent response contract for source-derived output. It must identify the derivation engine and source lineage, and must not claim a Modal call or Qwen model. Keep the Teacher response contract and worker path unchanged.
- If a topic has no pinned source derivation, follow the existing Modal/Qwen route and its current hard gates unchanged.
- Package the pinned source and derivation in the backend Docker image from the canonical repository data directory. Do not add environment variables, credentials, database rows, migrations, accounts, or seeds.
- No Modal deploy, warmup, GPU request, video request, shared-service restart, or mutation of `.env` is part of this plan.

## 3. Implementation work

1. Add a versioned source-derived guide manifest adjacent to the existing Arcadia source. Pin the source hash, supported topic aliases, derivation algorithm/revision, per-path source lineage, 4–8 stage order, Vietnamese drawing prompts, and only new open SVG path geometry. Keep the Arcadia source manifest unchanged.
2. Add a deterministic backend adapter that reads the real pinned source and derivation manifest, verifies both hashes and lineage references, constructs the SVG document/guide, sanitizes and canonicalizes the result, and applies the existing topic-guide validator including chicken topology before returning it.
3. Add a Parent-only derived-draft response schema with explicit source/engine provenance. Dispatch supported aliases to this adapter before the Modal call. Unsupported topics continue through the current Qwen path. Preserve the current feature flag, Parent authorization, local/dev policy, and PII/remote-reference rejection.
4. Extend the Parent mobile domain/API types to accept both truthful response variants. Keep the shared progressive SVG renderer and make the screen identify a source-derived draft distinctly from an AI-generated draft while retaining adult review and skip/capture behavior.
5. Copy the canonical Arcadia data directory into the backend Docker image and amend `.dockerignore` to allow only this dataset directory into the build context. Preserve one source of truth in the repository; do not add environment variables, credentials, database rows, migrations, accounts, or seeds.
6. Add focused regression coverage for source hash/topic/lineage failures, valid progressive output, anatomy/sanitizer enforcement, Parent route dispatch without Modal for supported aliases, unchanged Modal fallback for other topics, and mobile response/render compatibility.
7. Run focused backend and mobile checks, generate one actual SVG response/artifact from the pinned source-derived adapter, verify its document hash and stage/path counts, and render/inspect it with an available SVG renderer. Record exact commands/results and any renderer limitation in feature-owned evidence.
8. Update FEAT-063 context, decisions, source register, status, evidence index, and only SRS §32 with as-built evidence. Do not change target requirements in §§1–31.

## 4. Files in scope

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11_ARCADIA_DERIVED_PARENT_SVG_GUIDE_20261114.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `.dockerignore` (allowlist only the pinned Arcadia source directory)
- `deployment/modal/srs_v23/data/arcadia_organism_strokes/arcadia-gallus-derived-guide-v1.json`
- `backend/Dockerfile`
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py` (new)
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/tests/unit/` focused source-derived guide tests (new)
- `backend/tests/contract/` focused Parent endpoint dispatch tests (new)
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
- `apps/ui-mobile/tests/` focused response compatibility test (new or existing focused file)
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-102_ARCADIA_PARENT_SOURCE_DERIVED_GUIDE_20261114/` (new; real output and report)
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (§32 only)
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

No other repository path may change under Rev87.11. If implementation requires an additional path, stop and amend the plan and approval hash first.

## 5. Acceptance criteria

- The exact source file SHA-256 matches the pinned Arcadia source manifest; derivation manifest records the same hash and references only existing source elements.
- A supported chicken-topic Parent request returns the new source-derived response contract with a sanitized `SvgDocumentV1`, 4–8 progressive stages, 8–64 unique visible paths, exact per-stage/path coverage, valid lineage, and all existing chicken anatomy checks passing. `modal_call_id` and `model` are absent from this contract.
- The actual returned SVG can be rendered by the app's SVG renderer; its saved evidence artifact matches the response digest. It visibly reads as a chicken and reveals new dashed strokes in order while previous strokes remain solid.
- A supported topic does not call Modal. An unsupported topic still uses the pre-existing Modal path and V1 contract; existing strict behavior is unchanged.
- Parent UI accepts both response contracts, accurately labels the source-derived draft, and keeps adult review/skip/capture progression. Teacher contract and presentation behavior remain unchanged.
- Focused tests and static checks pass. No AI/GPU, video, fixture response, database migration, credentials, child data, or shared-service restart is used.
- SRS §§1–31 are unchanged; §32 and FEAT-063 implementation records describe the result without claiming educator approval, publication readiness, or formal SRS sign-off.

## 6. Risks and limits

- The Arcadia source is an anatomy reference, not a stroke-order dataset. The derived paths and teaching sequence therefore need later educator review before catalog approval/publication; this implementation produces a private draft only.
- This first source-specific derivation covers chicken only. Other topics retain the existing Qwen path and may still fail its quality gates until their own reviewed sources/derivations exist.
- Rendering/performance thresholds from Rev68 remain separate acceptance gates; focused functional rendering does not establish the full M3 performance or educator-quality thresholds.
