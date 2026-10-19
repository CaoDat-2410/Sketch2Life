# Administrator Security Hardening & Isolation Architecture

- Zero Direct Database Access: Web client strictly talks to REST API gateway.
- Session Expiry: Administrative sessions expire after 15 minutes of inactivity.
- CSP Headers: Strict script-src and object-src none.
