# SOLL Credential Platform Completion Plan

Baseline reviewed: `master` at `66c60486181bd558acd9d619fa83b1c9e2ca1220` (2026-11-26).

## Existing foundations

- Email one-time-code authentication API, secure HTTP-only session cookie, CSRF cookie/header validation, logout, and rate limits.
- User, organisation, organisation-membership, programme, recipient, template, credential, and session data models.
- Organisation membership-scoped read endpoints.
- Role permission map for owner, admin, and issuer.
- Soroban read integration for public credential status and issuer authorisation.
- Public verifier UI and API; the deployed verifier has been manually confirmed against a Testnet credential.
- Soroban credential registry contract and contract tests covering organisation/issuer authorization, credential anchoring, revocation, and tenant isolation.

## Remaining product work

### P0 — Secure usable workspace
- Add frontend sign-in / email-code verification and session-aware route protection.
- Add organisation creation and onboarding, with an explicit on-chain registration/issuer setup workflow.
- Add organisation switching and active-organisation context.
- Replace dashboard demo values and placeholder workspace labels with authenticated API data.
- Add frontend API client with credentialed requests, CSRF handling, and safe error states.

### P1 — Core organisation workflows
- Add tenant-scoped API and UI for programmes.
- Add tenant-scoped API and UI for recipients.
- Add template CRUD and immutable template versions.
- Add credential issuance workflow: recipient + programme + template version, canonical credential payload, commitment generation, secure blinding-value handling, PDF generation/storage, and on-chain anchoring.
- Add credential list/detail/search and shareable public verification URLs.
- Add revocation workflow with permission checks, on-chain transaction confirmation, reason/audit record, and public verifier status refresh.

### P2 — Governance and operations
- Add member invitation/role management and owner-only controls.
- Add append-only audit events for security-sensitive actions.
- Add verification event analytics with privacy-conscious retention and rate limiting.
- Add operational health checks, structured logs, backups/restore procedure, and deployment runbooks.
- Review secrets handling, CORS, trusted proxy configuration, cookie settings, CSRF, rate limits, data retention, and dependency vulnerabilities.

### P3 — Production release gates
- Add integration and end-to-end tests for authentication, tenant isolation, issuance, verification, and revocation.
- Run database migration checks and contract tests.
- Perform an independent security review and recovery drill.
- Keep Testnet as the default until the Mainnet contract, signing/custody model, funding, monitoring, and incident procedures are explicitly approved.

## Safety and implementation constraints

- Do not expose Stellar secret keys, OTPs, session tokens, or recipient PII in logs or public responses.
- Never trust a client-supplied organisation ID without checking active membership and permission on every request.
- Do not treat a local database record as proof of an on-chain transaction; persist transaction identifiers and confirmed ledger state.
- Do not deploy to Mainnet or make irreversible on-chain changes as part of routine CI.
- Do not mark a workflow complete until its tests and deployed behaviour have both been verified.

## Delivery approach

Implement in small, reviewable pull requests on `feat/platform-completion`; preserve the working public verifier and existing Testnet contract. Run the relevant backend, frontend, and contract checks for each slice before merge or production deployment.
