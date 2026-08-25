# Montessori Offline Test Console user guide

Run commands from the repository root. The tool uses committed synthetic fixtures only and never calls a network, backend, mobile app, AI model, database, or provider.

## One-command validation

```powershell
backend\.venv\Scripts\python.exe tools\validate_montessori_console.py
```

Expected headline: `MONTESSORI_CONSOLE_VALID`, with `golden_fixture_parity=74/74`.

## Browse activity IDs

```powershell
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py list
```

This lists all 20 records and their required IDs. It does not choose, score, rank, or recommend an activity.

## Guided mode

```powershell
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py interactive
```

Choose one `ACT-xxxx` and enter only synthetic IDs/numeric age. Empty readiness/material/policy fields are allowed so blocked behavior can be tested.

## Reproducible scenarios

```powershell
# Primary material: exit 0
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py replay tests\fixtures\montessori-console\valid-primary.json

# Household substitute: exit 0
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py replay tests\fixtures\montessori-console\valid-substitute.json

# Four blockers: exit 2
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py replay tests\fixtures\montessori-console\blocked-multiple.json

# Forbidden unknown child field: exit 1
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py replay tests\fixtures\montessori-console\malformed-unknown-field.json
```

Add `--json` for stable compact JSON.

## Evaluate one explicit activity

```powershell
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py evaluate `
  --activity ACT-0004 `
  --age-months 16 `
  --readiness READY_SEARCH_PARTLY_HIDDEN `
  --material GMAT-0004-PRIMARY `
  --supervision DIRECT `
  --policy CAREGIVER_PRESENT
```

Repeated values use repeated flags, for example `--completed ACT-0001 --completed ACT-0002`. The console evaluates only the supplied activity ID.

## Record sanitized evidence

```powershell
backend\.venv\Scripts\python.exe tools\montessori_golden_console.py replay `
  tests\fixtures\montessori-console\valid-primary.json `
  --record-evidence my-valid-run
```

Run IDs permit lowercase letters, digits, and internal hyphens only. Output is confined to `features/FEAT-014-montessori-offline-test-console/evidence/runs/`, and existing files are never overwritten.

Do not enter real names, narration, observations, diagnoses, media, or any child data. `VALID_CANDIDATE` means only that the synthetic input passes the deterministic fixture contract; every record remains `production_eligible=false`.
