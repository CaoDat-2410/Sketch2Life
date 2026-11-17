# BE2 cross-lane integration test scaffold

This directory tracks the selected offline producer-to-consumer edges between
BE2-01–07 and BE2-08–14. `edge_registry.py` is a planning/evidence inventory;
`test_edge_registry.py` validates that inventory. Passing these registry tests
does **not** prove that any service communicates with another service.

Every edge starts `NOT_IMPLEMENTED`. A later behavior test may claim `PASS` only
after it:

1. Instantiates the actual producer and consumer application services.
2. Obtains its input from the producer service in the same scenario; it does not
   hand-construct a DTO that imitates producer output.
3. Delivers the value through the versioned public contract/port and asserts the
   consumer's committed state and lineage.
4. Exercises the edge's required stale, revocation, race, duplicate, or
   fail-closed case from the registry.
5. Records the behavior-test module and a source-pinned evidence reference.

Use deterministic fakes only at unavailable external boundaries such as BE1,
provider transport, or queue infrastructure. Do not fake the BE2 producer or
consumer under test, read/write another feature's tables directly, call a real
provider, or run a shared database. If a public contract or owner approval is
missing, leave the edge `NOT_IMPLEMENTED` and report the blocking card/decision.

Planned behavior-test modules are named in the registry and are intentionally
not created as empty or skipped tests. Existing BE2-01–06 chain evidence remains
separate and must not be counted as proof for X01–X09.
