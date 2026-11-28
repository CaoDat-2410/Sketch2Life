#!/bin/sh
set -eu

app_env=${SKETCH2LIFE_ENV:-local}
case "$app_env" in
  local|test) ;;
  *)
    printf '%s\n' "Firebase Auth Emulator is available only when SKETCH2LIFE_ENV is local or test." >&2
    exit 2
    ;;
esac

: "${SKETCH2LIFE_FIREBASE_PROJECT_ID:?SKETCH2LIFE_FIREBASE_PROJECT_ID is required}"
mkdir -p /data /root/.cache/firebase/emulators

exec firebase emulators:start \
  --project "$SKETCH2LIFE_FIREBASE_PROJECT_ID" \
  --only auth \
  --import=/data \
  --export-on-exit=/data
