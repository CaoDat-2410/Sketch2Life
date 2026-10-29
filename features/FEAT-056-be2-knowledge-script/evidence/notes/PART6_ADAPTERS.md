# Part 6 trusted fixture adapter mini-plan

Part4 C independently closed before source. Own files now infrastructure/knowledge_bundle/adapters.py and unit/test_knowledge_bundle_adapters.py; root owns coordinator/repository/races and ports. All fixture mutation uses the exact same coordinator instance as repository; read-only coordination_token allows composition identity guard. Lock order is coordinator then no separate adapter lock. Every input is deeply copied before publication queue; every read returns a copy/immutable tuple, no public dictionary exposure.

Behavior: deny by default. Named publish_basis/audience/source/catalog_claim/teacher/disclosure/consent/policy/mutation methods call coordinator.publish. Exact child consent/disclosure keys include organization/session and the full contributor identity/purpose/snapshot. Teacher mutation and disclosure decisions independent; policy active and session mutation independent. Read basis current by(kind,ref) to permit meaningful stale revision errors; catalog/source projections sorted by ID; source recall flows through public publish_source.

Verification: tests audit each public publication in a held unit, assert actual getter state remains unchanged until outer exit on commit and rollback; getter isolation and input-copy prevent raw alias publication; per-scope/purpose/snapshot consent never leaks; default deny and separate disclosure/mutation states. Thread wait/block and actual handler integrated races belong root tests. Focused pytest, Ruff, strict source mypy. Independent reviewer C reads actual adapter assertions; no distributed fence claim.

## A/B checkpoint

Independent atomic_review A PLAN_REVIEW_PASS, no concrete design P1/P2. Adapter source and8 focused tests implemented; inventory covers all9 named publication methods and observes both authority/consent mutation and disclosure flags inside held unit commit+rollback windows. Nested input/returned object aliases cannot mutate stored facts. Generic real guard invokes zero child consent lookups; child guard invokes one. Ruff and strict adapter mypy PASS. Initial7-pass snapshot and refined8-pass JUnit/log receipts retained locally. C requested; adapter source/test paused while reviewer pins actual snapshot. No handler/current/race integration PASS claimed from adapter-only tests.

## C closure

Independent actual source/assertion review PASS_WITH_INTEGRATION_NOTES.8 adapter tests and combined25 race+adapter tests independently PASS,0 skips, hashes stable. Reviewer raw-publication mutant applied real facts during a held unit while returning False; both commit/rollback actual-state-window assertions failed, proving oracle observes facts rather than acknowledgements. No known P1/P2 adapter findings. Integrated service/current/receipt/resolve obligations remain later parts. Adapters hash cb0733cc… and tests fb30ec44… pinned in independent review.
