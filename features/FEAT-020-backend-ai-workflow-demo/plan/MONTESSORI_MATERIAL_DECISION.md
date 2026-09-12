# FEAT-020 Montessori Material Decision

## M-020-02 — Primary material before household substitute

**Status:** confirmed
**Date:** 2026-09-12

For each selected activity, the backend first evaluates the concrete `PRIMARY` material from the golden catalog. If it is unavailable, the workflow may select only the concrete household `SUBSTITUTE` defined by that same activity record, including its suitability and prohibited-substitution rules.

The workflow must not invent a new substitute, silently relax a safety constraint, or choose a generic material merely to avoid a no-result outcome. The selected material kind, material ID/version, suitability, and safety decision must be present in the context/handoff manifest.
