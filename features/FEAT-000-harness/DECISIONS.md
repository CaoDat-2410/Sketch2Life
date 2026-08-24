# Feature decisions

1. Use a feature-local evidence directory to keep audit trails attributable.
2. Keep a global context ledger plus feature-local context because project-level invariants and feature-specific assumptions have different lifecycles.
3. Enforce gates with a lightweight standard-library validator so the harness does not depend on the final tech stack.
