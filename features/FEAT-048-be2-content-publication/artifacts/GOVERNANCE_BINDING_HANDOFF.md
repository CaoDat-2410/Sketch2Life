# CMD-48 fixed dispatcher and strict binding — candidate 0.1

User clarified receiver owns BE2-08–14, sender owns 01–07. The absence of future
13/14 implementations does not block all BE2-12 work. This checkpoint provides
the receiver-owned dispatch/validation seam without implementing those cards.

## What exists now

- Fixed routing: learning_content, preset, policy/ai, policy/core; no open plugin
  registry. Unknown branch/action/policy-kind is invalid.
- Existing content action DTO union and ContentCommands remain unchanged.
- StrictDelegateBinding[ConcreteOwnerCommand] binds a strict frozen extra-forbid
  model and DelegateHandler[ConcreteOwnerCommand]. Handler receives that model,
  never raw JSON/dictionary, plus separately verified principal/org and record CAS.
- Full bound owner model validates before handler call; common target ID/version/
  hash, retirement/change reason and publish review set are checked first too.
- Shared selection parse is routing-only, NOT full owner payload validation. An
  unbound recognized owner route fails GOVERNANCE_DELEGATE_UNAVAILABLE without
  calling owner/content.
- Strict delegate result metadata checked for scope/kind/policy/target; invalid
  responses are hidden behind GOVERNANCE_DELEGATE_INVALID_RESPONSE. Owner handler
  owns transaction/authorization/CAS/receipt semantics, not dispatcher rollback
  after an already committed owner mutation.

## Single HTTP factory

build_governance_commands_router(dispatcher, resolve_identity, max_body_bytes=...)
creates one POST /api/collaboration/v1/governance/records. The older content
factory is a compatibility wrapper to this same factory, not a second route.
Do not mount both. Default application remains unchanged pending real identity/
authority composition. No demo header identity and no competing delivery GET.

Bound model schemas appear inline in OpenAPI alongside the content schema.
When unbound, no fictitious complete preset/policy body schema is published;
recognized route returns safe typed 503. Unknown routing remains 422.

## Binding example for later receiver-owned card

```python
# OwnerCommand is defined/reviewed by the owning card, not a generic JSON model.
binding = StrictDelegateBinding(OwnerCommand, owner_handler)
dispatcher = GovernanceDispatcher(content_service, ai_policy=binding)
# Preset/core slots are independent. No DB access to those owners from dispatcher.
```

Executable fixtures: tests/contract/test_governance_dispatcher.py and
test_governance_http.py. Minimal FixturePreset/FixtureAi/FixtureCore models are
explicitly synthetic, not proposed final stage_rules/policy payload semantics.
They prove typed routing, exact shared envelope, rejection before effects,
independent slots, unavailable behavior, response scope and one HTTP path.

## What still needs adoption

Complete owner-specific write/review models and business handlers bind when the
separately approved 13/14/BE1 card defines them; do not treat the routing selector
as a complete final DATA-33 union. Current owner rights/source/review fencing and
recall/audit consumer delivery still require their real adapters and conformance.
This supplies component readiness, not full-card DONE/production integration.
No new owner permission or business field inferred. No new GPU/runtime required.
