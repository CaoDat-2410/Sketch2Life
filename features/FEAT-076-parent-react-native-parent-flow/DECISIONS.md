# FEAT-076 Decisions

## D1 — Reuse the native feature boundary

Keep Parent screens dependent on ParentWorkflowPort. Put synthetic run/profile transitions in ParentDemoWorkflowAdapter and keep fixture content centralized in parentDemoFixtures.

## D2 — Preserve demo-only behavior

All profile, quota, video, purchase, and playback states remain synthetic and in-memory. No provider, API, auth, device capture or persistence integration is added.

## D3 — One active run and stable child identity

The adult may select a profile in one tap. A currently active run remains bound to its original child and blocks a second active run; profile changes cannot rewrite that run's childProfileId.

## D4 — Explicit final script and accepted-job boundary

P06 opens an adult-facing preflight. Only the explicit create action confirms the final script and requests video. A successfully accepted request consumes one demo quota unit once, routes to P07, and remains there until the fixture reaches READY. Playback opens only after READY.

## D5 — Keep gender local to the demo profile UI

Boy/girl selection drives the illustrative avatar only. It is not added to AI context or a product/API/SRS contract, consistent with the previous FEAT-073 scope.

## D6 — Do not resolve the activity catalog question

Show only the configured pinned lesson fixture after ready playback. No-preset activity catalog behavior remains OPEN in the current SRS.

## D7 — Use native primitives without new visual assets

Build the requested child-friendly visual treatment with existing React Native components and styles. No new generated/external asset enters the asset approval pipeline.
