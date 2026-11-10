# School Manager web remediation — contract inventory

Date: 2026-11-10 (Asia/Bangkok)
Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
Branch: `codex/fe-ui-web-remediation`
Plan: FEAT-066 revision 4, approved before code changes; SHA-256 `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`
Product baseline: canonical FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; unsigned draft. §§1–31 are the target requirements; §32 is not used as product requirements.

## Read-only API/contract audit before implementation

No backend or provider was started or called. This is a source/contract inventory only.

| School Manager flow | Contract evidence in this branch | FE-only disposition |
|---|---|---|
| M01 public lesson review | Existing Lesson Library access-grant list and decision endpoints; existing `ManagerApiReviewPage` uses `backendApi.accessGrants` and `decideAccessGrant`. | Keep the real API path. Fix only the local fixture outcome counts/wording; child media remains hidden. |
| Class list | BE1 `GET /api/be1/v1/organizations/{organization_id}/classes`; existing `backendApi.classes` and manager API page. | Supported; keep API-backed list. |
| Class creation within capacity | BE1 `POST .../classes` accepts `display_name`; `be1_registry.create_class` creates a row without a capacity entitlement/check. No capacity-summary contract was found. | Do not submit class-create requests. Show unavailable until server-side capacity enforcement/contract exists. |
| Class archive/suspend | No class archive/suspend endpoint was found in the checked mounted BE1 OpenAPI and router. | Unavailable; dependency recorded. |
| Teacher assignment | BE1 create/revoke assignment contracts exist (`POST/DELETE .../assignments`), but the manager client only exposes current user's assignment read and the checked API has no organization teacher-directory/search contract. The write payload requires an opaque `subject`. | Do not invent identity or provide a misleading assignment form; show unavailable until teacher discovery/selection is supported. |
| Roster | BE1 `GET .../classes/{class_id}/profiles` exists; `backendApi.profiles` is already available. It returns profile fields and the server filters by assignment/effective consent. | Add read-only roster display from this contract. Show display name only; do not display child media or call the endpoint during local visual review. Full add/edit/transfer lifecycle remains unsupported in the Manager flow. |
| Organization billing, invoice, payment, subscription | No compatible billing/payment endpoints were found in the checked mounted OpenAPI/routers. SRS prices and some commercial policy remain open. | Unavailable; no price, policy, payment, invoice, or subscription state is fabricated. |
| Organization quota summary/top-up | No compatible organization quota-summary or purchase API was found. | Unavailable; remove local quota mutation/success behavior. |
| Notification inbox | No compatible in-app inbox API/route was found in the checked API surface. | Replace bell/unread dot with a clear non-interactive unavailable status. |
| School Manager feedback reply | Existing session-feedback endpoint is unrelated to school-scoped lesson feedback threads; no manager reply contract was found. | Unavailable; do not present a reply action as working. |

Relevant SRS requirements include FR-T-02/03, FR-B-01–14, FR-PL-22, §21.5, AC-58 and NFR-36. The current SRS leaves commercial values/open decisions unresolved; no values are inferred here. This inventory covers only the current checked API surface, not unstarted backend capabilities.

## Review and implementation evidence

The original audit note and screenshots remain unchanged as pre-remediation evidence. Post-remediation observations and limitations are recorded below.

## FE implementation and local UI review

Reviewed on 2026-11-10 against plan revision 4, after implementation, using the existing Vite preview from the requested worktree at `http://127.0.0.1:5173/` (confirmed process command line points to `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation/apps/school-manager-ui`, bound to `127.0.0.1`). The headless review browser bound only to loopback `127.0.0.1:9233`; the helper blocked HTTPS and backend localhost URLs. No backend or provider was started or called.

Screenshots are stored under `evidence/screenshots/remediation-before/` and `evidence/screenshots/remediation-after/`. Each after route has desktop 1440x900 and narrow 390x844 captures: `/login`, `/m01-publication-review`, `/m02-organization-management`, and M02 sections `teachers`, `classes`, `quota`, and `settings`. Before screenshots remain preserved.

Observed results:

- M01 request-change interaction: toast explicitly says the change is local preview state; the next state shows `Chờ duyệt: 2`, `Đã duyệt: 0`, `Yêu cầu chỉnh sửa: 1`.
- M01 tab accessibility: each `tab` has a unique `id`, `aria-controls`, `aria-selected`, and roving `tabIndex`; each `tabpanel` points back through `aria-labelledby` and inactive panels are hidden. ArrowRight from the first tab moved focus and selection to the second tab and showed its linked panel. The tabs are keyboard-focusable.
- Header: inbox is a static `role=status` message (`Hộp thư chưa khả dụng`) with no unread dot or click affordance. Organization context is a non-interactive `DIV` with no dropdown indicator.
- M02 narrow layout: no page-level horizontal overflow at 390px in captured routes. Class title and action row wrap; the create button remains fully within the viewport and marked unavailable. Quota actions wrap to multiple lines and remain fully within the viewport. The class table sits in an explicit horizontal-scroll wrapper at narrow width.
- Login labels and required email field remain present at both sizes. Screenshot review found no remaining title/button overlap or clipped quota control.

The preview still contains pre-existing synthetic summary/table fixtures, consistently marked `Xem thử · Dữ liệu minh họa, không lưu`; unsupported controls no longer mutate them or display a success toast. The actual API-mode route was not exercised because that would require an authenticated backend session. API-mode roster is implemented read-only through the existing profile-list contract, but is not visually verified against real records. No child media/story is fetched or displayed.

Automated tests/builds were not run, as requested. Repository validators and final Git status are recorded in `status/STATUS.md` after completion.