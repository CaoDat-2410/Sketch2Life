# Montessori domain glossary

| Term | Canonical meaning | Authority/version rule |
|---|---|---|
| Activity | One concrete, prepared physical task with objective, readiness, materials, steps, safety, and review state | `ACT-nnnn` plus integer version |
| Concept | A stable curriculum/interest concept used to connect confirmed meaning to objectives | `CONCEPT_*`; version when semantics change |
| LearningObjective | The single approved learning direction an activity supports | `OBJ_*` plus integer version |
| Prerequisite | A required prior activity, skill, or readiness condition | Hard prerequisites block eligibility; soft relationships never bypass hard rules |
| SafetyRule | Deterministic condition governing hazard, supervision, and block/allow outcome | Machine-readable reason code; evaluated before ranking |
| MaterialOption | One required material group with one or more permitted alternatives | At least one available option is required for a required group |
| TaskVariant | A delivery variant explicitly mapped to its parent activity/version | Cannot silently change activity or objective identity |
| AgeBand | Review classification `0-3`, `3-6`, `6-9`, or `9-12` | Classification aid; exact age/readiness fields remain authoritative |
| ReadinessTag | Observable prerequisite capability, never a personality inference | Missing required tag blocks that candidate |
| ConstraintDecision | Per-activity allowed/blocked result with all applicable hard-rule reason codes | Deterministic and reproducible |
| NO_VALID_ACTIVITY | Valid outcome when no candidate survives hard constraints | Rules are not relaxed to force a result |
| Gate B | Future adult review that locks activity and objective IDs/versions together | Specification only in Sprint 1 |
| ActivityHandoff | Versioned instructions ending digital playback and starting the physical task | Must preserve approved activity/objective identity |
| PENDING_OWNER_REVIEW | Draft fixture awaiting owner review | Never production eligible |
| PROVISIONAL_OWNER_REVIEWED | Owner accepted the record for capstone fixture use | Still not qualified pedagogical approval |
| QUALIFIED_REVIEWED | Future state after review by a qualified Montessori reviewer | Required, with separate production/security gates, before production eligibility |

## Language policy

Machine IDs, enum values, schema keys, and reason codes use English ASCII. Reviewer-facing titles, steps, safety notes, and handoff content use `vi-VN`. Display translations cannot change identity or rule semantics.
