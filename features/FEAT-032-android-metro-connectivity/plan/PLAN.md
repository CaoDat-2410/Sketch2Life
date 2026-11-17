# Android Metro connectivity fix plan

- Status: REVIEW
- Plan revision: 3
- Implementation status: REVIEW; DEVICE_RETEST_PASS

## Goal

Remove the recurring Android development-client failure caused by launching against an unreachable
`127.0.0.1:8081` URL, while keeping Metro local-only/trusted and preserving release networking.

## Scope

- Add an explicit Expo dev-client LAN script for physical devices.
- Add an explicit one-command native debug script that builds/installs the debug variant and starts
  Metro on the same port.
- Force the dev-client launch URL to a detected private LAN address in LAN mode so a stale
  `127.0.0.1` setting is not reused.
- Add a Windows PowerShell launcher that can either use LAN mode or configure ADB reverse before
  starting Metro in localhost mode.
- Update local development documentation with the exact commands and recovery checks.
- Record reproducible host-side and static verification evidence.

## Steps

1. Add the dev-client launch scripts without changing runtime app code or release configuration.
2. Make the launcher fail clearly when emulator mode is requested but ADB is unavailable.
3. Update the local-development and Android integration guides.
4. Probe Metro status and bundle delivery, then run UI validation and repository security checks.
5. Record limitations: device-level reload remains unverified when no ADB device is attached.

## Acceptance criteria

- [x] `start:dev-client` starts Expo with a host-reachable LAN URL.
- [x] `android:dev` provides the supported fresh-install debug path with Expo/Metro.
- [x] LAN launch resolves a private host address and overrides stale localhost packager settings.
- [x] The PowerShell launcher supports LAN mode without ADB and emulator mode with an explicit
      `adb reverse tcp:8081 tcp:8081` mapping.
- [x] Emulator mode reports an actionable error instead of silently starting an unreachable
      localhost session when ADB is unavailable.
- [x] Documentation distinguishes physical-device LAN mode from emulator ADB reverse mode and
      includes a Metro status probe.
- [x] Existing app source, provider boundaries, release networking, and secrets remain unchanged.
- [x] Host-side Metro/bundle probes and applicable repository checks pass.
- [x] The native debug/release boundary is documented: debug requires Metro; release must embed a
      bundle through the Gradle `export:embed` task.

## Risks and mitigations

- LAN mode can be blocked by Windows Firewall: document trusted-network/firewall checks and keep
  the server bound to Expo's LAN mode rather than exposing credentials or backend services.
- ADB may not be on PATH: resolve the standard Android SDK path and fail with the exact missing
  prerequisite if no executable is found.
- A stale dev server may occupy the port: Expo's own port handling remains authoritative; the
  launcher does not kill unrelated processes.

## Verification plan

- `pnpm --dir apps/ui-mobile exec expo start --dev-client --lan --port 8081` is started or its
  equivalent launcher is exercised.
- `GET http://127.0.0.1:8081/status` returns Metro running status.
- The Android virtual entry bundle returns HTTP 200 from the host.
- `pnpm --dir apps/ui-mobile test` passes.
- `python tools/validate_repository_security.py` passes or reports only pre-existing findings.
- Device screenshot/reload is claimed only if a connected Android device is available.

## Evidence plan

Store the command output and interpretation in
`features/FEAT-032-android-metro-connectivity/evidence/`, including the current environment
limitation that no ADB executable/device is available in this workspace.

Implementation is blocked until `approvals/TASK_APPROVAL.md` says `APPROVED` for this plan revision.
