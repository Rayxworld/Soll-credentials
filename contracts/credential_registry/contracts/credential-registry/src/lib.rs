#![no_std]

use soroban_sdk::{contract, contractevent, contractimpl, contracttype, Address, BytesN, Env};

const DAY_IN_LEDGERS: u32 = 17_280;
const TTL_THRESHOLD: u32 = 29 * DAY_IN_LEDGERS;
const TTL_BUMP_AMOUNT: u32 = 30 * DAY_IN_LEDGERS;

/// Renews a persistent entry when its remaining TTL falls below the threshold.
fn extend_persistent_ttl(env: &Env, key: &DataKey) {
    env.storage()
        .persistent()
        .extend_ttl(key, TTL_THRESHOLD, TTL_BUMP_AMOUNT);
}

#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OrganizationRegistered {
    #[topic]
    pub organization_id: BytesN<32>,
    pub owner: Address,
}

#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IssuerAuthorized {
    #[topic]
    pub organization_id: BytesN<32>,
    #[topic]
    pub issuer: Address,
}

#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IssuerRemoved {
    #[topic]
    pub organization_id: BytesN<32>,
    #[topic]
    pub issuer: Address,
}

#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CredentialAnchored {
    #[topic]
    pub organization_id: BytesN<32>,
    #[topic]
    pub credential_id: BytesN<32>,
    pub issuer: Address,
    pub commitment: BytesN<32>,
}
#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CredentialRevoked {
    #[topic]
    pub organization_id: BytesN<32>,
    #[topic]
    pub credential_id: BytesN<32>,
    pub revoked_by: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Organization {
    pub owner: Address,
    pub active: bool,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Issuer {
    pub active: bool,
}

/// Public metadata for an anchored credential.
/// No recipient personal information is stored here.
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CredentialRecord {
    pub organization_id: BytesN<32>,
    pub commitment: BytesN<32>,
    pub issuer: Address,
    pub issued_at: u64,
    pub revoked: bool,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum DataKey {
    Organization(BytesN<32>),
    Issuer(BytesN<32>, Address),

    // Credential IDs are globally unique across all organisations.
    Credential(BytesN<32>),
}

#[contract]
pub struct CredentialRegistry;

#[contractimpl]
impl CredentialRegistry {
    pub fn register_organization(env: Env, organization_id: BytesN<32>, owner: Address) {
        owner.require_auth();

        let key = DataKey::Organization(organization_id.clone());

        if env.storage().persistent().has(&key) {
            panic!("organization already exists");
        }

        let organization = Organization {
            owner: owner.clone(),
            active: true,
        };

        env.storage().persistent().set(&key, &organization);
        extend_persistent_ttl(&env, &key);

        OrganizationRegistered {
            organization_id,
            owner,
        }
        .publish(&env);
    }

    pub fn get_organization(env: Env, organization_id: BytesN<32>) -> Organization {
        let key = DataKey::Organization(organization_id);

        match env.storage().persistent().get(&key) {
            Some(organization) => {
                extend_persistent_ttl(&env, &key);
                organization
            }
            None => panic!("organization not found"),
        }
    }

    /// Authorises an issuer for one organisation.
    /// Only the organisation's current owner can do this.
    pub fn authorize_issuer(env: Env, organization_id: BytesN<32>, issuer: Address) {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .unwrap_or_else(|| panic!("organization not found"));

        extend_persistent_ttl(&env, &organization_key);

        if !organization.active {
            panic!("organization is inactive");
        }

        organization.owner.require_auth();

        let issuer_key = DataKey::Issuer(organization_id.clone(), issuer.clone());

        if env.storage().persistent().has(&issuer_key) {
            panic!("issuer already authorized");
        }

        env.storage()
            .persistent()
            .set(&issuer_key, &Issuer { active: true });

        extend_persistent_ttl(&env, &issuer_key);

        IssuerAuthorized {
            organization_id,
            issuer,
        }
        .publish(&env);
    }

    /// Removes an issuer's authority within one organisation.
    pub fn remove_issuer(env: Env, organization_id: BytesN<32>, issuer: Address) {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .unwrap_or_else(|| panic!("organization not found"));

        extend_persistent_ttl(&env, &organization_key);

        organization.owner.require_auth();

        let issuer_key = DataKey::Issuer(organization_id.clone(), issuer.clone());

        if !env.storage().persistent().has(&issuer_key) {
            panic!("issuer not authorized");
        }

        env.storage().persistent().remove(&issuer_key);

        IssuerRemoved {
            organization_id,
            issuer,
        }
        .publish(&env);
    }

    /// Publicly checks whether an address is an active issuer.
    pub fn is_issuer_authorized(env: Env, organization_id: BytesN<32>, issuer: Address) -> bool {
        let key = DataKey::Issuer(organization_id, issuer);

        match env.storage().persistent().get::<_, Issuer>(&key) {
            Some(record) => {
                extend_persistent_ttl(&env, &key);
                record.active
            }
            None => false,
        }
    }

    /// Anchors a credential commitment on the Stellar network.
    ///
    /// The issuer must be authorised by the organisation and
    /// must authenticate this transaction.
    pub fn anchor_credential(
        env: Env,
        organization_id: BytesN<32>,
        credential_id: BytesN<32>,
        commitment: BytesN<32>,
        issuer: Address,
    ) {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .unwrap_or_else(|| panic!("organization not found"));

        extend_persistent_ttl(&env, &organization_key);

        if !organization.active {
            panic!("organization is inactive");
        }

        let issuer_key = DataKey::Issuer(organization_id.clone(), issuer.clone());

        let issuer_record: Issuer = env
            .storage()
            .persistent()
            .get(&issuer_key)
            .unwrap_or_else(|| panic!("issuer not authorized"));

        extend_persistent_ttl(&env, &issuer_key);

        if !issuer_record.active {
            panic!("issuer is inactive");
        }

        // The issuing Stellar account must authorize this transaction.
        issuer.require_auth();

        // Credential IDs are globally unique.
        let credential_key = DataKey::Credential(credential_id.clone());

        if env.storage().persistent().has(&credential_key) {
            panic!("credential already exists");
        }

        let record = CredentialRecord {
            organization_id: organization_id.clone(),
            commitment: commitment.clone(),
            issuer: issuer.clone(),
            issued_at: env.ledger().timestamp(),
            revoked: false,
        };

        env.storage().persistent().set(&credential_key, &record);
        extend_persistent_ttl(&env, &credential_key);

        CredentialAnchored {
            organization_id,
            credential_id,
            issuer,
            commitment,
        }
        .publish(&env);
    }

    /// Permanently revokes an anchored credential.
    ///
    /// Only the organisation owner or the original issuer can revoke it.
    /// Removing an issuer does not remove their authority over credentials
    /// they previously issued.
    pub fn revoke_credential(env: Env, credential_id: BytesN<32>, revoked_by: Address) {
        let credential_key = DataKey::Credential(credential_id.clone());

        let mut record: CredentialRecord = env
            .storage()
            .persistent()
            .get(&credential_key)
            .unwrap_or_else(|| panic!("credential not found"));

        extend_persistent_ttl(&env, &credential_key);

        if record.revoked {
            panic!("credential already revoked");
        }

        let organization_key = DataKey::Organization(record.organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .unwrap_or_else(|| panic!("organization not found"));

        extend_persistent_ttl(&env, &organization_key);

        let is_owner = revoked_by == organization.owner;
        let is_original_issuer = revoked_by == record.issuer;

        if !is_owner && !is_original_issuer {
            panic!("unauthorized revocation");
        }

        revoked_by.require_auth();

        record.revoked = true;

        env.storage().persistent().set(&credential_key, &record);
        extend_persistent_ttl(&env, &credential_key);

        CredentialRevoked {
            organization_id: record.organization_id,
            credential_id,
            revoked_by,
        }
        .publish(&env);
    }
    /// Retrieves an anchored credential record.
    ///
    /// Anyone can query this function.
    /// Returns None when the credential does not exist.
    pub fn get_credential(env: Env, credential_id: BytesN<32>) -> Option<CredentialRecord> {
        let key = DataKey::Credential(credential_id);

        match env.storage().persistent().get(&key) {
            Some(record) => {
                extend_persistent_ttl(&env, &key);
                Some(record)
            }
            None => None,
        }
    }
}

mod test;
