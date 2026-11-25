# Plan Rev16 — fresh Parent retry after environment reload

## Objective

Test whether the newly loaded Modal credentials resolve the Parent drawing-dispatch rejection, using a fresh synthetic Parent run through the Android UI.

## Why a fresh run is necessary

After the API container was recreated and health passed, the emulator showed the previous run in a terminal drawing-failure state with only normal “close” and “close and start again” lifecycle actions. It does not permit another analysis on that run. The synthetic butterfly image has already been preserved in this feature's evidence folder.

## Scope

1. Use the authenticated app's normal “close and start again” action for the terminal synthetic run. Do not edit DB state directly.
2. Create one new synthetic Parent topic run, select the existing insect/butterfly path, and attach the preserved synthetic crayon butterfly via Android image picker.
3. Send one UI drawing-analysis action only. The backend's existing two bounded `Function.spawn` attempts count as the one action.
4. If accepted, poll that exact call. Continue the same run through the previously authorized activity/story/video stages only after each stage succeeds and all gates pass. Do not retry any accepted or ambiguous call.
5. If rejected before a call ID, stop further inference and report the safe error category.

## Preservation

- No fixture output, direct worker request, direct DB write, quota/admission/safety bypass, Modal deployment/limit/billing edit, dependency/volume recreation, real-child data, credential output, Computer Use, commit, or push.
- The root `.env` remains local and ignored. The re-created API container must continue to match it for Modal credential keys; only boolean match results may be recorded.
- Record run/call refs, elapsed times, screenshots, UI result and any downstream output in the existing FEAT-085 evidence folder.
