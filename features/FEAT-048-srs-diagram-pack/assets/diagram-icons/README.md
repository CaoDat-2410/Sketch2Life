# Diagram icons and technology logos

Source assets for the System Architecture Draw.io tab. They are embedded in the Draw.io file as data URIs; the Mermaid sources use text labels only and do not reference these files.

## technology-logos/

Official-source logos, kept unmodified (same bytes as the source). Source URLs, extraction notes and SHA-256 values are in `technology-logos/PROVENANCE.json`.

| File | Technology |
|---|---|
| `react-native.svg` | React Native (Child Android app) |
| `fastapi.png` | FastAPI |
| `postgresql.png` | PostgreSQL |
| `firebase.svg` | Firebase (logomark from the official brand-asset archive) |
| `redis.svg` | Redis |

Logos remain trademarks of their owners. They identify a technology that the SRS names as confirmed or candidate; they do not imply endorsement and do not select a technology. A logo here does not change a status label in the diagram.

## ui-icons/

Generic category icons.

- Lucide icons (ISC licence; some also covered by the MIT notice, see `LICENSES.txt`): `cpu`, `database`, `hard-drive`, `list-ordered`, `monitor`, `server`, `shield-check`, `smartphone`, `sparkles`. Source and hashes: `lucide-PROVENANCE.json`.
- `brain-circuit.svg`: Lucide `brain-circuit`, unmodified (`brain-circuit-PROVENANCE.json`).
- `ai-endpoint-hub.svg`: locally authored generic icon for connected model endpoints, not a brand and not an implication of any provider, hosting or model (`ai-endpoint-hub-PROVENANCE.json`).

Icon meaning is a category cue only; the labels carry every SRS status and technology decision.

## Not included

- `firebase-brand-assets.zip` (6.2 MB official archive). The extracted logomark is `firebase.svg`; the archive source URL and SHA-256 are in `technology-logos/PROVENANCE.json`.
- A supplied Qwen SVG: not verified as an official logo and not used. The diagram names Qwen3-VL in text only, as a candidate from the FEAT-039 reuse note.
- `fastapi.svg` and `firebase.png` (no provenance entry), the demo `LAYOUT*.json` files and the earlier `NOTICE.md` (it described an older diagram design).
