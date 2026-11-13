# FEAT-067 publication record

- Target: `origin/FE_UI_Project_Ver2`.
- Authorization: Plan Rev2 and the direct owner instruction recorded in the feature approval register.
- Pre-publication check: `python tools/validate_repository_security.py` returned `REPOSITORY_SECURITY_VALID`; no credentials, signing keys, or absolute workstation paths were found.
- Diff check: `git diff --cached --check` passed.
- Included scope: Parent Android WebView packaging, Windows Gradle wrapper fix, Parent run instructions, the related FEAT-066 accessibility role fix and evidence, FEAT-067 plan/approval/status/evidence, and the root approval register.
- Excluded generated outputs: Gradle/CMake caches, Vite `dist`, and APK build output.
- Publication status: pending normal commit and push; no history rewrite is authorized.
