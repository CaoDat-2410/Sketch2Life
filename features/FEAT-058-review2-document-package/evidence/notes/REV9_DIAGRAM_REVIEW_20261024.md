# Rev9 diagram conversion and visual review

- Date: 2026-10-24 (Asia/Saigon)
- Feature: FEAT-058-review2-document-package
- Status: Seven-page editable Draw.io master rendered and visually reviewed.
- Authority: owner instruction to add the two missing diagram types (state machine and activity) from Mermaid, then convert/import to Draw.io. This is six state-machine pages within one requested diagram type plus one activity page.
- Render tool: Draw.io Desktop CLI 32.6.1. Mermaid was imported as editable Draw.io elements with `--mermaid-image=false`; a feature-local builder applies the curated multi-page layout. The master contains native editable shapes and connectors; raster renderings are review evidence only.

## Page index and review

| Page | Type | Coverage | Visual review |
|---|---|---|---|
| Session Lifecycle | State machine | Draft, optional scheduling, Lobby, Active, Completing, Completed, pre-Start cancellation | Clear left-to-right progression and separate cancel branches. |
| Session Pause and Recovery | State machine | Active/Pause/Resume, failure to Recovering, return to last valid state | Parallel transitions remain distinct and labels readable. |
| Session Early Termination | State machine | Early end from Lobby, Active, Paused or Recovering | Four origins have separate routes into terminal Ended early. |
| Participant Admission | State machine | Pending, Admitted, Denied, Revoked, Removed, Left, Expired | Pending/Admitted and terminal outcomes are readable; Start boundary is stated in note. |
| Device Connection | State machine | Connecting, Authenticated, Resyncing, Connected, Disconnected/reconnect | Main path and reconnect loop are readable. |
| Device Grant Revocation | State machine | Authenticated, Resyncing, Connected, Disconnected -> Revoked | Separate terminal revocation outcomes are readable. |
| Teacher Lobby and Session Start | Activity | Teacher lobby, QR/code, Child request, review/admit, atomic Start boundary | Decision branches and Start behavior are readable. |

Every page was exported at 1800 px wide and inspected from `evidence/render/rev9/diagrams/rev9-final-page-1.png` through `rev9-final-page-7.png`. Page order and render hashes are in `evidence/metrics/rev9_diagram_provenance_20261024.json`.

## Important boundary

These diagrams model SRS v3.3/B28 target behavior and current design boundaries. They do not prove implementation, persisted transactions, device acceptance, production service configuration, or end-to-end execution. The Activity page explicitly distinguishes the design workflow from the absent PostgreSQL-backed FE-to-BE acceptance run. Existing user-provided Draw.io sources were read-only and not modified.
