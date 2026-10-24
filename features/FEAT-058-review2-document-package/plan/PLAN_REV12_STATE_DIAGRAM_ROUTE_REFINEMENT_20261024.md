# Plan Rev12 — State Diagram Route Refinement

- Date: 2026-10-24
- Status: Approved by the project owner's direct instruction in the current chat.
- Feature: FEAT-058-review2-document-package.
- Scope: documentation and diagram structure only; no product/runtime changes.

## Owner request

The owner saw remaining text and arrow crowding in generated state-machine diagrams and asked for every generated diagram to be checked, with a more professional structure and arrow placement. This plan records that direct instruction and the follow-up layout work.

## Changes

1. Increase spacing between state nodes, transition routes, and edge labels across the generated set.
2. Move session cancellation and early-end transitions out of the main Session Lifecycle view into its companion Session Terminal Outcomes state machine. Keep every source transition represented and add an explicit companion note on the main view.
3. Move the four grant-revocation transitions out of Device Connection Lifecycle into the existing Device Grant Revocation companion state machine. Keep every transition represented and add an explicit companion note on the main view.
4. Split the Data Request terminal branches into focused cancellation and external-purge companion state machines. The main lifecycle points to both; every cancellation and purge outcome remains represented.
5. Regenerate the editable Draw.io pages and the four Review 2 DOCX/PDF dossier pairs from the revised diagram set. Preserve all five supplied Draw.io originals and omit canvas source attribution.
6. Inspect all 24 generated diagrams at full size, then inspect every page of the regenerated report PDF where the diagrams appear.

## Acceptance criteria

- AC72: All 24 generated lifecycle/activity pages are present in the editable Draw.io master: 20 state-machine and four activity diagrams. All canvases name their diagram type; no source attribution appears on canvases.
- AC73: Session terminal outcomes, device grant revocation, and Data Request cancellation/external-purge outcomes remain represented across focused companion views; each relevant main view points to its companions.
- AC74: Full-size visual review shows zero overlapping labels, text/node collisions, node collisions, route/node collisions, route/label collisions, and route crossings.
- AC75: The four dossier categories remain DOCX/PDF pairs. The consolidated report embeds the revised figures and captions; every page of the refreshed report PDF is rendered and inspected.
- AC76: All five supplied Draw.io originals remain byte-identical.
- AC77: The consolidated report gallery labels each figure with its diagram type and maps the final generated pages to D23–D46, including workflow activities D43–D46.

## Boundaries

- Keep registered project scope, requirement wording, provider decisions, and runtime evidence unchanged.
- The generated lifecycle/activity views remain design models; layout cleanup does not claim implementation or acceptance.
- Keep Registration+BM03, all PDFs, and page renders local under the repository security policy.
