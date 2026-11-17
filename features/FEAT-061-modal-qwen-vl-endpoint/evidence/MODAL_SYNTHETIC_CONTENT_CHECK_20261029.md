# Owner-authorized single synthetic content check

## Scope and execution

- On 2026-10-29, the owner asked what to do after the successful smoke and historical metrics. The next suggested check was to inspect the returned content for the existing house-and-sun synthetic fixture. The owner explicitly requested the startup command for their own PowerShell and instructed the assistant to run the test. This authorizes this bounded single synthetic request, without changing the protected original plan or approval record.
- The owner started the temporary Modal App and supplied `Serving...` for session `ap-7wtOFNdf80UNiggfJMYVpb`. The assistant sent exactly one POST to its `/v2/vision` route. The existing encrypted Bearer backup was read locally and passed to the temporary process through stdin; no credential value, raw response body, or secret file was printed or persisted in this evidence. The temporary probe file was deleted after execution.
- The synthetic input is the pre-existing geometric house-and-sun fixture; source SHA-256 `504a0d0c03a4183f25608138bf8dc46a6779155b4fa5015e9c4e89ce10103f89`. The probe verified source hash/base64, admission-artifact hash and `ADMITTED`, then used the existing PASS receipt. The old FEAT-048 artifact references were preserved unchanged. No real child data was used.

## Result

- HTTP 200; typed `VisionUnderstandingResultV2` status `SUCCEEDED`; policy execution `PASSED`; attempt 1; repair flag true; client wall time 24.386 s. Correlation ID `modal-synthetic-content-4581024d0d34`.
- The response passed schema, request correlation/source, profile/catalog, pinned model/revision, config/adapter and single-attempt checks. Model `Qwen/Qwen3-VL-8B-Instruct`, revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`.
- The validated response contained one entity, zero actions, zero themes, zero relations and zero ambiguous regions. The selected typed entity was presented transiently to the owner. Comparing it with the visible synthetic fixture, the assistant observed that it matched the house but did not explicitly identify the sun in the entity list. No raw response or predicted text is stored in this evidence.
- This is a single manual observation, not a benchmark, quality pass, generalization claim or comparison against Lightning L4. Model confidence is not an independently verified probability. FEAT-003 quality and production-readiness status remain unchanged.
- The owner subsequently supplied the serve shutdown output: at `2026-10-29T12:25:50+0700` a client heartbeat encountered `ConflictError: App state is APP_STATE_STOPPED`, followed by disconnect and `App aborted` for this same App. This confirms session shutdown. The output establishes that the App was already stopped when that heartbeat arrived; it does not establish who or what first stopped it. No retry or new request followed, and this lifecycle message does not negate the earlier validated successful response.
- GPU peak memory, billed duration and cost specific to this request were not measured.
