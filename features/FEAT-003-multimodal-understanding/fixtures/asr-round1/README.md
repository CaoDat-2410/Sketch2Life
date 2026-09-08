# ASR Round-1 local fixture layout

This directory contains the versioned manifest contract and documentation only. It does not
contain audio, transcript contents, credentials, or model/runtime files.

The selected local fixture source should use this layout:

```text
asr-round1/
├── manifest.example.json
├── audio/
│   ├── vi_clear/<fixture-id>.wav
│   ├── non_vi_clear/<fixture-id>.wav
│   ├── vi_en_code_switch/<fixture-id>.wav
│   ├── silence/<fixture-id>.wav
│   ├── noise/<fixture-id>.wav
│   └── noisy_speech/<fixture-id>.wav
└── transcripts/<fixture-id>.txt
```

`source_audio_ref` and `reference_transcript_ref` are POSIX-style references relative to this
directory. They identify local payloads but do not embed payload content. Every reference is
paired with a lowercase SHA-256 digest. The manifest entry's `data_provenance` is exactly
`SYNTHETIC` or `LICENSED`; no real-child data is permitted.

Speech entries (`vi_clear`, `non_vi_clear`, `vi_en_code_switch`, and `noisy_speech`) must
declare expected language metadata and a paired reference-transcript ref/hash. A
`vi_en_code_switch` entry declares `expected_language: "vi"` plus
`expected_languages: ["vi", "en"]`, and sets `language_accuracy_eligible` to `false`; its
WER/CER eligibility may remain true. Single-language speech entries use one expected language
and may be language-accuracy eligible. For `non_vi_clear`, the primary language subtag must
not be `vi`, so both `vi` and `vi-vn` are invalid. Silence and noise entries have no expected language,
transcript reference, or WER/CER/language-accuracy eligibility. Every `noisy_speech` entry
names a `noise_condition_id`; a matching noise-only entry is required, and each clear speech
language must have noisy-speech coverage.

Every entry also declares `expected_speech_present` (`true` for the four speech scenarios,
`false` for `silence`/`noise`), a coarse `duration_band` (`under_3s`, `3s_to_8s`, `8s_to_15s`,
`over_15s`), and `split` (`DEVELOPMENT` or `HELD_OUT`). Round-1 execution evidence is computed
and reported per split; a `DEVELOPMENT` result is never blended with a `HELD_OUT` result in an
aggregate metric.

The normalizer version is recorded at manifest level and is `vi-asr-normalizer-v1` for this
package. Set manifest `status` to `READY` only when all required slices and metadata are
present. `TEMPLATE` is valid for the empty example but cannot produce a runnable plan.

No fixture source has been selected in this change. Phase B approval already includes the
controlled live Round-1 execution; the only remaining `DECISION_REQUIRED` item is whether
the source is synthetic/TTS or licensed speech, followed by supplying compliant local
payload and reference-transcript refs/hashes. Local payload directories remain ignored and
must never be copied into feature evidence.
