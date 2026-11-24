# Rev39 — offline decoder verification

- **Date:** 2026-11-20 (Asia/Saigon).
- **Plan/approval:** Plan Revision 39; Addendum 63.
- **Scope:** Parent activity punctuation decoder only; no model inference was sent in this checkpoint.

## Results

- Focused Parent activity tests: **21 passed, 40 deselected**.
- Full `test_qwen35_lesson_suggestion_contract.py`: **60 passed, 1 failed**. The unrelated failure is `test_drawing_candidate_parser_rejects_extra_text_and_duplicate_keys`: its test fixture omits `confidence`, while the current drawing parser requires `candidate_subject`, `visible_features`, and `confidence`. No drawing source or test was changed under this plan.
- Python compilation and `git diff --check`: passed.
- CPU probe against the installed LM Format Enforcer **0.11.3** using the worker's real JSON schema parser and token enforcer: passed. After 147 decoder callbacks, the required prose field blocked both the standalone quote and a token that combines text with a closing quote before punctuation; after a period was generated, the standalone quote became available. The probe did not load model weights, use a GPU, or call Modal.
- Task API container `s2l-feat081-rev23-api-1`: running; `http://127.0.0.1:58100/health` returned `{"status":"ok","service":"sketch2life-api"}`.
- Android emulator `emulator-5554`: connected.

## Next gate

Deploy only the language/audio Modal app, run its approved CPU readiness check, and—only if both pass—send exactly one fresh activity request through the authenticated Parent UI. No retry is authorized by Addendum 63.
