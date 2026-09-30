# Feature decisions

## Owner-approved preview/mask follow-ups (2026-09-30)

- Subsequent owner choice supersedes initial full-list presentation only: show three ordered cards first, with “Xem thêm” for all remaining eligible cards. Backend catalog filtering/ranking and adult selection are preserved.
- Invalid mask handling is fail-closed at worker selection and backend artifact admission. Keep renderer's 75% maximum; do not crop/truncate oversized masks or hide rejection by animating the whole drawing. Synthetic validation does not imply segmentation quality or external deployment success.
- Local backend restarted after 65 passing focused tests. External worker deployment and a fresh session remain necessary. Owner subsequently requested commit/push of these follow-ups; unrelated feature edits and local runtime logs are excluded.

## Approved decisions — plan revision 1 (2026-09-30)

1. Review and correct all 300 active catalog mappings/cards; first repair topic-to-concept aliases and contaminated tags before increasing catalog quantity.
2. Candidate common static inputs are JPEG, PNG, WebP, and HEIC/HEIF; a format is supported only after the pinned app runtime passes the fixture/device matrix. Animated and RAW formats should fail with a clear reason in this scope.
3. Preserve the current backend admission safety limits unless performance/fidelity measurements justify a separately reviewed change. Normalize to the existing JPEG/PNG backend contract while retaining immutable source/derivative provenance.
4. Add animal activities only for demonstrated age/topic coverage gaps and qualified pedagogical review; do not generate activities dynamically with AI.
5. Owner-selected plan behavior: render the full eligible list immediately, then make one bounded backend AI request to highlight/rank the top three without hiding the rest. If AI ranking is slow or fails, retain the deterministic safe list and disclose that ranking is unavailable; do not retry automatically. Plan revision 1 has since been explicitly approved at the exact hash in `approvals/TASK_APPROVAL.md`. Keep exact topic/age match, session-only profile, and approved safety/adult-presence gates in either path.

## Implementation decisions/findings (2026-09-30)

- Corrected explicit family-level semantic ownership before considering catalog expansion. No new Montessori activity content was added: no qualified reviewer signed off on a new age-specific activity.
- The automated full-catalog report labels 77 records `CORRECT` only where an explicit code-level topic correction is present; 223 records remain `NEEDS_REVIEW` until qualified pedagogical review. Never treat `DEMO_REVIEWED` metadata or a generated report as that sign-off.
- Four structural general-animal cards appear for age band 3–6. Keep this as a recorded coverage gap candidate; no synthetic fifth activity was authored to satisfy a count.
- Image processing has bounded client-side prechecks and one normalization attempt, plus server-side content-sniffing/admission. Native decoder behavior remains unverified on device in this pass, so supported-format claims must remain conditional on the device matrix.

These decisions are implementation-authoritative within plan revision 1. Any cross-feature contract change beyond the approved scope requires a versioned contract/ADR and renewed owner approval.
