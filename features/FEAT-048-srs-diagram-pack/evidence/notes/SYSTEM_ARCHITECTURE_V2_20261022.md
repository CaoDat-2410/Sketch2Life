# System Architecture v2 — implementation and review

## Scope and source

- Owner: Khoa.
- Request: add a more conventional architecture version to the existing Draw.io file, include the corresponding Mermaid source, and make the drawing rules explicit after reviewing the AWS-inspired demo.
- Canonical source: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, section B8, registered as `collaborative-srs-v3-20261010` in `docs/context/SOURCE_REGISTER.md`.
- Repository constraints reviewed: `AGENTS.md`, including inward dependencies, Firebase Authentication-only, and no mobile storage/provider credentials.
- Approved task: feature plan revision 13 and `approvals/TASK_APPROVAL.md` revision 14.

## Deliverables

- Editable Draw.io page 4: `System Architecture v2` in `artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio`.
- Mermaid counterpart: `src/diagrams/system-architecture-v2.mmd`.
- Concrete visual/semantic rules: `ARCHITECTURE_DRAWING_RULES.md`.
- Builder that appends/replaces only the named comparison page: `src/add_system_architecture_v2.py`.

## Drawing rules applied

1. Use Draw.io-native, editable actor symbols, rectangles, swimlane/system boundaries, cylinders for durable storage, a queue shape, and orthogonal connectors. No generated background image, decorative cloud artwork, or vendor logo is used.
2. Draw a logical architecture with three visible areas: people/client surfaces, Sketch2Life backend, and external persistence/provider capabilities. Keep the async worker/queue path in its own lower band.
3. Put the status in each component label. Green is confirmed; amber marks candidate; blue marks proposed; gray marks TBD or policy-constrained. Color is only a secondary cue.
4. Label every meaningful connector. Solid arrows show runtime/data flow. Dashed arrows carry explicit labels to distinguish proposed transport from adapter-implements-port dependency. The port call and implementation dependency point in different directions by design.
5. Keep dependencies inward: Application uses owned ports, adapters implement the ports, and external calls originate at backend adapters. Mobile has no direct provider/storage call.
6. Keep the AWS reference as a layout inspiration only. PostgreSQL, Redis/RQ, and S3-compatible storage remain candidates. WebSocket and async worker processing remain proposed. AI provider/payload, desktop UI framework, and deployment topology remain unresolved.

Teacher Desktop and Super Admin are mixed-status surfaces: each page node is neutral and explicitly labels the surface `CONFIRMED` and UI framework `TBD` so the fill does not imply both are settled.

## Preservation and structural review

- The builder compares fingerprints for the original ERD, System Architecture, and Package Diagram pages before and after writing. Those pages were preserved from the latest owner-saved Drive baseline, including the owner's connector/layout edits.
- Final local document has four pages. The new page has 87 `mxCell` elements including two root cells: 61 vertices and 24 edges. Each edge has resolvable source and target cell IDs; no dangling edge endpoints were found.
- The XML is native editable Draw.io content. The Mermaid source expresses the same key component boundaries, statuses, request path, port/adapter relationship, external candidates, and async flow.
- This structural review does not establish pixel-level readability in diagrams.net. No official diagrams.net renderer/editor or Mermaid renderer was available; rendered visual QA remains pending.

## Drive readback

- Existing file was updated in place; ID retained: `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`.
- Destination parent retained: `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`.
- Final metadata readback: 113,485 bytes; modified `2026-10-22T16:53:42.570Z`.
- Raw readback declares four pages and contains page name `System Architecture v2`, plus the final mixed-status surface/framework labels.
- The file remains the existing Draw.io artifact in the supplied folder; no extra Drive file was created.

## Limits

- Canonical SRS and runtime/schema implementation were not changed.
- No vendor/deployment choice was inferred from the AWS-style reference.
- FEAT-048 remains on the local branch `feature/feat048-srs-diagram-pack`; no commit or GitHub push occurred.
