# FEAT directory mapping on the BE2-01–14 candidate

The sender (BE2-01–07) and receiver (BE2-08–14) allocations independently used
some of the same administrative FEAT numbers. Use the BE2 card number and full
directory name together when referring to these records:

| FEAT number | BE2-01–07 directory | BE2-08–14 directory |
|---|---|---|
| FEAT-048 | `FEAT-048-be2-vision-correction` (BE2-02) | `FEAT-048-be2-content-publication` (BE2-12) |
| FEAT-049 | `FEAT-049-be2-assistance-orchestration` (BE2-03) | `FEAT-049-be2-ai-policy` (BE2-14) |
| FEAT-050 | `FEAT-050-be2-sketch-generation` (BE2-04) | `FEAT-050-be2-knowledge-video` (BE2-08) |
| FEAT-052 | `FEAT-052-be2-sketch-review` (BE2-05) | `FEAT-052-be2-video-failure-disposition` (BE2-10) |

The names are distinct, and the current harness passes. The feature number is an
administrative prefix here; renaming either directory would invalidate references
from frozen approvals, source-pinned test runners, evidence, and handoffs. The
pre-existing FEAT-030 duplicate is unchanged.
