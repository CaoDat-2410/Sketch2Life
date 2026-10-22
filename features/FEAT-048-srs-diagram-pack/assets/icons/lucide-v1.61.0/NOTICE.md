# Lucide icon assets

- Upstream: [Lucide](https://github.com/lucide-icons/lucide), pinned to release `1.61.0`.
- SVG source package: `lucide-static@1.61.0`; each SVG retains the upstream version/license comment.
- Source files are embedded in the page 4 Draw.io cells as base64 SVG with only `currentColor` normalized to the single diagram ink color `#42566B`.
- The selected `database`, `monitor`, `server`, and `smartphone` icons are identified by Lucide as Feather-derived and are covered by the MIT notice as well as the ISC notice. Other listed icons use the Lucide ISC notice.
- Full required notices are in `LICENSES.txt`. Asset SHA-256 values are in `manifest.json`.
- No icon package is added to runtime or application dependencies; the Draw.io file works offline.

## Icon-to-role mapping

| Icon | Draw.io role |
| --- | --- |
| `user-round` | Child, Teacher, Super Admin |
| `smartphone` | Android client |
| `monitor` | Teacher and Super Admin surfaces |
| `server` | FastAPI API |
| `list-checks` | Application services |
| `layers` | Domain context groupings |
| `plug` | Outbound ports boundary |
| `database` | PostgreSQL capability |
| `hard-drive` | S3-compatible object-storage capability |
| `list-ordered` | Redis/RQ asynchronous queue |
| `cpu` | Separate worker process |
| `shield-check` | Adult identity boundary |
| `sparkles` | Generic AI provider boundary |
| `radio-tower` | Proposed WebSocket/realtime boundary |
| `package` | Artifact adapter |
| `workflow` | Asynchronous job-flow band |

Icon meanings are category cues only; labels carry all SRS status and technology decisions.
