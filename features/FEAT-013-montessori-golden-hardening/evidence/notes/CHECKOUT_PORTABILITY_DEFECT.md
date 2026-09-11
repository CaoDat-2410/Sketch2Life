# FEAT-013 checkout portability defect

- Detected: 2026-08-25
- Trigger: switch to `plan/person-1-montessori-offline-console`, then run `python tools/validate_montessori_golden.py`
- Result: `MONTESSORI_GOLDEN_INVALID: baseline hash mismatch: activities.v1.json`
- Baseline Git diff: empty
- Repository policy: `.gitattributes` sets `* text=auto eol=lf`
- Interpretation: raw-byte hashes captured line-ending representation rather than JSON content integrity.

## Raw-byte hashes after repository LF checkout

```text
activities.v1.json=c88fa6027fe8df177eae3e49bfcd08317b98920abd7f21f09f2523afb0dfb85c
learning-objectives.v1.json=8b7608a0005104d7c921c22a52dc8b61e8cf4faf9508b94f8b755474c289722c
hard-rules.v1.json=9a395757fdbdcb41c80f14843ce223a9decf37d1a5bbb5565e32b29e6dba0b46
provenance.v1.json=65fa2941433b61057739f8b89422cc05bcc14f19d1652ec5424e75f919597101
```

## Proposed canonical JSON SHA-256 values

```text
activities.v1.json=17dde39fcc6e2951fab7cc158c11d230766f69930be8dd0596d377dab514989c
learning-objectives.v1.json=69ecff8f8944628c0a9a6b3eeb28bda24d17fd3b3856603725d9e97638895a3e
hard-rules.v1.json=b42d46dd6c893e266b2f6cab73b7b04af11628ef5f58485f553ebcdca40cee7d
provenance.v1.json=345bffb87be6953595d89d37eb2d222352ff9be83a8fc40e637571b895edee47
```

No tracked FEAT-002 file was edited. This evidence records a pre-fix failure; passing evidence must not be claimed before corrective approval and implementation.

## Related repository-gate finding

After the Golden baseline fix first passed, the full suite exposed the same checkout representation issue in the legacy FEAT-002 fixture manifest: its historical digests represent CRLF files while Git checks them out as LF. The approved correction preserves all fixture/catalog files and adds line-ending normalization only to the legacy validator compatibility path. Semantic fixture mutations remain detectable.

## Resolution

- Status: RESOLVED
- Golden baseline algorithm: `sha256-canonical-json-v1`
- Legacy FEAT-002 fixture compatibility: normalize text line endings to historical CRLF before checking existing manifest digests
- LF/CRLF parity tests: PASS
- Semantic baseline mutation: PASS_EXPECTED_NONZERO
- Deterministic Golden rebuild: PASS
- FEAT-002 data diff: none
- Test result at correction closure: 18 passed
