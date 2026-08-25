# Golden Activity v2 field guide

Golden records are complete candidate replacements for one FEAT-002 activity version, not implicit patches. The FEAT-002 v1 record remains immutable and traceable through `base_ref`.

| Field family | Meaning and review rule |
|---|---|
| `id`, `version`, `base_ref` | Activity identity is unchanged; candidate version is 2 and carries the canonical checksum of its exact v1 parent record. |
| `age_months` | Narrow provisional guidance inside the original age band. Readiness and safety remain authoritative. |
| `purpose_vi`, `direct_aim_vi`, `indirect_aims_vi` | Explain why the activity exists without diagnosing or scoring a child. |
| `objective_mapping` | Exactly one primary and at most two secondary objective IDs/versions. |
| `readiness_criteria` | Observable prerequisite behavior; no personality, emotion, disability, or developmental diagnosis. |
| `prerequisite_activity_ids`, `progression_successor_ids` | Explicit acyclic preparation/progression links. They never bypass hard eligibility rules. |
| `prepared_environment_vi` | Exact placement, quantity, and environmental preparation before invitation. |
| `material_group_ids` | Required group resolved through the golden material registry to a concrete primary or household substitute. |
| `presentation_steps_vi` | Adult's slow, ordered presentation; content must be activity-specific. |
| `child_work_cycle_vi` | Actions the child may perform independently after presentation. |
| `restoration_steps_vi` | How the environment is returned to a safe ready state. |
| `isolation_of_difficulty_vi` | The one principal difficulty isolated by material/presentation. |
| `control_of_error_vi` | Observable feedback in the material/result, not adult praise or correction. |
| `duration_minutes`, `repeatability_vi` | Range and stopping/repetition guidance, never a performance target. |
| `safety`, `policy_constraints` | Supervision, hazards, stop conditions, prohibited substitutions, and caregiver policy. |
| `variants` | Support/standard/extension keep activity and objective identity and cannot weaken constraints. |
| `completion_observations_vi` | Non-evaluative observations of process/support/environment; no inferred psychology. |
| `review`, `provenance` | Golden candidates start pending owner review and remain non-production after provisional acceptance. |

## Version rule

Any accepted semantic change to age, readiness, materials, objective identity, steps, control of error, or safety increments the activity version. Display-only typo corrections are recorded in provenance and reviewed for fixture impact.
