# FEAT-025 implementation plan — architecture boundary and workflow polish

## 1. Approved objective

Refactor the backend workflow so the application layer depends only on
application ports and versioned contracts, then add focused polish and
regression coverage while preserving the current real-AI behavior.

## 2. Scope

### 2.1 Dependency-direction fix

1. Add application-owned ports/protocols for the dependencies currently
   created inside `BackendAiWorkflow`:
   - media validation;
   - P1 template library access;
   - V1 semantic catalog access;
   - V2 semantic catalog access;
   - Pixi asset resolution and preflight;
   - curated catalog lookups used by material and duration helpers.
2. Keep the protocols expressed in terms of existing contracts or small
   application-neutral value objects; do not import infrastructure classes
   into `application`.
3. Change `BackendAiWorkflow` to receive those dependencies through its
   constructor. It must not call infrastructure loaders, read catalog files,
   or construct a file inspector.
4. Move all concrete construction and loader error translation to the CLI
   composition root (`interfaces/cli/workflow_demo.py`) or a dedicated
   infrastructure composition module called by that root.
5. Preserve an explicit catalog-preflight failure path with the existing
   typed terminal status/reason code. Loader failures must not become generic
   uncaught exceptions.
6. Keep provider adapters in infrastructure and injected through the existing
   ASR/VLM ports.

### 2.2 Workflow polish

1. Centralize workflow dependency construction in one named composition
   function so the Lightning entrypoint has one auditable setup path.
2. Replace broad infrastructure-specific type annotations in the application
   service with application port types and typed contract/value objects.
3. Make the injected dependency bundle immutable and explicit; avoid hidden
   defaults that reintroduce infrastructure imports.
4. Keep legacy V1 projection and V2 continuity/bridge output byte/schema
   compatible unless a test demonstrates an approved additive correction.
5. Preserve sanitized debug evidence only behind the existing opt-in flag;
   do not log prompts, raw model output, tokens, credentials, or child data.
6. Improve failure diagnostics at the composition boundary so missing model,
   catalog, asset, or media dependencies report a stable typed reason without
   masking the underlying class in local evidence.

### 2.3 Test and evidence polish

1. Add application unit tests using in-memory fakes for every new port.
2. Add a test that imports the application package and verifies no application
   source contains `sketch2life.infrastructure` or `sketch2life.interfaces`.
3. Add composition-root tests proving the real CLI builds all dependencies and
   that an injected catalog preflight failure returns the existing terminal
   manifest path.
4. Re-run FEAT-024 targeted tests and the broader unit suite, documenting the
   two known pre-existing deterministic/provenance baseline failures if they
   remain unchanged.
5. Run compile, harness, architecture, security, and diff checks.
6. Store command outputs and a short implementation note under this feature's
   `evidence/` directory.

### 2.4 3D scope gate

No 3D code or generated visual asset is part of the implementation until the
user confirms which of the following is intended:

- “thiếu 3D”: add a future 3D/Pixi-compatible asset/runtime workstream;
- “Hiếu 3D”: a named teammate/requirement to document or assign;
- another specific polish item.

If the user confirms actual 3D work, it will be planned separately with its
own asset provenance, runtime boundary, acceptance criteria, and visual gate;
it will not be smuggled into this architecture fix.

## 3. Acceptance criteria

- `python tools/validate_architecture.py` prints `ARCHITECTURE_VALID`.
- `python tools/validate_harness.py` prints `HARNESS_VALID`.
- `python tools/validate_repository_security.py` prints
  `REPOSITORY_SECURITY_VALID`.
- The real CLI composition root can still construct the workflow with the
  local ASR/VLM adapters and pinned catalog/asset sources.
- Existing V1/V2 workflow tests pass, including case-02 resilience,
  continuity, age eligibility, bridge, and debug-evidence behavior.
- No application module imports `sketch2life.infrastructure` or
  `sketch2life.interfaces`.
- No raw AI output, prompt, credential, or real child data is added to source
  or evidence.
- The feature remains clearly marked as pending Lightning smoke if GPU/model
  execution is not available locally.

## 4. Implementation order

1. Confirm approval and clarify the 3D phrase.
2. Add ports/value objects and tests first.
3. Move composition/loaders to the interface/infrastructure boundary.
4. Refactor `BackendAiWorkflow` and helpers to consume injected ports.
5. Run focused tests and fix regressions.
6. Run architecture, harness, security, compile, and broader tests.
7. Record evidence and update context/status/decisions.

## 5. Explicit non-goals

- no mobile UI changes;
- no video generation;
- no model/provider replacement;
- no catalog expansion;
- no 3D engine, GLTF/GLB asset, or generated 3D artwork before clarification.
