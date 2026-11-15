#!/bin/sh
set -eu

: "${SKETCH2LIFE_FIREBASE_PROJECT_ID:?SKETCH2LIFE_FIREBASE_PROJECT_ID is required}"
mkdir -p /data /root/.cache/firebase/emulators

exec firebase emulators:start \
  --project "$SKETCH2LIFE_FIREBASE_PROJECT_ID" \
  --only auth \
  --import=/data \
  --export-on-exit=/data
