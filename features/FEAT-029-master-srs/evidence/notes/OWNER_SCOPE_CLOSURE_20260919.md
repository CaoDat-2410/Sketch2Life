# FEAT-029 owner scope closure evidence — 2026-09-19

## Purpose

Record the owner answers that closed the Parent/Guide/ChildProfile relationship, Parent Web, session revoke, retention, audit and observability scope for the master SRS.

## Owner-confirmed decisions

- MVP contains personalized animation, narrated story and learning micro-video.
- One Owner Caregiver owns each ChildProfile; one owner may create many ChildProfiles.
- Child has no account or credential.
- A ChildProfile can have multiple Guide assignments, including overlapping active assignments.
- Guide share duration is 3, 7, 15 or 30 days and becomes effective immediately.
- Parent can revoke Guide at any time.
- Parent assignment notifies Guide; Admin assignment notifies Parent and Guide.
- Guide session notifies Parent and exposes a live, redacted projection.
- Revoke during an active Guide session stops the session and shows an on-screen message.
- One Guide runs one session at a time.
- Parent Web is Phase 2 for management, monitoring and child information updates, using the same backend authorization.
- Retention 30/60/90 applies to all child/session data classes; expired data becomes inaccessible archive before purge.
- Audit retention is separate from child-data retention.
- Notification uses combined channels.
- Admin raw access is break-glass.

## Legal source check

The SRS records a legal constraint review of Nghị định 13/2023/NĐ-CP. The reviewed text states child best-interest and consent requirements, conditions to stop processing/delete child data, and a general 72-hour handling rule for valid deletion requests subject to legal exceptions. No universal statutory 30/60/90 retention period was found. This is a requirements constraint, not legal advice; production needs privacy/legal review.

Sources:

- https://vbpl.moj.gov.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=161106&Keyword=
- https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-dinh-13-2023-nd-cp-bao-ve-du-lieu-ca-nhan-119230516104357809.htm
- https://vbpl.moj.gov.vn/vanphongchinhphu/Pages/vbpqen-toanvan.aspx?ItemID=11044

## Result

The decisions were added to `artifacts/Sketch2Life_Master_SRS.md` v1.3 in B20–B29. No runtime code, provider, cloud resource, contract migration, real child data or pre-existing user file was changed.
