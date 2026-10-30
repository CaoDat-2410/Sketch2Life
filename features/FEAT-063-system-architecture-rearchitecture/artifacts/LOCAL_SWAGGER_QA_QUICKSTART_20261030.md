# Local Swagger QA quickstart — 2026-10-30

## What can be tested now

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The local session and image-upload example uses process-local memory and the synthetic PNG at `features/FEAT-063-system-architecture-rearchitecture/artifacts/qa-fixtures/synthetic-demo.png`. It does not write to the persistent application database or call an AI provider.

The demo accepts only the `demo:local` actor marker and an explicit synthetic/non-child confirmation. This sample is an abstract sun-and-hills graphic; it contains no person, child, or personal data.

## Run the create-session and image-upload flow

1. In Swagger, open `POST /v1/sessions`, choose **Try it out**, and use the `localSyntheticSession` example. For a later run, replace `session_id` with a fresh UUIDv4 and change `request_id` and `idempotency_key` to new values.
2. Execute the request. Expect HTTP `201`, `status: "SUCCEEDED"`, and `observed_session_version: 0`.
3. Open `POST /v1/sessions/{session_id}/media/image`, choose **Try it out**, set `session_id` to the ID from step 1 and `X-Expected-Session-Version` to the version from step 2.
4. Keep `X-Actor-Ref` as `demo:local`, set `X-Synthetic-Non-Child-Confirmed` to `true`, and use fresh values for `X-Request-ID` and `Idempotency-Key`.
5. Select `synthetic-demo.png` from `features/FEAT-063-system-architecture-rearchitecture/artifacts/qa-fixtures/`. Keep `source_media_type` as `image/png` and `normalization_policy` as `IDENTITY_V1`, then execute.
6. Expect HTTP `200`, `status: "SUCCEEDED"`, `payload.decision: "ADMITTED"`, and a new `observed_session_version` of `1`.

Each upload increments the session version. Use the latest returned version for the next write. Create a new session after restarting the API; all demo sessions and uploaded bytes are held in process memory and are cleared when the process exits.

## Protected Lesson Library and BE1 APIs

Swagger's Bearer field requires a valid Firebase ID token for the configured Firebase project. The local integration fixture creates synthetic principals in a disposable `be1_acceptance` database and overrides identity verification only inside tests; its `X-Test-Principal` header is not accepted as a production/API token. This quickstart does not create Firebase users or credentials and does not add a token bypass. Interactive requests to protected routes need a separately configured Firebase Auth Emulator or valid local Firebase test account/token.

For the verified local setup on 2026-10-30, `FIREBASE_AUTH_EMULATOR_HOST` and `BE1_TEST_DATABASE_URL` are unset; no Firebase CLI/Auth Emulator listener on port `9099` or PostgreSQL listener on port `5432` is available. Protected-role workflows therefore are not ready for interactive `Try it out` here. Only the synthetic Demo session/image flow above was exercised.

Role tags in Swagger are navigation aids. Route authorization remains enforced by the API.
