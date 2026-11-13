# FEAT-069 product and API questions

These leader-review requests are not implemented as production behavior because they conflict with, or are not defined by, the current FEAT-063 SRS v2.5-draft and mounted contracts. Keep them open until the product owner resolves them.

1. **Outdoor activity before video.** Leader feedback requested the outdoor activity before video. SRS §5.1, FR-P-05 and FR-PL-16 place Parent activities after a playable video. Current UI retains the SRS order.
2. **Removing context confirmation.** The review suggested removing the context/age opt-in screen. FR-P-06 still requires adult review and confirmation of the minimal context before story generation. The UI now presents a compact confirmation dialog; the confirmation itself remains.
3. **Child gender field.** No persisted gender field exists in the current SRS/API profile model. It has not been added to Parent profile UI or data.
4. **Lesson mismatch modal.** The requested choice modal when the analyzed drawing differs from lesson direction has no mounted analysis result/contract defining mismatch state or next action. The existing supported subject correction and post-capture direction choice remain.
5. **Teacher dashboard from API.** Current teacher dashboard uses fixtures. The web auth bridge `window.sketch2lifeAuth` and `GET /api/auth/v1/me` are absent; the user/organization context required by API calls cannot be derived safely. Do not hard-code a tenant or call shared writes with fixture identity.
6. **Live AI/occurrence capabilities.** ASR, generated Teacher Show Slide, complete occurrence/session persistence and the complete Parent story/video chain are not connected through the current UI route composition. Static guide/deck states remain labeled and no success is fabricated.

These questions affect product scope or API integration, not visual polish alone. The owner should resolve them against the canonical SRS and versioned contracts before those behaviors are represented as production-ready UI.
