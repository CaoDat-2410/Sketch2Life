# FEAT-057 X01 Modal offline rerun — 2026-10-20

## Result

**PASS for the scoped offline test rerun.** The owner supplied the Modal
`modal_run.json`, JUnit, and pytest log after executing the prepared notebook.
The receipt, JUnit counts, artifact hashes, and local source archive were
independently compared.

| Check | Verified result |
|---|---:|
| Source ZIP SHA256 | `5e7d3e10c8ef5439efc6a39dd6a17774ec40e746b054153b004215f6479ca9e8`; matches the local packaged ZIP |
| Python | 3.12.6 |
| Modal profile | CPU, 2 cores, 4 GiB RAM, no GPU; Default image |
| Dependency setup | Install completed; `pip check` reported no broken requirements |
| X01 cross-lane suite | 14 passed |
| Adjacent BE2-07/08 suites | 282 passed |
| Total | **296 passed, 0 failed, 0 errors, 0 skipped** |
| Pytest exit | 0 |

The test command covered `tests/integration/be2_cross_lane` and the six
BE2-07/08 unit modules recorded in
`metrics/CROSS_LANE_X01_MODAL_20261020.json`. The JUnit timestamp is
`2026-10-20T16:39:50.031778+00:00`.

## Artifact integrity

The exact owner-supplied artifacts are preserved under
`evidence/raw/modal-x01-20261020/`:

| File | Bytes | SHA256 |
|---|---:|---|
| `modal_run.json` | 971 | `2ea3406d19622f963bbf600b95e7821fdb564e7fb71bc2cdfbcc51a64824e5f7` |
| `junit.xml` | 48,166 | `552cf4ead2dd17f409676dc77dbfccf0822a450779c1de4e25cfd25b6b31e4a3` |
| `pytest.log` | 3,140 | `3b990a3e0c35976fcb0e82f8c6483cf7748b1ba00e15df5acb05fc1eee871d3d` |

The receipt's JUnit and log hashes match the downloaded files, and the parsed
JUnit totals match the receipt exactly. The source ZIP hash also matches the
locally prepared archive.

## Interpretation and limits

This confirms that the pinned source package can install its declared test
profile and run the selected offline tests in a hosted CPU notebook. It does
not close X01's missing BE2-01 foundation job/artifact commit or cross-owner
fence. X01 remains `PARTIAL`; X02–X09 remain `NOT_IMPLEMENTED`. It is not full
BE2-01–14 integration, a card acceptance, or evidence for PostgreSQL, HTTP,
real provider/decoder, Lightning/Studio, live worker, or deployment behavior.
No card approval, status, or `DONE` state changed.
