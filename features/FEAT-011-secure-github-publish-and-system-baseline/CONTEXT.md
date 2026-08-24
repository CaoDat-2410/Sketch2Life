# FEAT-011 secure GitHub publish and system baseline

- Status: APPROVED
- Owner: project owner
- Goal: finalize remaining identity ownership decisions, create one detailed current-system document, and securely publish the foundation to the owner's GitHub repository.
- Scope: context/ADR updates, system baseline document, repository security audit, ignore/secret/signing-key hardening, validation, initial commit, remote configuration, and push to `https://github.com/CaoDat-2410/Sketch2Life.git`.
- Non-goals: uploading `.env`, seed accounts, signing keys, cloud credentials, attached source documents, real child data, node/venv caches, provider provisioning, or product implementation.
- Dependencies: FEAT-010, local Git repository on branch `main`, GitHub access/credentials, and all project validators.
- Risks: accidental secret/private-source disclosure, pushing generated caches, overwriting a non-empty remote, or documenting proposed behavior as implemented behavior.

## Context snapshot

The owner confirmed that children do not have separate accounts; parent/guide users authenticate and open child mode. Initial Firebase methods are Google Sign-In plus email/password. The owner personally controls the Firebase/Google Play accounts and Android release key. The owner explicitly required that environment files and seed accounts never be uploaded and authorized publication to the named GitHub repository.
