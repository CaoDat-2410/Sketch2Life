# C4b closed dispatch / strict owner binding — implementation detail

Within approved revision 1: finish BE2-12's fixed routing and typed delegation
boundary without implementing BE2-13/14/BE1 business logic or inventing their
stage/policy payload semantics. User clarified receiver owns 08–14; absence of
those implementations is not a reason to stop all BE2-12 component work.

Fixed routes: learning_content, preset, policy/ai, policy/core. Fixed eight DATA-33
actions. A selection parse is routing-only, NOT full payload approval. Content
always uses its existing strict action union and service. A missing owner binding
returns a typed unavailable error with no writes and no owner call. Unsupported
kind/action/policy-kind is invalid, not a fallthrough.

An installed owner binding declares a concrete strict frozen Pydantic command
model/validator and typed handler. Validate full JSON with that model, reject
extras, and compare shared envelope with selected route before invoking handler.
The handler receives the concrete model, never a passthrough dict or raw body.
The owning handler must revalidate independent current capabilities, receipt/CAS
and policy through commit; dispatcher supplies verified principal/org separately.
Delegate response is strict DATA-33 metadata and is checked for scope/kind/target.

This supplies a component integration seam and conformance fixtures now. It does
not claim complete preset/policy payload schema adoption from a routing selector,
or turn fixtures into real authority/owner implementation. Owner-specific stage/
policy models can be bound when their separately approved cards define them.
No dynamic branch/plugin registry, no second HTTP route, no direct foreign SQL.
