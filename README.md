# SOLL Credential

SOLL Credential is a multi-tenant digital credential management and verification platform.

It is being developed to help organisations create, issue, manage, and verify digital certificates and credentials.

## Project status

**Development — application foundation**

The current repository contains the backend foundation, database models and migrations, authentication infrastructure, and an initial Next.js dashboard.

Not all product workflows are implemented yet. This repository should not be considered production-ready.

## Architecture

| Component | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Authentication | Email OTP, secure sessions, CSRF protection |
| Smart contracts | Rust, Soroban |
| Blockchain network | Stellar |
| Planned object storage | Cloudflare R2 |
| Planned database connectivity | Cloudflare Hyperdrive |

## Current capabilities

- Email one-time-password authentication
- Session creation, validation, and revocation
- CSRF protection
- IP-based authentication rate limiting
- Organisation and membership data models
- Owner, admin, and issuer roles
- Organisation ownership transfer workflow
- Programme and recipient data models
- Certificate template and version models
- Credential data model with commitment and revocation fields
- Database migrations
- Automated backend tests

## Planned capabilities

- Organisation onboarding and workspace management
- Member invitations and administration
- Programme management
- Recipient registration and bulk import
- Certificate template designer
- Certificate generation and PDF downloads
- Email delivery of issued credentials
- QR-based public verification
- Credential revocation and reissuance
- Blockchain commitment anchoring
- Audit logs and organisation analytics

## Repository structure

```text
soll-credential/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   ├── db/
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── alembic.ini
│   │   └── requirements.txt
│   └── web/
│       ├── src/
│       │   ├── app/
│       │   └── components/
│       ├── package.json
│       └── package-lock.json
├── contracts/
├── docs/
└── .gitignore
```

## Local development

### Backend

Requirements:
- Python 3.12+
- PostgreSQL

From the backend directory:

```powershell
cd apps/api

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

Configure the required environment variables in a local `.env` file. Never commit secrets or production credentials.

Apply database migrations:

```powershell
alembic upgrade head
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

### Frontend

Requirements:
- Node.js
- npm

From the frontend directory:

```powershell
cd apps/web

npm ci
npm run dev
```

The frontend development server will display its local address in the terminal.

## Backend tests

From `apps/api` with the Python environment activated:

```powershell
python -m pytest -q
```

## Security principles

- Organisation data must be isolated by tenant.
- API permissions must be enforced server-side.
- Session tokens must not be exposed to browser JavaScript.
- Secrets and credentials must never be committed.
- Personal recipient information must remain off-chain.
- Blockchain commitments must not expose private credential data.
- Public verification must validate credential status through trusted application logic.

## Deployment direction

The intended free-first deployment architecture is:

- Cloudflare Workers for the application runtime
- Cloudflare Workers with Python support for FastAPI, subject to compatibility testing
- Cloudflare Hyperdrive for PostgreSQL connectivity
- Neon or another compatible hosted PostgreSQL provider
- Cloudflare R2 for certificate files and object storage
- Stellar for blockchain anchoring

Deployment configuration and runtime compatibility are still to be validated.

## License

No open-source license has been assigned yet. All rights are reserved unless a license is explicitly added to this repository.
