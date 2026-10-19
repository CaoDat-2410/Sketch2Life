# COPPA 72-Hour Data Erasure Protocol

1. Parent submits data erasure request via mobile app or web portal.
2. System places request in `DataRequestsPage` queue with SLA timer (72 hours).
3. Admin verifies legitimacy and clicks confirm.
4. Data purge executes: child profile, artifacts, and biometric traces permanently deleted.
5. Audit log retains cryptographic hash only, zero PII.
