# Montessori ID and version rules

## IDs

- Activity: `ACT-0001` through `ACT-9999`; never reused.
- Learning objective: `OBJ_[A-Z0-9_]+`; semantic name is stable and locale-independent.
- Material: `MAT_[A-Z0-9_]+`.
- Material group: `MG-<activity sequence>-<group sequence>`.
- Rule: `RULE_[A-Z0-9_]+`.
- Fixture case: `CASE_[A-Z0-9_]+`.

IDs identify logical records; versions identify immutable revisions of those records. Display title changes do not create a new identity, but material changes to objective, readiness, safety, prerequisite, or physical steps increment the version.

## Compatibility

- Consumers reference `(id, version)`, never title/slug alone.
- A retired version remains traceable and cannot be overwritten by a new meaning.
- Gate B must lock `(activity_id, activity_version)` and `(learning_objective_id, learning_objective_version)` atomically.
- Task variants explicitly identify the parent activity ID/version.
- Fixture expected outputs include exact activity IDs; changed eligibility requires a reviewed fixture/version update.

## Review states

```text
DRAFT / PENDING_OWNER_REVIEW
  -> PROVISIONAL_OWNER_REVIEWED
  -> QUALIFIED_REVIEWED
  -> RETIRED
```

Owner review is sufficient only for synthetic capstone fixtures. It must not set `production_eligible=true`.
