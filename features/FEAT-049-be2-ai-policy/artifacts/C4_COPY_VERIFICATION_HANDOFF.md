# C4a — exact provider-copy receipt verification bridge

ProviderCopyReceiptVerifier.purge_receipt is a backend context manager, not a
mounted endpoint or provider dispatcher. Inputs: verified actor/org context,
strict ProviderCopyCommand, existing foundation ProviderCopy and reference/hash.
Command binds client operation key, exact data-request ref/version/hash, scope
and operation; never accepts verified/allowed/URL/provider receipt assertions.
Cancel intentionally does not become a purge receipt; typed cancel acknowledgment
and missing-hook outcomes remain open integration work.

Boundary.guard must adopt real current BE1 subject/purpose/expiry/revocation and
original exact profile provenance. Missing provenance is not replaced by latest
profile alias. Verifier authenticates actual receipt bytes/hash/issuer/operation
and exact target binding; a raw boolean or existing status report is not proof.
Returned grant/proof strictly revalidated, expiry and current unchanged authority
checked again before yield. No default numeric TTL, provider or model selected.

Inside context, foundation PurgeReceipt may be applied using existing state
transitions only in eventual authorized registry UoW with exact envelope/intent
history. Receipt outside context is metadata, not a standalone authorization or
actual-deletion proof. No registry write performed by C4a. Real owner commit fence
must enforce deadlines at commit; a held mutex alone does not freeze wall clock.

Unverified deletion maps to pending via existing foundation domain. Fixture
receipt maps to fixture_deleted_not_actual; synthetic provider-kind unit test
only checks expected mapping, not actual authenticated provider integration.
Pending/Unsupported/Exception never reported as Deleted. Backend verification
adapter must remain fixture-labelled unless genuine adopted provider evidence
was authenticated; no permissive production adapter is mounted.

Open CR_PROVIDER_COPY_ADOPTION.md records durable registry pages/coverage, original
profile version/hash storage, external operation-key deduplication/crash safety,
typed cancel acknowledgment/missing hooks and late-copy/expiry commit fencing.
It is not adopted foundation change or permission for actual provider actions.
BE1 still owns overall data-request closure; empty copy registry is not proof
of provider-wide deletion. C4b/C4c and C5/full card remain incomplete.

Verification: 44 new component cases, 532 own total PASS; 477 selected existing
regression +114 targeted foundation suites PASS. Actual PG inventory unchanged:
44 NOT_RUN. No provider API call, deletion, credential access or dispatch here.
