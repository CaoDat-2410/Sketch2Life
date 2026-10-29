# C6d — approved actual local PG17 pack

Parent0e192da, owner direct approval2026-10-18. Existing Python environment only.
Official portable PostgreSQL17.11 EDB archive, previously recorded SHA256
80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f.
Compare downloaded bytes; mismatch stops. Hash is byte identity, not independent
publisher signature claim. Unique ignored runtime, current-user ACL, random secret
files/SCRAM, loopback IPv4 random free port. No Windows service/global PATH.

Bootstrap only own cluster; runner role nonsuperuser/CREATEDB/no CREATEROLE. Run
four source-pinned packs15+10+21+58=104 sequentially, retain raw FAIL/PASS separately,
read first root failure before fixes/retry. Actual tests create/drop own random DBs.
No shared/prod DB or fixture-as-runtime claim. Stop exact cluster then validate
cleanup targets under unique runtime directory before removing data/binaries/ZIP/
secret files; preserve redacted logs/summary. Do not delete runtime/workspace root.
Update evidence/status/acceptance with actual results, rerun local pack/security
and scoped commit. Full integration still open, no card/goal DONE.
