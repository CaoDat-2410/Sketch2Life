# Montessori domain boundary

This package contains framework-independent specifications and JSON Schemas for Montessori activity fixtures. It does not implement recommendation ranking, persistence, UI, or provider integration.

## Review status

The current 100-activity catalog is synthetic/provisional. The project owner accepted every activity and objective as `PROVISIONAL_OWNER_REVIEWED` on 2026-08-25; all remain `production_eligible=false`. Qualified Montessori review is still required before production use.

FEAT-013 adds a 20-activity Golden Activity v2 overlay for deeper integration fixtures. The project owner accepted all 20 as `PROVISIONAL_OWNER_REVIEWED` on 2026-08-25; they remain `production_eligible=false` and do not replace the 100-record v1 baseline.

## Contents

- `spec/GLOSSARY.md`: canonical terms.
- `spec/ID_VERSION_RULES.md`: identity and compatibility rules.
- `spec/RULE_SEMANTICS.md`: deterministic hard-rule behavior.
- `spec/GATE_B_ACCEPTANCE.md`: future Gate B acceptance criteria, not runtime code.
- `spec/ACTIVITY_HANDOFF.md`: off-screen handoff contract.
- `spec/GOLDEN_ACTIVITY_FIELD_GUIDE.md`: Golden Activity v2 field semantics.
- `spec/GOLDEN_REVIEW_RULES.md`: independent review and hard-rule constraints.
- `schemas/`: versioned JSON Schemas.

## Standalone validation

```powershell
python tools/validate_montessori_domain.py
python tools/validate_montessori_golden.py
```

The validator reads only committed local JSON files and fixtures. It does not access a network, database, AI model, or another team's service.
