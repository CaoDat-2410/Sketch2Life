# FEAT-002 decisions

- Hard age/readiness, prerequisite, safety, and material rules run before model selection.
- No-valid-activity is a valid outcome; constraints are never relaxed silently.
- Gate B locks activity and learning-objective IDs/versions together.
- Sprint 1 produces specifications, fixture data, a deterministic harness, and acceptance criteria; recommendation/Gate B runtime is excluded by ADR-0006.
- Catalog records carry source provenance and reviewer status. Schema-valid records are not automatically pedagogically approved.
- Supported scope is under 13: 0-3, 3-6, 6-9, and 9-12 review bands. Activities for 0-3 are caregiver-led.
- Catalog target is 100 required activities plus up to 100 stretch activities, capped at 200.
- Machine IDs and schema field names are English; reviewer-facing content is `vi-VN`.
- Until a qualified Montessori reviewer is available, the project owner may mark records `PROVISIONAL_OWNER_REVIEWED`; this is not production pedagogical approval.
