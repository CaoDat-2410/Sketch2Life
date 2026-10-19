# Admin UI to Backend API Integration Specification

- Base URL: `/api/v1/admin`
- Authentication: Bearer JWT in `Authorization` header.
- Error Response Format: RFC 7807 Problem Details.
- PII Protection: Child references are strictly UUIDs, never names or raw images.
