# FEAT-018 Person 4 cache/fallback scenario matrix

This matrix is synthetic and feature-local. It does not contain raw media,
prompts, provider output, credentials, or personal data.

| Scenario | Resolver result | Reason | Provider call |
|---|---|---|---|
| `cache-hit-reviewed` | `READY/HIT` | none | no |
| `cache-miss-unknown-key` | `BLOCKED/MISS` | `CACHE_MISS` | no |
| `cache-reject-stale` | `BLOCKED/MISS` | `STALE_MEDIA` | no |
| `cache-reject-corrupt` | `BLOCKED/MISS` | `CORRUPT_MEDIA` | no |
| `cache-reject-unsafe` | `BLOCKED/MISS` | `UNSAFE_MEDIA` | no |

The resolver result is the input to the fallback component. A miss/rejection
does not itself select another activity; fallback selection remains a separate
step and preserves the exact request identity.
