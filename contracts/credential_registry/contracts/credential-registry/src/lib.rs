#![no_std]

use soroban_sdk::{
    contract, contracterror, contractevent, contractimpl, contracttype, Address, BytesN, Env,
};

const DAY_IN_LEDGERS: u32 = 17_280;
const TTL_THRESHOLD: u32 = 29 * DAY_IN_LEDGERS;
const TTL_BUMP_AMOUNT: u32 = 30 * DAY_IN_LEDGERS;

// Stable error codes returned by the credential registry.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
#[repr(u32)]
pub enum RegistryError {
    OrganizationAlreadyExists = 1,
    OrganizationNotFound = 2,
    OrganizationInactive = 3,
    AlreadyCurrentOwner = 4,
    IssuerAlreadyAuthorized = 5,
    IssuerNotAuthorized = 6,
    IssuerInactive = 7,
    CredentialAlreadyExists = 8,
    CredentialNotFound = 9,
    CredentialAlreadyRevoked = 10,
    UnauthorizedRevocation = 11,
    OrganizationAlreadyInactive = 12,
    OrganizationAlreadyActive = 13,
}
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
pub struct OrganizationDeactivated {
    #[topic]
    pub organization_id: BytesN<32>,
}

#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OrganizationReactivated {
    #[topic]
    pub organization_id: BytesN<32>,
}

#[contractevent]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OwnershipTransferred {
    #[topic]
    pub organization_id: BytesN<32>,
    pub previous_owner: Address,
    pub new_owner: Address,
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
    pub fn register_organization(
        env: Env,
        organization_id: BytesN<32>,
        owner: Address,
    ) -> Result<(), RegistryError> {
        owner.require_auth();

        let key = DataKey::Organization(organization_id.clone());

        if env.storage().persistent().has(&key) {
            return Err(RegistryError::OrganizationAlreadyExists);
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

        Ok(())
    }
    pub fn transfer_ownership(
        env: Env,
        organization_id: BytesN<32>,
        new_owner: Address,
    ) -> Result<(), RegistryError> {
        let organization_key = DataKey::Organization(organization_id.clone());

        let mut organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        extend_persistent_ttl(&env, &organization_key);

        let previous_owner = organization.owner.clone();

        if previous_owner == new_owner {
            return Err(RegistryError::AlreadyCurrentOwner);
        }

        previous_owner.require_auth();
        new_owner.require_auth();

        organization.owner = new_owner.clone();

        env.storage()
            .persistent()
            .set(&organization_key, &organization);

        extend_persistent_ttl(&env, &organization_key);

        OwnershipTransferred {
            organization_id,
            previous_owner,
            new_owner,
        }
        .publish(&env);

        Ok(())
    }
    pub fn deactivate_organization(
        env: Env,
        organization_id: BytesN<32>,
    ) -> Result<(), RegistryError> {
        let organization_key = DataKey::Organization(organization_id.clone());

        let mut organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        organization.owner.require_auth();

        if !organization.active {
            return Err(RegistryError::OrganizationAlreadyInactive);
        }

        organization.active = false;

        env.storage()
            .persistent()
            .set(&organization_key, &organization);

        extend_persistent_ttl(&env, &organization_key);

        OrganizationDeactivated { organization_id }.publish(&env);

        Ok(())
    }

    pub fn reactivate_organization(
        env: Env,
        organization_id: BytesN<32>,
    ) -> Result<(), RegistryError> {
        let organization_key = DataKey::Organization(organization_id.clone());

        let mut organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        organization.owner.require_auth();

        if organization.active {
            return Err(RegistryError::OrganizationAlreadyActive);
        }

        organization.active = true;

        env.storage()
            .persistent()
            .set(&organization_key, &organization);

        extend_persistent_ttl(&env, &organization_key);

        OrganizationReactivated { organization_id }.publish(&env);

        Ok(())
    }

    pub fn get_organization(
        env: Env,
        organization_id: BytesN<32>,
    ) -> Result<Organization, RegistryError> {
        let key = DataKey::Organization(organization_id);

        let organization = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        extend_persistent_ttl(&env, &key);

        Ok(organization)
    }
    pub fn authorize_issuer(
        env: Env,
        organization_id: BytesN<32>,
        issuer: Address,
    ) -> Result<(), RegistryError> {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        extend_persistent_ttl(&env, &organization_key);

        if !organization.active {
            return Err(RegistryError::OrganizationInactive);
        }

        organization.owner.require_auth();

        let issuer_key = DataKey::Issuer(organization_id.clone(), issuer.clone());

        if env.storage().persistent().has(&issuer_key) {
            return Err(RegistryError::IssuerAlreadyAuthorized);
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

        Ok(())
    }
    pub fn remove_issuer(
        env: Env,
        organization_id: BytesN<32>,
        issuer: Address,
    ) -> Result<(), RegistryError> {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        extend_persistent_ttl(&env, &organization_key);

        organization.owner.require_auth();

        let issuer_key = DataKey::Issuer(organization_id.clone(), issuer.clone());

        if !env.storage().persistent().has(&issuer_key) {
            return Err(RegistryError::IssuerNotAuthorized);
        }

        env.storage().persistent().remove(&issuer_key);

        IssuerRemoved {
            organization_id,
            issuer,
        }
        .publish(&env);

        Ok(())
    }
    pub fn is_issuer_authorized(env: Env, organization_id: BytesN<32>, issuer: Address) -> bool {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = match env.storage().persistent().get(&organization_key) {
            Some(record) => record,
            None => return false,
        };

        extend_persistent_ttl(&env, &organization_key);

        if !organization.active {
            return false;
        }

        let issuer_key = DataKey::Issuer(organization_id, issuer);

        match env.storage().persistent().get::<_, Issuer>(&issuer_key) {
            Some(record) => {
                extend_persistent_ttl(&env, &issuer_key);
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
    ) -> Result<(), RegistryError> {
        let organization_key = DataKey::Organization(organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        extend_persistent_ttl(&env, &organization_key);

        if !organization.active {
            return Err(RegistryError::OrganizationInactive);
        }

        let issuer_key = DataKey::Issuer(organization_id.clone(), issuer.clone());

        let issuer_record: Issuer = env
            .storage()
            .persistent()
            .get(&issuer_key)
            .ok_or(RegistryError::IssuerNotAuthorized)?;

        extend_persistent_ttl(&env, &issuer_key);

        if !issuer_record.active {
            return Err(RegistryError::IssuerInactive);
        }

        // The issuing Stellar account must authorize this transaction.
        issuer.require_auth();

        // Credential IDs are globally unique.
        let credential_key = DataKey::Credential(credential_id.clone());

        if env.storage().persistent().has(&credential_key) {
            return Err(RegistryError::CredentialAlreadyExists);
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

        Ok(())
    }

    /// Permanently revokes an anchored credential.
    ///
    /// Only the organisation owner or the original issuer can revoke it.
    /// Removing an issuer does not remove their authority over credentials
    /// they previously issued.
    pub fn revoke_credential(
        env: Env,
        credential_id: BytesN<32>,
        revoked_by: Address,
    ) -> Result<(), RegistryError> {
        let credential_key = DataKey::Credential(credential_id.clone());

        let mut record: CredentialRecord = env
            .storage()
            .persistent()
            .get(&credential_key)
            .ok_or(RegistryError::CredentialNotFound)?;

        extend_persistent_ttl(&env, &credential_key);

        if record.revoked {
            return Err(RegistryError::CredentialAlreadyRevoked);
        }

        let organization_key = DataKey::Organization(record.organization_id.clone());

        let organization: Organization = env
            .storage()
            .persistent()
            .get(&organization_key)
            .ok_or(RegistryError::OrganizationNotFound)?;

        extend_persistent_ttl(&env, &organization_key);

        let is_owner = revoked_by == organization.owner;
        let is_original_issuer = revoked_by == record.issuer;

        if !is_owner && !is_original_issuer {
            return Err(RegistryError::UnauthorizedRevocation);
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

        Ok(())
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
