# FEAT-021 Decisions

1. V2 is canonical; V1 is derived compatibility output.
2. ASR child narration has priority over VLM-only background concepts when confidence is sufficient.
3. Activity ID/version is resolved from the canonical activity template, not an older semantic profile version.
4. Baseline fallback is not silently selected in V2; missing eligible activity is `UNAVAILABLE_AGE_BAND`.
5. Catalog coverage is measured before adding reviewed content; runtime must not synthesize activities.
6. PixiJS, video, production gates, and feedback persistence are deferred.
