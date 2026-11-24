# SOLL Credential - Credential Registry Architecture

## 1. Purpose

The Credential Registry is the Soroban smart contract responsible
for organisation ownership, issuer authorisation, credential
integrity commitments, issuance records and revocation status.

It is one component of a multi-tenant credential infrastructure.
It is not the complete credential application.

## 2. Organisation Ownership

SOLL Credential uses a hybrid ownership model.

Supported modes:

- Managed: SOLL Credential provisions and securely manages a
  separate Stellar signing account for the organisation.
- External: The organisation connects and controls its own
  Stellar account.

Every organisation has an independent on-chain owner address.

The platform must not use one shared owner account for all tenants.

Ownership transfer requires authorisation from the current owner
and acceptance by the proposed new owner in the same transaction.

The account custody mode is application-level metadata. The
contract enforces owner-address authorisation regardless of mode.

## 3. On-chain Data

Organisation:
- Random 32-byte organisation ID.
- Owner Stellar address.
- Active status.

Issuer:
- Organisation ID.
- Issuer Stellar address.
- Active status.

Credential:
- Organisation ID.
- Random 32-byte credential ID, globally unique across the registry.
- 32-byte cryptographic commitment.
- Original issuing address.
- Issuance ledger timestamp.
- Revocation status.

No recipient names, email addresses, course titles, credential
documents, private keys or other personal data may be stored
on-chain.

## 4. Credential Commitment

The backend constructs a canonical representation of the
cryptographically secured credential.

It generates a cryptographically random 32-byte blinding value
and computes a domain-separated cryptographic commitment.

The blinding value and credential contents remain off-chain.

The contract receives only the resulting 32-byte commitment.

The backend must retain the information required to verify the
commitment later. The blockchain record alone does not establish
the validity of the credential's W3C proof or disclose its contents.

## 5. Authorisation

Organisation registration:
- The proposed owner authorises registration.
- An organisation ID cannot be registered more than once.

Issuer management:
- Only the organisation owner can authorise or remove issuers.
- Issuer authorisation is scoped to its organisation.
- An inactive organisation cannot authorise issuers.

Credential issuance:
- The organisation must exist and be active.
- The issuer must be authorised and active.
- The issuer must authorise the anchoring transaction.
- Credential IDs must be globally unique.

Credential revocation:
- The organisation owner or original issuing account may revoke.
- An unrelated address cannot revoke a credential.
- Removing an issuer does not remove its authority to revoke
  credentials it previously issued.
- A revoked credential cannot be revoked again.

Ownership transfer:
- Current owner authorises the transfer.
- New owner authorises acceptance.

Public reads:
- Registry read operations require no wallet connection.
- Issuer authorisation queries return false if the organisation
  is missing or inactive, even if an issuer record still exists.

## 6. Tenant Isolation

All organisation-specific storage and write operations must be
scoped to the organisation ID.

A credential operation must verify that its organisation is
active and that the authenticated account has the required
authority for that organisation.

Credential IDs are globally unique across organisations.

A tenant must not be able to modify another tenant's records.

## 7. Credential Lifecycle

1. Organisation is registered by its proposed owner.
2. Organisation authorises one or more issuers.
3. Backend generates and secures the credential.
4. Backend calculates its cryptographic commitment.
5. An authorised issuer anchors the commitment.
6. Public verification retrieves the registry record.
7. The organisation owner or original issuer may revoke it.

Organisation lifecycle:
- The owner may deactivate an active organisation.
- The owner may reactivate an inactive organisation.
- Deactivation prevents new issuer authorisations and credential
  anchoring.
- Existing credentials remain in the registry and may still be
  revoked by the organisation owner or original issuer.
- Existing issuer records are retained during deactivation.
  Reactivation restores their operational authorisation.

Revocation is permanent in the first contract version.

## 8. Implemented Contract Operations

Write operations:

- register_organization
- transfer_ownership
- deactivate_organization
- reactivate_organization
- authorize_issuer
- remove_issuer
- anchor_credential
- revoke_credential

Read operations:

- get_organization
- is_issuer_authorized
- get_credential

Business-rule failures return typed RegistryError values where
defined. Authentication failures are enforced through Soroban
address authorisation.

There is no global organisation initialization operation.
Each organisation registers independently under its own owner.

## 9. Events

The contract emits events for:

- Organisation registration
- Ownership transfer
- Organisation deactivation
- Organisation reactivation
- Issuer authorisation
- Issuer removal
- Credential anchoring
- Credential revocation

Events must not expose personal information.

## 10. Storage and Security

- Use persistent storage for organisation, issuer and credential
  records.
- Extend persistent-entry TTL when remaining TTL falls below
  the configured threshold.
- Current policy: 29-day renewal threshold and 30-day extension
  target, using 17,280 ledgers per day.
- Persistent entries may expire and require restoration if they
  are not renewed. Production availability requirements may
  therefore require an off-chain keeper strategy.
- Reject duplicate organisation IDs.
- Reject globally duplicate credential IDs.
- Prevent issuance under inactive organisations or issuers.
- Revocation is terminal; the contract has no credential reactivation operation.
- Keep contract upgrade authority separate from tenant ownership.
- Test authorisation failures and cross-tenant access attempts.
- Keep all personal data off-chain.

## 11. Application Responsibilities

The FastAPI backend handles:
- Tenant authentication and authorisation.
- W3C Verifiable Credential creation.
- Credential signing and proof verification.
- Cryptographic commitment generation.
- PDF generation.
- QR code generation.
- Email delivery.
- Secure transaction submission.
- Managed-account key custody.
- Audit logging.

The Next.js frontend handles organisation dashboards,
participant management, credential presentation and verification.

## 12. Technology

- Smart contracts: Rust and Soroban SDK 29
- Blockchain: Stellar Testnet initially
- Backend: FastAPI and Python
- Frontend: Next.js and TypeScript
- Database: PostgreSQL
- Credential standard: W3C Verifiable Credentials 2.0
- PDF: HTML templates and Playwright

## 13. Deployment Policy

The initial deployment is on Stellar Testnet.

Production deployment requires security review, storage-cost
analysis, key-management review and an upgrade-governance plan.
