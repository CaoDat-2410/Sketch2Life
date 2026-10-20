# C3c1 — internal emergency stop (approved P3)

No ninth CMD-48 action, public endpoint, provider call or automatic resume.
Typed internal command: feature_scope/client_request_id/expected_epoch/reason.
Verified principal/org supplied separately. Current DISABLE capability required;
hold owner guard through same transaction scope epoch/intent/receipt commit.

Scope lock and exact epoch CAS prevent stale operator action stopping a newer
activation. Before first policy, known registry feature may be stopped with
epoch0/null pin; never report epoch0 as usable. Current known nonzero scope can
be stopped even when registry definitions/features are withdrawn, allowing safe
remediation. Unknown uninitialized feature fails and rolls back lazy scope row.
Reason required, no raw content/secret fields. Result is immutable stop metadata,
not worker cancellation/usage grant. Pending intent delivery is still separate.

Same org/principal/key/body replay checks current DISABLE and exact stopped scope
snapshot, returns recorded result without another intent. Changed body conflicts.
Old stop after reactivation must fail, never mutate new pin. New key on already
disabled exact epoch records receipt without incrementing epoch or duplicate intent.
Receipt/epoch/intent rollback together on failure; unique conflict only fresh read.
No destination/profile/budget/TTL values chosen. Numeric budget/concurrency and
actual work eligibility remain subsequent C3c work, not implied by emergency stop.
