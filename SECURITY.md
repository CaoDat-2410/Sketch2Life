# Security policy

## Never commit

- `.env` files or non-placeholder environment values;
- Firebase service accounts or `google-services.json`;
- Android release/debug keystores and signing passwords;
- Lightning, Runpod, AWS, S3, database, or GitHub credentials;
- seed accounts/users/passwords;
- real child media, identifiers, prompts, transcripts, or model outputs;
- external handbook/workbook originals or rendered page extracts.

Use ignored local files for development and an approved runtime secret manager for deployed environments. Test identities must be ephemeral emulator/factory data, not reusable seeded credentials.

## Required check

```powershell
python tools/validate_repository_security.py
```

If a secret is committed, revoke/rotate it first, then remove it from Git history before any further release. Do not merely delete it in a later commit.

## Reporting

Report suspected exposure privately to the project owner. Do not open a public issue containing credentials, child data, exploit details, or vulnerable endpoint information.
