# BE2-07 supplemental implementation approval — DRAFT

- Status: APPROVED — supplemental offline scope only; official record in TASK_APPROVAL.md
- Scope: plan/CROSS_LANE_BE2_07_SCOPE_DRAFT_20261021.md
- Current draft SHA256: CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24
- Approval must pin the reviewed final bytes; this draft hash is not an approval.
- Existing authority: TASK_APPROVAL.md and component acceptance remain unchanged;
  neither proves the cross-card source-fence behavior proposed here.

## Decision requested

Approve or reject the exact proposed FEAT-056 delta: expose producer-owned exact
source identity/currentness through a public typed boundary, reject stale or unknown
currentness, and agree with BE2-08 on a fence/revalidation protocol that is actually
valid through its finalizer commit.

Approval does not authorize a process-local mutex as a durable fence, direct consumer
table reads/writes, a new migration, X02, BE2-09 X05d, X05c/CR09-02, Modal,
Lightning/runtime, publication, or a status/acceptance change. If no durable adopted
protocol is selected, X01 remains PARTIAL.

## Owner response

- Approver: project owner
- Exact response: see verbatim owner approval below and TASK_APPROVAL.md
- Date/time and timezone: 2026-10-21, Asia/Saigon; exact message timestamp not independently asserted
- Frozen plan SHA256: CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24
- Frozen allowed-file manifest: Candidate paths in the approved scope; the minimal execution subset must be recorded before editing. New/unlisted paths require renewed approval.

The owner approved this exact scope in the current Codex chat. The official approval
is in TASK_APPROVAL.md. Preserve the existing task approval and component acceptance.

### Verbatim owner approval

> Duyệt scope BE2-01, BE2-07, BE2-08, BE2-09 và BE2-14 theo đúng nội dung và SHA trong hồ sơ. Chỉ làm offline. Giữ X05d BLOCKED, X05c/CR09-02 mở; không chạy Modal, Lightning, provider hay runtime.
