# Frontend visual asset gate

The frontend asset lifecycle is:

```text
BRIEF -> GENERATED -> REVIEW_PENDING -> APPROVED -> APPLIED
                         \-> REJECTED -> REVISE -> GENERATED
```

## Rules

- Generate assets only into the feature's `assets/generated/` directory.
- Record prompt/brief, source references, generator, timestamp, and output hash in the asset manifest.
- A reviewer must record approval or rejection in `assets/REVIEW.md`.
- `assets/approved/` may contain only assets with an approval record.
- Runtime code may reference only `assets/approved/` or `assets/applied/`.
- Never overwrite an approved asset; create a new version and repeat review.
- If the asset changes materially, the old approval does not carry forward.

See `tools/validate_harness.py` for the mechanical checks currently enforced.
