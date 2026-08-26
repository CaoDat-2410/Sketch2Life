# Evidence index

| ID | Related task | Type | Result |
|---|---|---|---|
| EV-003-T1-01 | P2-T1 | Validation and review | `notes/P2_T1_MEDIA_VALIDATION.md`: deterministic PNG/WAV validation and initial review baseline. |
| EV-003-T1-HARDENING-01 | P2-T1 hardening | Regression evidence | `notes/P2_T1_HARDENING.md`: bounded/fail-safe media parsing, PCM normalization, truthful source provenance, manifest validation, and 23 passing tests. |
| EV-003-T2-T3-01 | P2-T2/P2-T3 | Contract and adapter evidence | `notes/P2_T2_T3_ADAPTERS.md`: fixture/provider-shaped Whisper and Qwen3-VL mappings, typed failures, source preservation, and schema rejection cases. |

Future P2-T4 and P2-T5 evidence will add fusion, evaluation metrics, latency, and live-model measurements only after separate approval. No live provider call is included here.
