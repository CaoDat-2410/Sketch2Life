# FEAT-011 decisions

- Parent/guide authenticates; child mode has no independent child login/account.
- Initial Firebase methods are Google Sign-In and email/password.
- Project owner controls Firebase, Google Play, and Android release/upload key custody.
- `.env`, seed accounts/credentials, service accounts, provider keys, and signing keys never enter Git.
- Attached handbook/spreadsheet originals and extracted page screenshots are local reference evidence, not GitHub publication content.
- Publish to the exact owner repository on `main`; fetch first and never force-push.
