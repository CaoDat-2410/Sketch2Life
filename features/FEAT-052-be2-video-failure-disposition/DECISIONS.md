# BE2-10 planning decisions

2026-10-19 D01: "tiếp" means inspect/plan next card, not approve unseen revision.
D02: DATA-28 and CMD-43 run-revision If-Match remain distinct from09 review ETag.
D03: terminal08 row/01 job never resurrected; retry new lifecycle mapping is CR10-01.
D04: intent persisted before side effect; ambiguous outcome uses separate candidate
pending202, not invented confirmed DATA-28 fields or implicit retry/cancel/rollback.
D05: one disposition winner across actions/actors; actor-key dedup alone insufficient.
D06: end requires actual early outcome/checkpoint receipt; skip not generated/success.
D07: bounded retry consumes adopted authorization at owning effect; note not grant.
D08: CR10-01/02/03 deferred owners explicit; no direct SQL/budget numeric defaults.
D09: after exact plan approval finish internal P1–P4 in one continuous workflow,
commit meaningful clusters without repeated approval stops. External gates stay open.
