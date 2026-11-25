# Plan Rev15 — reload the edited Modal environment and retry Parent flow

## Objective

Apply the owner's newly edited root `.env` to the isolated FEAT-085 API container, then retry the current synthetic Parent butterfly flow through Android UI to see whether the Modal pre-call rejection is resolved.

## Approved scope

1. Compare only whether the container's Modal token ID/secret match the root `.env`; never print either value.
2. Recreate only Compose service `api` in project `fe085-parent-api`, leaving Postgres, Redis, ClamAV, MinIO, data volumes, and other stacks untouched.
3. Verify API health and that the re-created container now matches the root `.env` without exposing values.
4. Continue the existing authenticated synthetic Parent run from Android UI with the already attached butterfly drawing. Submit one UI action only. The backend's existing two bounded `Function.spawn` attempts remain part of that one action.
5. If Modal returns a call ID, poll that exact call. Under the earlier approved real-E2E scope, continue the same run through activities, story review, and video only if each prior stage succeeds and all current gates pass. Do not retry any accepted or ambiguous call.
6. If the UI request is rejected before a call ID, stop further inference and report the safe cause. No request is sent directly to a Modal worker.

## Preserved constraints

- Use only synthetic child-style drawings and the real Parent Android UI/API/Modal path; no fixtures.
- Keep auth, consent, upload scanning, schema, quality/safety, activity selection, script review, quota/admission, and video safety gates enabled. Do not edit DB records directly or bypass quota.
- Do not modify Docker files, Modal deployments, GPU/container limits, payment settings, credentials, or unrelated services as part of diagnosis.
- No Computer Use, no secrets in logs/evidence, no commit, no push.

## Acceptance evidence

- The running API container is confirmed to have been recreated and to match the root `.env` for the two Modal credential keys, using boolean results only.
- API health passes.
- Record the one UI request's Modal call ID or typed pre-call rejection, timings, UI result, and downstream stage outcomes.
- Update `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md` and FEAT-085 status/context.
