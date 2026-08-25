# Montessori domain boundary

This package contains framework-independent specifications and JSON Schemas for Montessori activity fixtures. It does not implement recommendation ranking, persistence, UI, or provider integration.

## Review status

The current 100-activity catalog is synthetic/provisional. Every activity is `PENDING_OWNER_REVIEW` and `production_eligible=false`. A future owner review may mark a record `PROVISIONAL_OWNER_REVIEWED`; qualified Montessori review is still required before production use.

## Contents

- `spec/GLOSSARY.md`: canonical terms.
- `spec/ID_VERSION_RULES.md`: identity and compatibility rules.
- `spec/RULE_SEMANTICS.md`: deterministic hard-rule behavior.
- `spec/GATE_B_ACCEPTANCE.md`: future Gate B acceptance criteria, not runtime code.
- `spec/ACTIVITY_HANDOFF.md`: off-screen handoff contract.
- `schemas/`: versioned JSON Schemas.

## Standalone validation

```powershell
python tools/validate_montessori_domain.py
```

The validator reads only committed local JSON files and fixtures. It does not access a network, database, AI model, or another team's service.
