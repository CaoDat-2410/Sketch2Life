# Backend dev setup — owner report, 2026-10-29

## Evidence boundary

This sanitized progress record begins with the owner's instructions and terminal output supplied in chat, followed by the separately authorized bounded backend smoke check. Its successful result is recorded in `BACKEND_DEMO_MODAL_SMOKE_20261029.md`; it is not a wider app or quality acceptance. No raw terminal log, credential, actual `.env` value, or machine-specific absolute path is retained.

The existing [backend compatibility review](BACKEND_MODAL_COMPATIBILITY_REVIEW_20261029.md) remains the source-level assessment. The original Modal configuration stays in the original checkout; backend preparation uses a separate dev-based worktree rather than replacing either backend tree.

## Confirmed owner-reported preparation

- Created `.worktrees/modal-vision-dev` on branch `feature/modal-vision-dev` from `origin/dev` at `529cbef9` and entered that worktree.
- Created a separate backend virtual environment. The owner's version output confirmed Python 3.12 and pip 25.0.1.
- The initial editable backend installation with extras `[dev,image-admission]` failed with a network `ReadTimeout` while downloading mypy. This was an installation failure, not an application or model failure.
- A subsequent installation using `--timeout 120 --retries 10` reported successful installation. Selected reported versions were `sketch2life-backend 0.0.0`, `av 18.1.0`, `fastapi 0.162.0`, and `uvicorn 0.54.0`.
- The owner's subsequent `pip check` returned `No broken requirements found`.
- The owner's CPU import check successfully imported `av`, `Feat018ImageAdmission`, and `AvImageDecoder`, returning `IMAGE_ADMISSION_IMPORT_OK` and `av=18.1.0`.
- Owner step 8 executed `WriteAllText` to create the backend token file outside the repository from the DPAPI-protected CLIXML backup, using UTF-8 without a BOM, and returned without reported errors. The assistant did not read or print the credential value.
- Owner step 9 assigned backend settings in the same PowerShell process and returned `BACKEND_MODAL_ENV_READY`: local environment, development auth, existing `lightning_dev` adapter, the selected Modal base URL, token-file path, `/v2/vision`, a 120-second provider timeout, and disabled SAM/planner/whiteboard/video options. This marker confirms the reported assignment step, not backend startup or provider reachability.

Dependency consistency and these CPU imports are confirmed by the supplied output. Those preparation checks alone did not establish startup, admission or provider connectivity; the later bounded run below supplies separate evidence for those steps.

## Branch-picker observation

The dev-based test branch automatically tracks `origin/dev`. GitHub Desktop's [remote/local branch merge logic](https://github.com/desktop/desktop/blob/development/app/src/lib/stores/git-store.ts#L388-L426) keeps local branches and filters out a remote branch already represented by a local branch's upstream. This explains why `origin/dev` can be present in Git and on GitHub while a separate `dev` entry is absent from the picker.

The owner was guided to remove the test branch's upstream with `--unset-upstream`. A later assistant read-only `git for-each-ref` returned an empty upstream for `feature/modal-vision-dev`, independently confirming that link is now absent. No subsequent Desktop screenshot was inspected, so visual picker recovery is not claimed. The remote `dev` branch was not deleted or renamed.

## Current runtime state and pending checks

- The owner subsequently supplied `Application startup complete` for `sketch2life.demo_main:app`, PID 44944, on loopback port 8001. The assistant verified the required OpenAPI routes, created one synthetic session and uploaded the existing combined crayon source. Its actual `ImageAdmissionReceiptV2` returned `ADMITTED`, version 1.
- Earlier metadata-only local checks confirmed the encrypted CLIXML backup existed and the proposed token file and test worktree's `.env` and `backend/.env` were absent before those owner steps. Their contents were not read. The later steps used the outside-repository token file and process environment; no `.env` creation is reported.
- The owner listed the prior Modal App as stopped with zero tasks, resolving that earlier serving-state uncertainty. The owner then started App `ap-PMAK4LcJOs8qXnndTL0Fwr` with the existing configuration and supplied its expected function URL.
- After a read-only session preflight, the assistant sent exactly one backend understanding request, narration NONE. HTTP 200, outer and nested `SUCCEEDED`, client wall 23.938 s, four entities, provider attempt 1, repair true, observed session version 2 and Gate A ready. Source/correlation and pinned profile/model/config checks passed. See `BACKEND_DEMO_MODAL_SMOKE_20261029.md` and its linked metadata records.
- No retry, Gate A confirmation, later AI route or mobile test was performed. The run's durable one-request reservation remains consumed. The owner supplied successful Modal server logs (23.0 s HTTP duration / 19.5 s execution) and `App aborted`, then `Application shutdown complete` and `Finished server process [44944]` from the backend. Both tested processes are confirmed stopped; this bounded run and cleanup are complete.

Earlier preparation documentation did not itself start a provider. The subsequent assistant HTTP test and owner-started Modal session are explicitly distinguished above. Protected original plan/approval, runtime source and production provider policy remain unchanged. No commit or push was performed.
