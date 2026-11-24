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
and acceptance by the proposed new owner.

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
- Random 32-byte credential ID.
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
commitment later.

## 5. Authorisation

Organisation registration:
- The proposed owner authorises registration.

Issuer management:
- Only the organisation owner can add or remove issuers.

Credential issuance:
- The issuer must be active.
- The organisation must be active.
- The issuer must belong to that organisation.

Credential revocation:
- The organisation owner or original issuing account may revoke.
- An arbitrary issuer cannot revoke another issuer's credentials.

Ownership transfer:
- Current owner authorises the transfer.
- New owner authorises acceptance.

Public verification:
- Requires no authentication or wallet connection.

## 6. Tenant Isolation

All organisation-specific storage and write operations must be
scoped to the organisation ID.

A credential operation must verify that its organisation is
active and that the authenticated account has the required
authority for that organisation.

A tenant must not be able to modify another tenant's records.

## 7. Credential Lifecycle

1. Organisation is registered.
2. Organisation authorises one or more issuers.
3. Backend generates and secures the credential.
4. Backend calculates its cryptographic commitment.
5. An authorised issuer anchors the commitment.
6. Public verification retrieves the registry record.
7. The organisation owner or original issuer may revoke it.

Revocation is permanent in the first contract version.

## 8. Contract Operations

Proposed operations:

- initialize
- register_organization
- add_issuer
- remove_issuer
- transfer_ownership
- anchor_credential
- revoke_credential
- verify_credential

Exact signatures and storage types will be finalised against
the selected Soroban SDK version.

## 9. Events

The contract should emit events for:

- Organisation registration
- Issuer addition
- Issuer removal
- Ownership transfer
- Credential anchoring
- Credential revocation

Events must not expose personal information.

## 10. Storage and Security

- Use persistent storage for organisation, issuer and credential
  records where appropriate.
- Manage storage TTL and extension costs.
- Reject duplicate credential IDs within an organisation.
- Prevent issuance under inactive organisations or issuers.
- Prevent reactivation of revoked credentials.
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
