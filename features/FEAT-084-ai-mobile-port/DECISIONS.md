# FEAT-084 decisions

## D-084-01 - Current mobile line is the base (2026-11-23)

The source branch's mobile files are older than the current line. Only the new AI screens and their additive types, ports and API calls are hand-merged; nothing is taken wholesale and Phase A wiring is not changed.

## D-084-02 - Video candidate and activity AI stay out (2026-11-23)

The video-candidate screen and the AI activity-suggestion calls duplicate Phase A designs or depend on routes that are not ported. They are separate follow-ups.

## D-084-03 - Unknown topic has no AI guide (2026-11-23)

The ported sketch-guides route is catalogue-first and returns 404 for an unknown topic. The screen lets the adult continue without a guide, because the guide is optional.

## D-084-04 - Feature id (2026-11-23)

FEAT-083 is the backend port; FEAT-084 is the mobile port.

## D-084-05 - Backend Pydantic contracts govern mobile field mapping (2026-11-23)

Use the AIPORT1 Pydantic models at commit `283158a8` for exact request and response names, limits and literals. Do not preserve the source branch's retired sketch-guide request body.

## D-084-06 - Only allowlisted topic API copy reaches the screen (2026-11-23)

For `PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED` and `PARENT_TOPIC_TEXT_NOT_ALLOWED`, preserve only a bounded, control-character-free API display message. Keep the safe display copy separate from the exception's general message so unrelated server details never flow into the UI.

## Open

- OPEN-1: owner decision on SRS Rev70-Rev73.
- OPEN-2: video-candidate screen and AI-generated activity set under Phase A (follow-up tasks).
