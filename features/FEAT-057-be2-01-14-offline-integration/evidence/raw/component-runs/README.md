# Component-run receipts

These files are copied from the seven card-owned `run_component_checks.py`
executions on the merged candidate. Each `*-summary.json` is the runner's
machine-readable receipt; adjacent JUnit files preserve the selected test
outcomes. Trailing spaces in captured failure text were trimmed from the copied
BE2-12 XML; the committed-copy SHA-256 values are listed in
`../../metrics/offline-test-matrix.json`.

The BE2-12 receipt records the single environment failure: importing the live
FastAPI route requires the declared but unavailable `python-multipart` package.
BE2-14 delegates its 477-case regression pack to BE2-12 and inherits that same
failure. No database URL, provider endpoint, or Lightning runtime was used.
