# FEAT-073 evidence

Interactive browser review was performed in an isolated Edge 157 session against the local Parent UI preview on port 5171. Viewports: phone 390×844 and tablet 768×1024.

## Results

- Add Child opens with two unchecked, labeled radio choices and matching boy/girl avatar previews. Save is disabled before gender selection.
- Keyboard sequence from the name field: Tab focuses Nam, Space selects it, and Save becomes enabled when the name is present. The created profile keeps the boy avatar.
- Invalid age 121 disables Save and displays the existing validation message; the valid 120-month upper boundary enables Save.
- Editing the created profile to Nữ changes the detail avatar before save; after save, the girl avatar remains in the settings profile row and P01 child switcher.
- No horizontal overflow was observed at either viewport, and the browser emitted no runtime exceptions during the flow.
- Source review confirms gender stays in in-memory demo profile state and is not included in local storage, an API request, or story/AI context.
- Automated tests/builds were not run under the approved plan.

## Screenshots

- `p13-profile-phone.png` — existing profile list before adding the new profile.
- `add-profile-empty-phone.png` — required gender selection before choosing an option.
- `add-profile-male-selected-phone.png` — keyboard-selected Nam option and matching avatar.
- `profile-created-male-phone.png` — created profile and boy avatar in settings.
- `profile-edit-female-preview-phone.png` — live Nữ preview in profile detail before save.
- `profile-saved-female-phone.png` — saved girl avatar in settings.
- `p01-female-profile-switcher-phone.png` — saved girl avatar in P01 child switcher.
- `add-profile-phone-tablet.png` — Add Child sheet at tablet viewport.
- `add-profile-age-invalid-phone.png` — invalid 121-month value keeps Save disabled.
- `add-profile-age-boundary-enabled-phone.png` — valid 120-month boundary enables Save.
