# AWS Architecture Icons attribution and provenance

Provider: Amazon Web Services, Inc. or its affiliates. AWS architecture artwork remains the property of its respective rights holders. This directory does not relicense the artwork as MIT, Apache, or another open-source license.

- Official architecture icon usage and download page: https://aws.amazon.com/architecture/icons/
- AWS Site Terms: https://aws.amazon.com/terms/ (page last updated June 4, 2025; consulted October 23, 2026).
- AWS-owned diagram guidance: https://github.com/aws/aws-networking-best-practices/blob/main/content/community/conventions.md

The official architecture icons page permits customers and partners to use the toolkits and assets to create architecture diagrams and related materials. The AWS Site Terms address ownership and trademarks; do not represent AWS endorsement or create confusion about service/provider identity. The AWS-owned guidance recommends current icons, correct semantic use, and retaining their supplied colors. These summaries identify the provider's published sources and do not replace those terms.

The official `Icon-package_07312026` ZIP was retrieved on October 23, 2026. It contained no separate non-graphic license/readme/terms document. `manifest.json` records the exact package URL, package SHA-256, original member paths, asset SHA-256 values, original SVG titles, and intended diagram mappings. The download ZIP is kept in a temporary cache outside the repository.

The eleven SVG files are byte-for-byte copies of selected official SVG members. Only local filenames are aliased; paths, colors and SVG content were not modified. General resources use the supplied `Res_48_Light` artwork (dark marks for light backgrounds); AI and integration use official category icons. The Light variants replace the initially selected Dark variants after rendered QA found that the Dark artwork uses white marks unsuitable for the diagram's white background. No SVG recoloring was performed. The Artificial Intelligence category member retains its original internal SVG title containing `Machine-Learning_64`.

Scope: FEAT-048, System Architecture v2, task approval revision 18. General and category icons describe actors, components and capabilities. They do not select AWS hosting or services. PostgreSQL, S3-compatible storage and Redis/RQ remain CANDIDATE; WebSocket remains PROPOSED; the AI provider remains TBD. Firebase is Authentication-only. No SQS, RDS, EC2, Bedrock, SageMaker, Cognito, account, region or VPC service decision is implied.
