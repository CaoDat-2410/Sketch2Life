# Task approval

Status: APPROVED

Feature: FEAT-033 — Montessori profile form and workflow recovery
Plan: `plan/PLAN.md`, revision 3
Plan SHA-256: `9AE60C76F63DD351BD3E94F154BAC200EE65295F898129F097DBC51BA059FC2E`
Approver: Project owner
Approval timestamp: 2026-09-29 (Asia/Saigon)
Approval record: User explicitly instructed “triển khai plan trc đi, các plan trc” after review of the FEAT-033 flow and the catalog benchmark. This is recorded as approval of revision 3 and its exact hash above. The hash was refreshed after the approved plan's lifecycle status changed to `APPROVED`; objectives, acceptance criteria, scope, and exclusions are unchanged.

The owner's prior approval covered the earlier FEAT-018/020/030 integrated profile-and-rig plan. This proposal adds AI classification of free text, removes current progress/supervision profile fields, changes readiness sequencing, addresses a newly observed validation failure, and adds targeted catalog and performance work. Those are material scope changes and are not authorized by the earlier approval.

Approval scope is limited to the objectives, acceptance criteria, constraints and exclusions in `plan/PLAN.md` revision 3. It does not authorize expanding the catalog merely to match the 3,000+ counts advertised by broader Montessori curriculum libraries, persisting child profile data in this increment, or changing unrelated Pixi/SAM flows.

## Approved scope amendment — revision 4

Status: APPROVED
Feature: FEAT-033 — Montessori profile form and workflow recovery
Plan: `plan/PLAN.md`, revision 4
Plan SHA-256: `3F09467BAFB1DF473B479A08DC94F96BCCE3DE78BAA43541C41589ADD5EAE3BB`
Approver: Project owner
Approval timestamp: 2026-09-30 (Asia/Saigon)
Approval record: In response to the exact scope question, the owner selected “Bỏ checklist, vẫn lọc hoạt động đủ điều kiện” (“Remove the checklist, still filter eligible activities”).
Approved delta: Remove the bulk preselection readiness/material/supervision checklist. Present the bounded normal activity shortlist first; after selection, ask only for that activity's missing applicable conditions. Keep every authored catalog, age, readiness, prerequisite, material, supervision, policy, and safety hard gate. Never infer an unknown requirement as satisfied; if a choice fails, explain and return to the shortlist. Do not alter unrelated Pixi/SAM flows or persist profile data.

## Approved scope amendment — revision 5

Status: APPROVED
Feature: FEAT-033 — Montessori profile form and workflow recovery
Plan: `plan/PLAN.md`, revision 5
Plan SHA-256: `2BA07600A426A6EF11960974AA9ECA3D45A047A6265237C664AA164F6E7905A0`
Approver: Project owner
Approval timestamp: 2026-09-30 (Asia/Saigon)
Approval record: The owner clarified: “cái gợi ý hoạt động đó ko cần làm check list đâu, cứ cho thẳng ra list hoạt động như trc là đc nhé, ko cần phải thêm gate trung gian vào như v để cho nó bị bug”.
Approved delta: Remove not only the bulk checklist but also any per-activity pre-gate and separate “check conditions” action. Automatically load the normal activity list after Gate A, show only activities already passing backend hard eligibility filters, and retain the existing adult activity review/approval before start. Unknown readiness/material data still fails closed; use the current session's explicit adult/caregiver participation for supervision policy. If no activity qualifies, explain and return to initial profile/topic selection rather than inserting a checklist. This amendment supersedes revision 4 only on the intermediate/per-activity gate sequence; all other revision 4 constraints remain.

## Approved scope amendment — revision 6

Status: APPROVED
Feature: FEAT-033 — Montessori profile form and workflow recovery
Plan: `plan/PLAN.md`, revision 6
Plan SHA-256: `38ABFEA1FA88E262C7445D60C5FDE90A49B376F8E6055F4EC13A925F2F4CD47D`
Approver: Project owner
Approval timestamp: 2026-09-30 (Asia/Saigon)
Approval record: The owner directed: “fix lại cái đó đi, ko đc hiển thị ko có hoạt động như v, fix lại luôn cái đó đi, bỏ cái readiness,... ấy luôn, đảm bảo ra full list hoạt động phù hợp chủ đề”; then added “thêm cái là lọc theo sở thích của trẻ đồ nữa, như cái hồ sơ ấy, ko chỉ cho ra 3 hoạt động phù hợp”. This is explicit authorization to implement the specific revision 6 scope.
Approved delta: Automatically show the complete reviewed activity set matching Gate-A topic and exact age; do not cap at three. Use adult-confirmed profile interests/dislikes to personalize ordering/explanations inside that full set, without topic drift or suppressing otherwise matching activities. Remove child readiness, completed-history, and material-availability questions/filters from discovery; display material needs as preparation information after selection. Preserve catalog status, exact age, confirmed topic, authored safety/policy, adult participation, under-three caregiver/direct-supervision rules, and adult review before start. Version contracts additively and record an ADR; do not mutate existing V1–V3 contracts. No durable child-profile storage, unrelated flow changes, or commit/push is authorized.
