# FEAT-073 approval — Child profile gender and matching avatar

- Status: APPROVED
- Prepared / approved: 2026-11-10
- Approver: Project owner, direct instruction in this conversation
- Approved plan: features/FEAT-073-parent-profile-gender-avatar/plan/PLAN.md
- Plan revision: 1
- Plan SHA-256: 76623107BBEBFFC10BFD92EC3A158685816998928CAA1CD1D9C85047D0FFD36B

## Authorization recorded

The owner requested: “phần tạo hồ sơ thiếu giới tính nữa ví dụ như là giới tính nam thì avatar là đứa bé trai nếu là con gái thì là avatar đứa bé gái á”.

## Approval boundaries

- Add Nam/Nữ selection to local Parent FE child-profile creation and editing.
- Display the matching existing inline boy/girl SVG avatar at every Parent profile view.
- Keep gender in local session demo state only. Do not add API, backend, storage, persistence, analytics, SRS, AI-context, consent, or auth behavior.
- Preserve current profile workflows and existing mock avatar appearance.
- No automated tests/builds, commit, push, deployment, or publication.
