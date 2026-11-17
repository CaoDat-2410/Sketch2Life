# FEAT-025 decisions

## D-025-01 — Composition root owns infrastructure construction

Status: accepted

`BackendAiWorkflow` will receive catalog, media, and asset dependencies through
application-owned ports. Concrete loaders and file inspectors remain outside
the application layer.

## D-025-02 — 3D request is gated

Status: accepted

The repository has no current 3D runtime/source. No 3D implementation will be
added until the user clarifies whether the request means missing 3D capability,
a named work item, or another polish requirement.
