# System Architecture drawing rules

These rules apply to both System Architecture pages in the Draw.io file and their Mermaid sources. They keep the diagram readable and stop a candidate from looking like an approved deployment choice.

## 1. State the diagram's scope

- Label the page as a **logical architecture** or **candidate deployment view**.
- Draw only boundaries supported by the SRS: people/client surfaces, the Sketch2Life backend, and persistence/provider services outside the backend.
- Do not add AWS Region, VPC, availability zone, API Gateway, CloudFront, S3, Lambda, or other vendor products unless an ADR selects them. The AWS reference provides a layout style, not a deployment decision.
- Keep the original architecture page as the baseline. Name the additional page `System Architecture v2` so reviewers can compare them.

## 2. Use one meaning for each shape

| Shape | Meaning |
|---|---|
| Role card with Lucide `user-round` | Child, Teacher, or Super Admin actor |
| Rectangle | Client application, API, use case, adapter, worker, or external service |
| Swimlane / large framed rectangle | A system, client, domain, adapter, or external-service boundary |
| Cylinder | Durable database or object-storage capability |
| Queue symbol / explicitly named queue box | Asynchronous work queue |
| Small boxes inside the Domain frame | B8 domain context groupings; these are proposed boundaries |
| Port/interface box | Application-owned outbound contract; it is not an infrastructure service |

Prefer Draw.io-native editable shapes. Use generic symbols for unselected providers. Do not flatten the page into a background image.

## 3. Use icons as restrained role cues

- Use the Lucide v1.61.0 outline assets already previewed in the icon catalog. Keep one monochrome stroke, consistent size, and consistent placement inside component nodes.
- Place icons only on primary roles and boundaries: people, clients, FastAPI, Application, Domain, outbound ports, selected external capabilities, the artifact adapter, and the async flow. Leave the nine small B8 context boxes and most adapter rows text-only so the page stays readable.
- Icons identify component type only. Status always remains in the adjacent text label and status styling; an icon never means confirmed, proposed, candidate, or TBD.
- Keep confirmed technology names as text. Use generic icons for AI, identity, storage, queue, and realtime boundaries; do not use vendor logos or remote/CDN images.
- The `.drawio` embeds SVG as a self-contained, percent-encoded data URI so it works offline. Do not use `;base64` inside an image URI in the style string: semicolons separate Draw.io style entries. The builder decodes each URI and checks that it contains valid SVG XML. The `.mmd` source records the same icon-name-to-role mapping in comments; the flowchart remains self-contained and does not require a Mermaid icon pack.
- Preserve the Lucide source/version and applicable ISC/MIT notices in `assets/icons/lucide-v1.61.0/NOTICE.md`.

## 4. Write status in the node label

| Label | Use |
|---|---|
| `CONFIRMED` | Explicitly confirmed by the current SRS/owner: Android with React Native/TypeScript, FastAPI/Python, and the named product surfaces |
| `CANDIDATE` | A technology named by the SRS as scaffolding or a proposal, not a selected production dependency: PostgreSQL, Redis/RQ, S3-compatible storage |
| `PROPOSED` | A behavior or design path described as proposed: WebSocket canvas/presence, ordered canvas operations/checkpoints, worker separation where still pending implementation |
| `TBD` | The SRS has not selected the value: AI provider, provider payload, teacher/admin UI framework, deployment topology |
| `POLICY CONSTRAINT` | A repository rule limits the choice, but integration is not complete: Firebase Authentication is the only permitted Firebase service; the adult-identity adapter remains TBD |

Status must appear as text. Use color and line style only as a second cue. Never style a candidate exactly like a confirmed component. If one box combines a confirmed product surface with an undecided framework, keep the box neutral and label both statuses separately; do not let one fill color imply both choices are settled.

## 5. Give arrows distinct meanings

- **Solid directional arrow:** runtime request, response, or data movement. Label it with the action/data, such as `REST command`, `enqueue bounded job`, or `typed result`.
- **Dashed amber arrow pointing from adapter to port:** dependency/implementation direction; the adapter implements the application-owned contract. This arrow is not the runtime call direction.
- **Dashed blue arrow:** proposed transport or flow, such as a WebSocket canvas/presence stream.
- Do not use one unlabeled dashed line for both a proposed runtime flow and an adapter dependency. Include the arrow samples and meanings in the page legend.
- Keep each connector orthogonal, behind nodes, and attached to the intended boundary. Avoid crossings and shared trunks that make the source or destination unclear.

## 6. Preserve the architecture boundaries

- Primary request path: client surface → FastAPI/Python → Application → Domain.
- Application uses outbound ports. Infrastructure adapters implement those ports. Do not draw a direct Application-to-database/provider dependency.
- External identity, AI, storage, queue, and realtime calls originate from backend adapters. Mobile does not call AI or storage providers directly and never holds their credentials/endpoints.
- Keep the asynchronous worker separate from the request path. It claims bounded work from the queue, calls the backend-only AI adapter, and returns a typed result/status for Application scope/version checks. Do not route AI calls through every pointer event.
- Realtime is a proposed canvas/presence transport; it is not a source of truth for portfolio, consent, approvals, or durable operation history.

## 7. Keep the layout reviewable

- Lay out the main request flow left to right: actors/clients, API, Application/Domain, then outbound integrations.
- Put external services outside the backend boundary. Keep the worker/async path in a separate lower band.
- Align port, adapter, and capability rows so their mapping is clear. Use short component labels and put detailed caveats in the legend or notes.
- Use a white canvas, restrained fills, consistent type sizes, and no shadows, decorative textures, or repeated status pills.
- Fit labels to the page at normal diagrams.net zoom; reroute a connector rather than shrinking the text to make it fit.

## 8. Keep Mermaid and Draw.io aligned

- Mermaid expresses the component relationships and statuses; Draw.io expresses the same model with editable visual layout.
- When a node, status, or flow changes in one format, update its counterpart and record the SRS paragraph that supports the change.
- Keep technology candidates visibly unselected until a decision is recorded in an ADR. Do not turn a visual example into a stack decision.

## SRS v3.1 facts used on v2

- Confirmed: Android / React Native / TypeScript, FastAPI / Python, Child, Teacher, and Super Admin surfaces.
- Proposed context groupings: Identity/Consent; Classroom; Session/Groups; Drawing/Collaboration; AI Assistance; Knowledge/Media; Activities; Portfolio/Assessment; Governance/Audit.
- Named candidates: PostgreSQL, Redis/RQ, and S3-compatible storage. Firebase is Authentication-only under repository policy; adult-identity adapter completion remains open.
- Proposed: WebSocket canvas/presence and server-authoritative ordered operations/checkpoints. AI provider, exact payload, deployment topology, and web frameworks remain unresolved.
