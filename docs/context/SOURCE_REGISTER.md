# Source register and authority boundary

The files below are reference inputs. Their contents inform context and proposed architecture, but they do not override direct user instructions or grant permission to implement unapproved work.

| ID | Source | Type | Used for | Authority in this repo |
|---|---|---|---|---|
| `handbook-v7` | `external-reference/Sketch2Life_Complete_Technical_Handbook_v7_PreImplementation_Freeze.pdf` | Architecture/product handbook | Product invariants, state machine, codebase proposal, baseline tech stack, validation expectations | Local external reference; not published in the repository; user approval and measured evidence still required |
| `sprint-task-breakdown` | `external-reference/Sketch2Life_Sprint1_4_People_Detailed_Task_Breakdown.xlsx` | Sprint task breakdown | Workstream/task examples, acceptance criteria, fixtures, evidence expectations | Local external reference; not published in the repository; no task is implementation-approved merely because it appears in the sheet |
| `android-distribution-2025-snapshot` | `https://developer.android.com/about/dashboards` | Official Android documentation | Determine whether public Android-version adoption percentages are available | Evidence source only; it redirects platform-version analysis to Android Studio/Play Console |
| `google-play-target-2026` | `https://support.google.com/googleplay/android-developer/answer/11926878` | Official Google Play policy | 2026 target API requirement | Compliance input; re-check before release |
| `react-native-087-release` | `https://reactnative.dev/blog/2026/08/11/react-native-0.87` | Official React Native release note | Node/AGP/Kotlin/compile SDK baseline | Toolchain input for FEAT-009 |
| `lightning-deployment-options` | `https://lightning.ai/docs/security/privacy/deployment-options` | Official Lightning AI security documentation | Private/BYOC/VPN deployment choices | Security input; concrete availability depends on account/plan |
| `lightning-managed-secrets` | `https://lightning.ai/docs/overview/ai-studio/managed-secrets` | Official Lightning AI documentation | Runtime secret storage behavior | Security input; backend/gateway secrets only |
| `android-app-bundle` | `https://developer.android.com/guide/app-bundle` | Official Android documentation | APK versus AAB distribution | Release input; new Play apps publish as AAB |
| `firebase-id-token-verification` | `https://firebase.google.com/docs/auth/admin/verify-id-tokens` | Official Firebase documentation | Custom-backend identity verification | Authentication input; does not authorize Firebase storage/database products |
| `runpod-serverless-endpoints` | `https://docs.runpod.io/serverless/endpoints/overview` | Official Runpod documentation | Production queue endpoint and job semantics | AI infrastructure input for future integration |
| `runpod-api-keys` | `https://docs.runpod.io/get-started/api-keys` | Official Runpod documentation | Endpoint-scoped restricted keys | Security input; backend runtime only |
| `ami-programme-levels` | `https://montessori-ami.org/about-montessori/montessori-programmes` | Official Association Montessori Internationale guidance | Montessori programme bands 0-3, 3-6, and 6-12 | Domain-classification input for FEAT-002; does not replace activity-level pedagogical review |
| `ams-programme-levels` | `https://main-cd-prod.amshq.org/About-AMS/Press-kit/What-Is-Montessori` | Official American Montessori Society guidance | Infant/Toddler, Early Childhood, and Elementary 6-9/9-12 groupings | Secondary age-band cross-check for FEAT-002; AMI bands remain the primary classification baseline |

## Reading notes

- The handbook explicitly describes its stack as an implementation baseline and says exact models/providers must be frozen after evaluation.
- The spreadsheet's `Not Started` tasks are backlog candidates, not authorization to implement.
- Any future conflict is resolved in this order: direct user request, explicit approved decision/ADR, project evidence, then reference baseline.
