# Evidence management guide

## Evidence location

Evidence belongs in the feature that owns the behavior:

```text
features/FEAT-xxx/evidence/
├─ README.md or INDEX.md            # evidence index and status
├─ raw/                             # raw logs or captured outputs
├─ screenshots/                     # visual/device evidence
├─ metrics/                         # JSON/CSV benchmark results
└─ notes/                           # review interpretation and limitations
```

Do not put feature evidence in a shared `evidence/` root or only in a chat message.

## Minimum evidence record

Every entry records:

- Evidence ID.
- Related acceptance criterion/task.
- Type: test, screenshot, benchmark, review, source, or decision.
- Exact command or input/reference.
- Environment/device/model/config version.
- Output artifact path.
- Timestamp and reviewer.
- Interpretation, limitations, and follow-up.

## Evidence quality

- Behavioral claims need reproducible test/log evidence.
- Visual claims need screenshots or recordings plus device/context.
- Model claims need fixture manifest, model/config version, metrics, and failure examples.
- Architecture claims need a dependency review or import scan.
- Negative cases are first-class evidence: blocked transitions, invalid fixtures, fallback, and stale versions.

## Retention

Keep small human-readable summaries in `README.md`/`INDEX.md` and store larger outputs under the same feature. Use IDs and hashes instead of raw sensitive data.
