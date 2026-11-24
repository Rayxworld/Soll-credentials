#![cfg(test)]

use super::*;

use soroban_sdk::{
    testutils::{storage::Persistent as _, Address as _, Ledger as _},
    Address, BytesN, Env,
};

fn setup() -> (Env, Address, CredentialRegistryClient<'static>) {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register(CredentialRegistry, ());
    let client = CredentialRegistryClient::new(&env, &contract_id);

    (env, contract_id, client)
}

#[test]
fn test_register_organization() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[1u8; 32]);
    let owner = Address::generate(&env);

    client.register_organization(&organization_id, &owner);

    let organization = client.get_organization(&organization_id);

    assert_eq!(organization.owner, owner);
    assert!(organization.active);
}

#[test]
fn test_organizations_are_isolated() {
    let (env, _, client) = setup();

    let organization_a = BytesN::from_array(&env, &[1u8; 32]);
    let organization_b = BytesN::from_array(&env, &[2u8; 32]);

    let owner_a = Address::generate(&env);
    let owner_b = Address::generate(&env);

    client.register_organization(&organization_a, &owner_a);
    client.register_organization(&organization_b, &owner_b);

    assert_eq!(client.get_organization(&organization_a).owner, owner_a);
    assert_eq!(client.get_organization(&organization_b).owner, owner_b);
}

#[test]
fn test_authorize_issuer() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[10u8; 32]);
    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);

    assert!(client.is_issuer_authorized(&organization_id, &issuer));
}

#[test]
fn test_issuer_authorization_is_scoped_to_organization() {
    let (env, _, client) = setup();

    let organization_a = BytesN::from_array(&env, &[11u8; 32]);
    let organization_b = BytesN::from_array(&env, &[12u8; 32]);

    let owner_a = Address::generate(&env);
    let owner_b = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_a, &owner_a);
    client.register_organization(&organization_b, &owner_b);
    client.authorize_issuer(&organization_a, &issuer);

    assert!(client.is_issuer_authorized(&organization_a, &issuer));
    assert!(!client.is_issuer_authorized(&organization_b, &issuer));
}

#[test]
fn test_remove_issuer() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[13u8; 32]);
    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.remove_issuer(&organization_id, &issuer);

    assert!(!client.is_issuer_authorized(&organization_id, &issuer));
}

#[test]
#[should_panic]
fn test_duplicate_issuer_authorization_rejected() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[14u8; 32]);
    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.authorize_issuer(&organization_id, &issuer);
}

#[test]
#[should_panic]
fn test_non_owner_cannot_authorize_issuer() {
    let env = Env::default();
    let contract_id = env.register(CredentialRegistry, ());
    let client = CredentialRegistryClient::new(&env, &contract_id);

    let organization_id = BytesN::from_array(&env, &[15u8; 32]);
    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    env.as_contract(&contract_id, || {
        env.storage().persistent().set(
            &DataKey::Organization(organization_id.clone()),
            &Organization {
                owner,
                active: true,
            },
        );
    });

    client.authorize_issuer(&organization_id, &issuer);
}

#[test]
fn test_anchor_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[20u8; 32]);
    let credential_id = BytesN::from_array(&env, &[21u8; 32]);
    let commitment = BytesN::from_array(&env, &[22u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);

    let expected_timestamp = env.ledger().timestamp();

    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    let record = client
        .get_credential(&credential_id)
        .expect("credential should exist");

    assert_eq!(record.organization_id, organization_id);
    assert_eq!(record.commitment, commitment);
    assert_eq!(record.issuer, issuer);
    assert_eq!(record.issued_at, expected_timestamp);
    assert!(!record.revoked);
}

#[test]
#[should_panic]
fn test_unauthorized_issuer_cannot_anchor_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[23u8; 32]);
    let credential_id = BytesN::from_array(&env, &[24u8; 32]);
    let commitment = BytesN::from_array(&env, &[25u8; 32]);

    let owner = Address::generate(&env);
    let unauthorized_issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);

    client.anchor_credential(
        &organization_id,
        &credential_id,
        &commitment,
        &unauthorized_issuer,
    );
}

#[test]
#[should_panic]
fn test_removed_issuer_cannot_anchor_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[26u8; 32]);
    let credential_id = BytesN::from_array(&env, &[27u8; 32]);
    let commitment = BytesN::from_array(&env, &[28u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.remove_issuer(&organization_id, &issuer);

    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);
}

#[test]
#[should_panic]
fn test_credential_id_is_globally_unique() {
    let (env, _, client) = setup();

    let organization_a = BytesN::from_array(&env, &[30u8; 32]);
    let organization_b = BytesN::from_array(&env, &[31u8; 32]);
    let credential_id = BytesN::from_array(&env, &[32u8; 32]);
    let commitment_a = BytesN::from_array(&env, &[33u8; 32]);
    let commitment_b = BytesN::from_array(&env, &[34u8; 32]);

    let owner_a = Address::generate(&env);
    let owner_b = Address::generate(&env);
    let issuer_a = Address::generate(&env);
    let issuer_b = Address::generate(&env);

    client.register_organization(&organization_a, &owner_a);
    client.register_organization(&organization_b, &owner_b);

    client.authorize_issuer(&organization_a, &issuer_a);
    client.authorize_issuer(&organization_b, &issuer_b);

    client.anchor_credential(&organization_a, &credential_id, &commitment_a, &issuer_a);

    // The same ID must be rejected, even under a different organisation.
    client.anchor_credential(&organization_b, &credential_id, &commitment_b, &issuer_b);
}

#[test]
#[should_panic]
fn test_duplicate_organization_rejected() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[3u8; 32]);
    let owner = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.register_organization(&organization_id, &owner);
}

#[test]
#[should_panic]
fn test_registration_requires_owner_authorization() {
    let env = Env::default();
    let contract_id = env.register(CredentialRegistry, ());
    let client = CredentialRegistryClient::new(&env, &contract_id);

    let organization_id = BytesN::from_array(&env, &[4u8; 32]);
    let owner = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
}

#[test]
fn test_organization_owner_can_revoke_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[40u8; 32]);
    let credential_id = BytesN::from_array(&env, &[41u8; 32]);
    let commitment = BytesN::from_array(&env, &[42u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    client.revoke_credential(&credential_id, &owner);

    let record = client.get_credential(&credential_id).unwrap();
    assert!(record.revoked);
    assert_eq!(record.issuer, issuer);
    assert_eq!(record.commitment, commitment);
}

#[test]
fn test_original_issuer_can_revoke_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[43u8; 32]);
    let credential_id = BytesN::from_array(&env, &[44u8; 32]);
    let commitment = BytesN::from_array(&env, &[45u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    client.revoke_credential(&credential_id, &issuer);

    let record = client.get_credential(&credential_id).unwrap();
    assert!(record.revoked);
}

#[test]
#[should_panic]
fn test_unrelated_address_cannot_revoke_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[46u8; 32]);
    let credential_id = BytesN::from_array(&env, &[47u8; 32]);
    let commitment = BytesN::from_array(&env, &[48u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);
    let unrelated = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    client.revoke_credential(&credential_id, &unrelated);
}

#[test]
#[should_panic]
fn test_already_revoked_credential_cannot_be_revoked_again() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[49u8; 32]);
    let credential_id = BytesN::from_array(&env, &[50u8; 32]);
    let commitment = BytesN::from_array(&env, &[51u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    client.revoke_credential(&credential_id, &owner);
    client.revoke_credential(&credential_id, &owner);
}

#[test]
#[should_panic]
fn test_nonexistent_credential_cannot_be_revoked() {
    let (env, _, client) = setup();

    let credential_id = BytesN::from_array(&env, &[52u8; 32]);
    let owner = Address::generate(&env);

    client.revoke_credential(&credential_id, &owner);
}

#[test]
fn test_removed_issuer_can_revoke_previously_issued_credential() {
    let (env, _, client) = setup();

    let organization_id = BytesN::from_array(&env, &[53u8; 32]);
    let credential_id = BytesN::from_array(&env, &[54u8; 32]);
    let commitment = BytesN::from_array(&env, &[55u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);
    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    client.remove_issuer(&organization_id, &issuer);

    assert!(!client.is_issuer_authorized(&organization_id, &issuer));

    client.revoke_credential(&credential_id, &issuer);

    let record = client.get_credential(&credential_id).unwrap();
    assert!(record.revoked);
}

// Verifies that an organisation's persistent storage entry is renewed on access.
#[test]
fn test_organization_ttl_is_extended_on_access() {
    let env = Env::default();

    // Use a manageable minimum TTL while allowing the 30-day target.
    env.ledger().set_min_persistent_entry_ttl(100);
    env.ledger().set_max_entry_ttl(TTL_BUMP_AMOUNT + 1_000);

    env.mock_all_auths();

    let contract_id = env.register(CredentialRegistry, ());
    let client = CredentialRegistryClient::new(&env, &contract_id);

    let organization_id = BytesN::from_array(&env, &[90u8; 32]);
    let owner = Address::generate(&env);

    client.register_organization(&organization_id, &owner);

    let key = DataKey::Organization(organization_id.clone());

    // Registration should extend the entry to the configured target.
    let initial_ttl = env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(initial_ttl >= TTL_BUMP_AMOUNT);

    // Advance the ledger until the entry is just below the renewal threshold.
    let ledgers_to_advance = initial_ttl - TTL_THRESHOLD + 1;
    let current_sequence = env.ledger().get().sequence_number;

    env.ledger()
        .set_sequence_number(current_sequence + ledgers_to_advance);

    let ttl_before_access =
        env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(ttl_before_access < TTL_THRESHOLD);

    // This read should trigger the TTL extension.
    let organization = client.get_organization(&organization_id);
    assert_eq!(organization.owner, owner);

    let ttl_after_access =
        env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(ttl_after_access >= TTL_BUMP_AMOUNT);
}

// Verifies that a public issuer-authorisation check renews the issuer entry.
#[test]
fn test_issuer_ttl_is_extended_on_access() {
    let env = Env::default();

    env.ledger().set_min_persistent_entry_ttl(100);
    env.ledger().set_max_entry_ttl(TTL_BUMP_AMOUNT + 1_000);
    env.mock_all_auths();

    let contract_id = env.register(CredentialRegistry, ());
    let client = CredentialRegistryClient::new(&env, &contract_id);

    let organization_id = BytesN::from_array(&env, &[91u8; 32]);
    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);

    let key = DataKey::Issuer(organization_id.clone(), issuer.clone());

    let initial_ttl = env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(initial_ttl >= TTL_BUMP_AMOUNT);

    let ledgers_to_advance = initial_ttl - TTL_THRESHOLD + 1;
    let current_sequence = env.ledger().get().sequence_number;

    env.ledger()
        .set_sequence_number(current_sequence + ledgers_to_advance);

    let ttl_before_access =
        env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(ttl_before_access < TTL_THRESHOLD);

    assert!(client.is_issuer_authorized(&organization_id, &issuer));

    let ttl_after_access =
        env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(ttl_after_access >= TTL_BUMP_AMOUNT);
}

// Verifies that public credential retrieval renews the credential entry.
#[test]
fn test_credential_ttl_is_extended_on_access() {
    let env = Env::default();

    env.ledger().set_min_persistent_entry_ttl(100);
    env.ledger().set_max_entry_ttl(TTL_BUMP_AMOUNT + 1_000);
    env.mock_all_auths();

    let contract_id = env.register(CredentialRegistry, ());
    let client = CredentialRegistryClient::new(&env, &contract_id);

    let organization_id = BytesN::from_array(&env, &[92u8; 32]);
    let credential_id = BytesN::from_array(&env, &[93u8; 32]);
    let commitment = BytesN::from_array(&env, &[94u8; 32]);

    let owner = Address::generate(&env);
    let issuer = Address::generate(&env);

    client.register_organization(&organization_id, &owner);
    client.authorize_issuer(&organization_id, &issuer);

    client.anchor_credential(&organization_id, &credential_id, &commitment, &issuer);

    let key = DataKey::Credential(credential_id.clone());

    let initial_ttl = env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(initial_ttl >= TTL_BUMP_AMOUNT);

    let ledgers_to_advance = initial_ttl - TTL_THRESHOLD + 1;
    let current_sequence = env.ledger().get().sequence_number;

    env.ledger()
        .set_sequence_number(current_sequence + ledgers_to_advance);

    let ttl_before_access =
        env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(ttl_before_access < TTL_THRESHOLD);

    let record = client.get_credential(&credential_id).unwrap();
    assert_eq!(record.commitment, commitment);
    assert!(!record.revoked);

    let ttl_after_access =
        env.as_contract(&contract_id, || env.storage().persistent().get_ttl(&key));

    assert!(ttl_after_access >= TTL_BUMP_AMOUNT);
}
