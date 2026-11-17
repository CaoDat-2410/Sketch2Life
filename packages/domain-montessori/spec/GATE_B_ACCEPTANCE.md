# Gate B acceptance criteria

This file specifies future Integration Sprint behavior. It does not implement UI, API, authorization, persistence, or state transitions.

## Approve proposed activity

Given a current recommendation containing an allowed activity and objective version, when an authorized parent/guide approves it at the expected session version, then both identities are locked together and an immutable approval record contains actor, timestamp, source recommendation version, and constraint evidence.

## Choose valid alternative

Given multiple allowed alternatives from the same current recommendation, when the reviewer chooses one, then the selected activity/objective pair is locked and the original proposal remains auditable. An activity absent from the allowed set cannot be selected.

## Reject

Given a current recommendation, when the reviewer rejects it with a reason, then no activity/objective is approved and experience generation remains blocked.

## Stale version

Given the session or recommendation changed after display, when approval uses a stale expected version, then the operation is rejected without mutating the newer state.

## No valid activity

Given every candidate is blocked, when Gate B data is requested, then the system returns `NO_VALID_ACTIVITY` and the relevant reason codes. It must not relax a hard rule or present a blocked choice as approvable.

## Identity lock

After approval, StoryPlan, ArtAnimationPlan, LearningExplanationPlan, ActivityHandoff, and any task variant must preserve the exact approved activity/objective IDs and versions. A fallback cannot change them.
