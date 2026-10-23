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
| Role/client card with a technology logo or AWS client pictogram | Child, Teacher, or Super Admin and the surface they use |
| Rectangle | Client application, API, use case, adapter, worker, or external service |
| Swimlane / large framed rectangle | A system, client, domain, adapter, or external-service boundary |
| Cylinder | Durable database or object-storage capability |
| Queue symbol / explicitly named queue box | Asynchronous work queue |
| Grouped Domain card / names inside its frame | All nine B8 proposed context groupings; names do not imply nine deployed services |
| Port/interface box | Application-owned outbound contract; it is not an infrastructure service |

Prefer Draw.io-native editable shapes. Use generic symbols for unselected providers. Do not flatten the page into a background image.

## 3. Use official technology logos and AWS role/category cues on v2

- Owner approval revision 22 selects original official FastAPI, Firebase, React Native, PostgreSQL and Redis artwork for the five explicitly named technologies. Keep original colors/aspect ratio and the existing icon positions. The Redis logo represents Redis in the candidate Redis/RQ combination, not a separate RQ brand or a newly adopted queue.
- The other nine main icon cells keep AWS General/Category artwork for logical roles and undecided capability boundaries. Generic S3-compatible storage does not receive the AWS S3 product logo; the unknown AI provider remains generic.
- Record exact official URLs, source revisions/hashes and usage conditions in the text manifest and `NOTICE.md` under `assets/icons/technology-logos-2026-10-23/`. Embed the original SVGs in the editable Draw.io file; standalone SVG files are local inputs and are excluded from the curated GitHub set. A logo identifies technology, while candidate/proposed/TBD text still controls its decision status.
- Mermaid remains a portable text-based counterpart of the same logical graph. Record icon mappings in source comments; no external icon pack or image download is required to render either delivered Mermaid diagram.

- Owner approval revision 18 selected the official AWS Architecture Icons package dated 2026-07-31, superseding Lucide on v2. Approval 22 replaces five named-technology cues with their own official logos; retained AWS assets and all historical previews preserve their provenance.
- Retain AWS General symbols for Teacher/Admin clients, worker, Application, Domain/Ports and generic object storage. Application Integration and Artificial Intelligence category symbols describe adapters and the unknown AI capability. Named-technology substitutions follow approval 22 above. Preserve original colors and shapes; do not recolor or redraw artwork.
- Do not use specific EC2, RDS, S3, SQS, Cognito, Lambda or Bedrock service icons for generic or unselected components. The diagram remains the SRS logical architecture, with deployment topology TBD.
- Place icons on main components only. Group all nine B8 domain names and the six aligned port/adapter mappings as readable text detail; aim for 14 main components rather than an icon for every row.
- Icons identify roles/categories only. Confirmed/candidate/proposed/TBD/policy status stays in the adjacent text; AWS category color never indicates project approval.
- Keep confirmed technology names as text and all embedded image sources local, without CDN/runtime dependencies.
- The `.drawio` embeds SVG as a self-contained, percent-encoded data URI so it works offline. Do not use `;base64` inside an image URI in the style string: semicolons separate Draw.io style entries. The builder decodes each URI and checks that it contains valid SVG XML. The `.mmd` source records the same icon-name-to-role mapping in comments; the flowchart remains self-contained and does not require a Mermaid icon pack.
- Record the official package URL, member names, unchanged SVG checksums and AWS usage terms in the text files `assets/icons/aws-2026-07-31/manifest.json` and `NOTICE.md`. Keep those provenance files with the editable artifact; standalone SVG files are local inputs and are excluded from the curated GitHub set. Do not describe AWS assets as MIT/ISC. Official source: https://aws.amazon.com/architecture/icons/.

## 4. Write status in the node label

| Label | Use |
|---|---|
| `CONFIRMED` | Explicitly confirmed by the current SRS/owner: Android with React Native/TypeScript, FastAPI/Python, and the named product surfaces |
| `CANDIDATE` | A technology named by the SRS as scaffolding or a proposal, not a selected production dependency: PostgreSQL, Redis/RQ, S3-compatible storage |
| `PROPOSED` | A behavior or design path described as proposed: WebSocket canvas/presence, ordered canvas operations/checkpoints, worker separation where still pending implementation |
| `TBD` | The SRS has not selected the value: AI provider, provider payload, teacher/admin UI framework, deployment topology |
| `POLICY CONSTRAINT` | A repository rule limits the choice, but integration is not complete: Firebase Authentication is the only permitted Firebase service; the adult-identity adapter remains TBD |

Status must appear as short text beside the affected choice. The current v2 uses neutral white boxes; different status words distinguish confirmed facts, candidates, proposals and open decisions without repeated color badges. If one box combines a confirmed product surface with an undecided framework, label both separately.

## 5. Give arrows distinct meanings

- **Solid directional arrow:** runtime request, response, or data movement. Label it with the action/data, such as `REST command`, `enqueue bounded job`, or `typed result`.
- **Dashed arrow labeled `implements` pointing from adapter to port:** dependency/implementation direction; the adapter implements the application-owned contract. This arrow is not the runtime call direction.
- **Dashed arrow labeled with the proposed transport/flow:** WebSocket canvas/presence or authorized events. The simplified v2 uses neutral connector colors and relies on these direct labels.
- Do not use one unlabeled dashed line for both a proposed runtime flow and an adapter dependency. Use direct labels such as `implements` and `WebSocket · proposed`; the owner-requested simplified v2 omits the large legend.
- Keep each connector orthogonal, behind nodes, and attached to the intended boundary. Avoid crossings and shared trunks that make the source or destination unclear.

## 6. Preserve the architecture boundaries

- Primary request path: client surface → FastAPI/Python → Application → Domain.
- Application uses outbound ports. Infrastructure adapters implement those ports. Do not draw a direct Application-to-database/provider dependency.
- External identity, AI, storage, queue, and realtime calls originate from backend adapters. Mobile does not call AI or storage providers directly and never holds their credentials/endpoints.
- Keep the asynchronous worker separate from the request path. It claims bounded work from the queue, calls the backend-only AI adapter, and returns a typed result/status for Application scope/version checks. Do not route AI calls through every pointer event.
- Realtime is a proposed canvas/presence transport; it is not a source of truth for portfolio, consent, approvals, or durable operation history.
- Place the proposed WebSocket client/backend connection at the backend realtime adapter (SRS B3/B8). Do not draw WebSocket as an independent external provider.

## 7. Keep the layout reviewable

- Current v2 presentation (plan 20): 3200×1740 editable canvas, 17px body/15px flow text and 48px official icons, with white group interiors, thin neutral boundaries, short labels and orthogonal routes. Remove explanatory note boxes, the large status/icon legend and footer provenance from the canvas. Keep the full source/caveat record in feature evidence. Reserve separate WebSocket, queue-claim and typed-completion corridors; review at native render scale as well as fit-to-page.

- Lay out the main request flow left to right: actors/clients, API, Application/Domain, then outbound integrations.
- Put external services outside the backend boundary. Keep the worker/async path in a separate lower band.
- Align port, adapter, and capability rows so their mapping is clear. Use short component labels and put detailed caveats in feature evidence rather than on-canvas notes.
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
