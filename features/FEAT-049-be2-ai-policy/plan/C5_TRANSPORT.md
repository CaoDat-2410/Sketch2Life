# C5a — sole CMD-48 AI-policy binding and safe transport errors

Approved revision1 P1/P5, parent0ecff26. Bind existing AiPolicyCommand and real
AiPolicyCommands through existing StrictDelegateBinding; no parallel router or
default app/auth adoption. Existing shared response model remains unchanged.
Extend existing governance transport with closed AI-policy error mapping: precise
safe status/code for known command failures, unknown codes/private exceptions
become generic dependency-unavailable. Never echo raw error text or payload.
Preserve content/preset/core routing, strict preconditions and security headers.

Test all eight actual policy actions through injected existing HTTP factory with
MEMORY/ASSUMED authority/registry, rights/replay/revocation/stale target, malformed
input-before-effects, unknown/private errors, schema and default-unbound behavior.
This is local transport composition, not actual owner/SQL/provider integration.
C5 operational projections remain separate subsequent work; no new production
limits/profile choices, no foundation contract rewrite.
