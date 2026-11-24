# FEAT-084 decisions

| ID | Decision | Rationale |
|---|---|---|
| D-084-01 | Keep suggestion cards API-driven; local UI mapping is limited to icons/artwork. | Prevent presentation improvements from changing catalog or AI selection behavior. |
| D-084-02 | Reuse the existing creative palette, UI components, topic images already referenced by the app, and Ionicons. | Preserve the current Parent visual language and avoid introducing new assets. |
| D-084-03 | Keep adult-facing activity instructions and safety details visible. | Copy reduction must not weaken review or safety guidance. |
| D-084-04 | Make no changes to screens where copy is needed to explain consent, errors, confirmation, or state transitions. | The source audit shows these screens carry policy and operational meaning. |
| D-084-05 | This is a source-only UI review; device verification is not claimed. | Emulator/test execution is outside the approved scope for this task. |
| D-084-06 | Screenshot work may sign in only with the existing synthetic Parent account and may view existing records; no account or backend data is created. | The owner asked to run the UI and capture screens; auth and consent gates remain intact. |
| D-084-07 | If the existing seed account is rejected, stop at the public auth screens and report the blocker. | Do not bypass auth or create data solely to obtain screenshots. |
