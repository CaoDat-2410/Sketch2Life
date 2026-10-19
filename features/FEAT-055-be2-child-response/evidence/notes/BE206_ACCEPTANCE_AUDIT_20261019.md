# BE2-06 acceptance assertion audit — 2026-10-19

This is a read-only source/test audit of the 35 cases in the frozen Rev5 plan, not owner
acceptance or a substitute for the final pinned batch. The audit inspected the domain,
contracts, ports, service, fake repository, public adapters, harness and all six BE2-06 test
modules on the task worktree based at `818ec0778ffb044a77d95c425193f4f02fc3aa44`.

`ASSERTED` means the named tests contain the relevant concrete assertions, supported by the
source boundary where stated. It does not mean this auditor reran every named test.
Execution results and source hashes belong to the final batch receipt; a passing aggregate
test count alone does not establish assertion completeness. The earlier adapter/chain development
run passed 32 cases, with Ruff and strict source mypy passing for that owned slice.

Test aliases below are repository-relative:

- **S**: `backend/tests/unit/test_child_response_service.py`
- **R**: `backend/tests/unit/test_child_response_races.py`
- **A**: `backend/tests/unit/test_child_response_adapters.py`
- **C**: `backend/tests/unit/test_child_response_chain.py`
- **D**: `backend/tests/unit/test_child_response_domain.py`
- **K**: `backend/tests/contract/test_child_responses.py`

## Coverage map

| Case | Assertion coverage | Concrete evidence and limits |
|---|---|---|
| B6-P01 | ASSERTED | C `test_real_chain_choice_preserves_source_producer_review_and_job_counters` obtains an authorized read before the response. A `test_read_uses_one_eligibility_result_and_never_calls_child_payload` checks same-decision payload/ref and target text/asset mapping. S `test_b6_p01_response_is_content_free_and_server_attributed` checks participant, turn, server time, revision, content-free result and exactly one history/receipt/audit/event. |
| B6-P02 | ASSERTED | S `test_b6_p02_explicit_reveal_does_not_itself_record_view` and C `test_hide_reveal_is_explicit_and_does_not_record_rendering_proof` check hidden suppression, explicit reveal with unchanged storage, then explicit viewed transition. S `test_b6_p02_restoring_a_does_not_change_b_viewer_state` compares B's entire projection before/after A's restore. |
| B6-P03 | ASSERTED | C `test_real_chain_choice_preserves_source_producer_review_and_job_counters` compares the complete recorded source/canvas facts, snapshots, producer record, 05 store, job map and provider/queue counters across viewed/hide/restore/decline; C `test_two_reviewed_children_keep_independent_choices_and_turns` checks viewer isolation. No direct artifact byte-store comparison is claimed; the inspected service has no artifact-write port. |
| B6-P04 | ASSERTED | S `test_b6_n09_decline_survives_new_turn_and_review`, C `test_decline_stays_terminal_after_rebinding_same_participant`, D transition tests, and C's source/provider invariance test show terminal participant/version state and no generation. No assessment interface exists in this component; event schema rejects assessment/deficit additions. |
| B6-P05 | ASSERTED | C `test_two_reviewed_children_keep_independent_choices_and_turns` uses actual group approval, separate GA/GB principals, distinct server turns and independent hidden/viewed/declined projections. |
| B6-P06 | ASSERTED | C `test_new_approved_version_is_independent_of_old_decline` produces and reviews actual v2, checks initial null/revision 1, and preserves the old history/marker; D `test_decline_survives_changed_turn_and_review_but_new_version_is_independent` separately checks the domain key. This test does not itself assert denial of v1 receipt replay; see I05. |
| B6-I01 | ASSERTED | S `test_b6_i01_same_key_replay_has_no_new_writes`, parameterized for all three actions, compares the full snapshot and commit count and checks immutable outcome equality. |
| B6-I02 | ASSERTED | S `test_b6_i02_semantic_field_change_conflicts` varies action/turn/version/review and checks one receipt; `test_b6_i02_changed_payload_still_conflicts_after_turn_close` checks current disclosure precedence without an active-turn gate. |
| B6-I03 | ASSERTED | S `test_b6_i03_new_key_same_state_is_noop`, parameterized for all actions, checks unchanged states/history/outbox/markers/revision/attribution and exactly two alias receipts/audits. `test_b6_i03_noop_under_later_turn_preserves_original_attribution` distinguishes current-operation audit turn from the original response turn. |
| B6-I04 | ASSERTED | S `test_b6_i04_closed_turn_and_stale_etag_replay_original_receipt` and C `test_closed_turn_replay_preserves_receipt_but_new_content_or_response_is_denied` replay the original result after closure with old/changed ETag, compare storage, and deny new command/content access. |
| B6-I05 | ASSERTED | S `test_b6_i05_replay_requires_current_disclosure` covers grant revoke, review revoke and participant rebind with unchanged storage; C `test_revoke_blocks_original_receipt_and_all_future_reads` checks review/grant denial. S `test_b6_i05_old_version_receipt_and_unseen_old_command_deny_after_replacement` produces actual v2 and denies both old accepted receipt replay and unseen old-version command, comparing storage/provider/job/queue counters. |
| B6-I06 | ASSERTED | S `test_b6_i06_old_receipt_cannot_restore_later_hidden_state` returns the original viewed receipt while preserving current hidden visibility/current ETag and suppressed content. |
| B6-N01 | ASSERTED | S `test_b6_n01_actual_ineligible_states_share_denial_without_generation` covers pending/blocked/stale/rejected/missing with actual producer/reviewer setup, asserted BLOCKED/PASSED moderation, asserted reject decision, and prior authorized read followed by asserted producer stale state. It denies read/command and checks no receipts/history/events/new provider/job/queue work. A missing/cross-org tests plus C subset/revoke tests cover the other variants. Generic errors expose only an application code; no HTTP error envelope is claimed verified. |
| B6-N02 | ASSERTED | A `test_new_operation_requires_current_non_null_matching_turn` covers null/closed/wrong/revoked turns; S/C closed-turn tests assert no new mutation or read. Receipt exception remains I04. |
| B6-N03 | ASSERTED | K `test_command_rejects_identity_and_envelope_overrides` covers participant/organization/hash/audience plus invalid extras. S `test_b6_n03_raw_unknown_identity_fields_rejected` exercises raw command handling and no successful receipt. |
| B6-N04 | ASSERTED | S `test_b6_n04_unseen_key_after_real_invalidation_has_no_work` covers review/grant/version invalidation with an unseen prepared command and compares the complete 06 snapshot plus provider/job/queue counters. S I04 and R `test_b6_r01_r02_change_completed_before_validation_denies` cover turn closure/review revoke with no history/events. |
| B6-N05 | ASSERTED | A `test_allowed_turn_participant_must_match_05_participant` deliberately allows different participants in the two fixtures and checks refusal. Service inspection confirms a refused turn yields generic unavailable before its write unit. |
| B6-N06 | ASSERTED | A `test_canvas_facts_are_checked_even_when_turn_authority_would_allow` covers inactive/org/session/canvas/class mismatches, and A turn tests cover null turn. S `test_b6_n06_inactive_owner_session_cannot_use_independently_allowed05` preserves independently allowed 05 results and checks denied command/read with no response history. |
| B6-N07 | ASSERTED | S `test_b6_n07_missing_if_match_only_blocks_unseen_mutation` denies the initial operation with no history, then proves accepted receipt replay bypasses missing/current If-Match equality. |
| B6-N08 | ASSERTED | S `test_b6_n08_stale_or_foreign_etag` and `test_b6_n08_another_participant_etag_is_rejected` deny stale/family/foreign-viewer tags without history. D ETag tests bind organization/participant/proposal/version/hash/review/local revision. Error type exposes no foreign revision metadata. |
| B6-N09 | ASSERTED | S `test_b6_n09_decline_survives_new_turn_and_review` changes both turn and actual effective approval reference, rejects viewed/hidden, returns original decline disposition, and keeps one history row/content suppressed. |
| B6-N10 | ASSERTED | A `test_producer_group_audience_cannot_authorize_unreviewed_child` and C `test_subset_review_does_not_publish_group_content_to_unreviewed_child` use producer audience A/B with approval only A and deny B. |
| B6-N11 | ASSERTED | S/C hide-reveal and decline tests suppress passive hidden/declined reads; explicit read alone never records a view, and declined content remains suppressed even on explicit reveal. |
| B6-R01 | ASSERTED | R `test_b6_r01_r02_change_completed_before_validation_denies[review]` and `test_b6_r01_r02_later_change_keeps_only_historical_response[review]` exercise revoke before validation and in the local before-commit hook. The latter checks no 06 history is yet published, one historical outcome afterwards, and denial of subsequent read/receipt. |
| B6-R02 | ASSERTED | R's corresponding `[turn]` cases cover close-before/after-validation, old attribution and authorized replay after close. R `test_b6_r02_rebinding_never_relabels_or_discloses_old_participant`, parameterized before/after decision, checks rejection of A's old command/receipt after binding B, preserves A's original history/turn if accepted first, and permits only B's separate initial viewer state. |
| B6-R03 | ASSERTED | R `test_b6_r03_every_effect_rolls_back_then_retry_commits` injects failures after state/history/terminal marker/receipt/audit/event and at commit; compares the entire pre-state, then checks one retry outcome and exactly one of each record. R `test_failed_local_commit_after_turn_close_has_no_accepted_receipt_to_replay` covers failed commit followed by lost authority. |
| B6-R04 | ASSERTED | R `test_b6_r04_r05_same_etag_has_one_winner_including_initial_state[True]` checks one applied/two-thread same-ETag winner and one STALE_AGGREGATE with exact record counts. R `test_nested_commit_preserves_accepted_decline_and_rejects_outer_stale_copy[True]` additionally protects an acknowledged nested decline from an outer stale staged copy; B6-CR01 is closed below. |
| B6-R05 | ASSERTED | The same two race tests with `[False]` check virtual-revision-1 initialization under two-thread and same-thread nested ordering. The repository compares viewer revision under its lock and captured local generation before publishing. The bounded audit repro confirms the inner accepted first write remains committed and the outer write is rejected. This proves single-process behavior only. |
| B6-R06 | ASSERTED | R `test_b6_r06_same_key_concurrent_commit_replays_without_second_event` requires one applied result/one replay, identical outcomes and one receipt/history/event/audit. |
| B6-C01 | ASSERTED | All C scenarios use `build_child_response_harness`, which composes unchanged real 04/05 services over their accepted fixture harness and actual 03 authority. `approved` generates a proposal, moderates it and issues a real Teacher review; it does not install a handcrafted approved record. |
| B6-C02 | ASSERTED | S `test_b6_c02_teacher_scope_and_event_replay` checks stable one-event output after command replay, neutral action and real history IDs/turn; C `test_teacher_event_consumer_is_currently_scoped_and_content_free` denies wrong-role/org/class and withdrawn assignments and excludes text/assets/provider/job/assessment data. This verifies idempotent outbox identity plus current scoped query, not broker delivery or deduplication of processed deliveries. |
| B6-C03 | ASSERTED | S `test_b6_c03_initial_projection_has_no_fake_response_or_storage` checks null initial response/no writes; K projection/time/attribution tests reject invented available responses and cross-viewer/naive-time choices; C group tests check actual viewer isolation. |
| B6-C04 | ASSERTED | C's before/after invariant test plus inspection of domain/ports/service establish 06-only writes and no direct producer/job/canvas storage access. `git diff --name-only` showed only approved shared records/config changes, with no modified 01–05 source; new source/test paths are 06-owned. Test fixture publications intentionally mutate synthetic owner facts and are not command implementation writes. |
| B6-C05 | ASSERTED | A metadata and one-result-read tests check actual proposal version and allowlisted fields; K `test_access_snapshot_cannot_transport_full_target_fields` rejects text/audience/asset/provider/job/epoch extras; typed service/history/receipt/event fields contain no producer target and the adapter contains no logging/cache serialization of that target. No cross-owner epoch or fencing guarantee is inferred. |
| B6-C06 | ASSERTED | S `test_b6_c06_command_whitespace_property_order_is_canonical` replays differently formatted JSON; S semantic-field tests reject changed values. K fingerprint tests preserve opaque value case. S closed-turn replay with changed/missing If-Match verifies envelope exclusion and no current-ETag gate for accepted receipts. |

## B6-CR01 — P2 local nested-commit overwrite — CLOSED

The five originally partial assertion variants (P02/I05/N01/N04/R02) now have explicit source
assertions in the added S/R tests. The audit did not independently execute that entire new set;
the final pinned batch must record the actual result. All 35 planned rows now have concrete
assertions, with no remaining partial assertion row or known open audit finding in this scope.

Probe executed with the existing interpreter, task-worktree imports, synthetic actual 04/05
harness and no network or runtime services:

1. Generate and approve one proposal; prepare outer hidden and inner declined commands from
   the same virtual-revision-1 ETag.
2. Set `h.store.before_commit` to record the inner command through the same 06 service.
3. Execute the outer command and inspect committed state.

Before the fix, both returned `applied=True`; final history/receipt/event counts were one, terminal
marker count zero, final visibility hidden, and the inner accepted decline receipt was absent.
The repository's RLock allows reentry. The inner transaction publishes its staged snapshot,
then the outer unit replaces it with its older staged snapshot without checking store commit
generation. This loses a previously acknowledged terminal response and violates the fake's
local CAS/atomicity claim. Root was notified immediately; this audit did not edit source/tests.

Root fixed the fake by capturing a private local generation at transaction start, incrementing
it on each published 06 write unit, and rejecting a dirty stale outer unit before publication.
R `test_nested_commit_preserves_accepted_decline_and_rejects_outer_stale_copy`, parameterized
for virtual initial/existing state, preserves accepted inner history/receipt/event/marker,
rejects the outer command as STALE_AGGREGATE, and replays the inner receipt unchanged. Root
reported both targeted cases passing; the auditor inspected the fix/test and reran the exact
original bounded first-write probe independently.

After-fix probe result: outer STALE_AGGREGATE; inner `applied=True`; one history/receipt/event;
one terminal marker; final visibility declined; inner receipt present; inner replay true with
the original identical outcome. B6-CR01 is closed for the single-process offline fake. This
adds no cross-service or distributed fencing claim.

Runtime authority, real Teacher assignment, ticket issuance, HTTP/UI, database/Redis,
cross-process CAS/revocation, broker delivery and processed-delivery deduplication remain
NOT_RUN / NOT_IMPLEMENTED as recorded by the approved offline boundary.

## Final execution binding (root executor)

The one final required batch ran after the audit/fix and passed all15506 test cases with0 skip/failure/error; the complete01–06 selection passed1322 and skipped3 existingPillow live-app checks. All35 asserted rows were included in those six06 modules. JUnit SHA256 79a12a6bbfb95f2d9d1dcf8261ed831204213d556eeab9a438d09e9f1aaeea6d. The added same-key nested-unit regression also confirms authorized winning receipt replay after outer rollback. See BE206_IMPLEMENTATION_EVIDENCE_20261019.md for environment, exact snapshot and honest runtime limits.
