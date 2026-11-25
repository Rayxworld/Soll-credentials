import uuid
import secrets
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    CertificateTemplate,
    CertificateTemplateVersion,
    Credential,
    Organization,
    OrganizationMembership,
    Program,
    Recipient,
    User,
)


def make_base_records(db):
    user = User(email=f"{uuid.uuid4().hex}@example.com")
    org = Organization(name="Test Organization", slug=uuid.uuid4().hex)
    db.add_all([user, org])
    db.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    recipient = Recipient(
        organization_id=org.id,
        full_name="Test Recipient",
        email="recipient@example.com",
        external_reference=uuid.uuid4().hex,
    )
    program = Program(
        organization_id=org.id,
        name="Test Programme",
        code=uuid.uuid4().hex,
    )
    template = CertificateTemplate(
        organization_id=org.id,
        name=f"Template {uuid.uuid4().hex}",
    )
    db.add_all([membership, recipient, program, template])
    db.flush()

    version = CertificateTemplateVersion(
        template_id=template.id,
        version_number=1,
        configuration={"title": "Test Certificate"},
    )
    db.add(version)
    db.flush()

    return user, org, membership, recipient, program, template, version


def make_credential(records, **overrides):
    user, org, _, recipient, program, _, version = records

    values = {
        "credential_id": secrets.token_bytes(32),
        "organization_id": org.id,
        "recipient_id": recipient.id,
        "program_id": program.id,
        "template_version_id": version.id,
        "issued_by_user_id": user.id,
        "commitment": secrets.token_bytes(32),
        "credential_data": b"encrypted-credential-data",
        "blinding_value_encrypted": b"encrypted-blinding-value",
        "pdf_storage_key": "credentials/test.pdf",
    }
    values.update(overrides)
    return Credential(**values)


def test_create_all_models(db_session):
    records = make_base_records(db_session)
    user, org, membership, recipient, program, template, version = records

    assert db_session.get(User, user.id) is not None
    assert db_session.get(Organization, org.id) is not None
    assert db_session.get(OrganizationMembership, membership.id) is not None
    assert db_session.get(Recipient, recipient.id) is not None
    assert db_session.get(Program, program.id) is not None
    assert db_session.get(CertificateTemplate, template.id) is not None
    assert db_session.get(CertificateTemplateVersion, version.id) is not None


def test_user_email_is_case_insensitively_unique(db_session):
    email = f"{uuid.uuid4().hex}@example.com"
    db_session.add(User(email=email))
    db_session.flush()

    db_session.add(User(email=email.upper()))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_organization_slug_is_unique(db_session):
    slug = uuid.uuid4().hex
    db_session.add_all([
        Organization(name="First", slug=slug),
        Organization(name="Second", slug=slug),
    ])

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_organization_rejects_invalid_custody_mode(db_session):
    db_session.add(
        Organization(
            name="Invalid Custody",
            slug=uuid.uuid4().hex,
            custody_mode="unknown",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_organization_rejects_invalid_on_chain_id_length(db_session):
    db_session.add(
        Organization(
            name="Invalid Chain ID",
            slug=uuid.uuid4().hex,
            on_chain_org_id=b"too-short",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_membership_rejects_invalid_role(db_session):
    user = User(email=f"{uuid.uuid4().hex}@example.com")
    org = Organization(name="Role Test", slug=uuid.uuid4().hex)
    db_session.add_all([user, org])
    db_session.flush()

    db_session.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role="superuser",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_membership_rejects_duplicate_org_user(db_session):
    records = make_base_records(db_session)
    user, org = records[0], records[1]

    db_session.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role="admin",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_recipient_external_reference_unique_per_org(db_session):
    _, org, _, _, _, _, _ = make_base_records(db_session)
    reference = uuid.uuid4().hex

    db_session.add_all([
        Recipient(
            organization_id=org.id,
            full_name="First Recipient",
            external_reference=reference,
        ),
        Recipient(
            organization_id=org.id,
            full_name="Second Recipient",
            external_reference=reference,
        ),
    ])

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_program_code_unique_per_org(db_session):
    _, org, _, _, _, _, _ = make_base_records(db_session)
    code = uuid.uuid4().hex

    db_session.add_all([
        Program(organization_id=org.id, name="First", code=code),
        Program(organization_id=org.id, name="Second", code=code),
    ])

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_template_name_unique_per_org(db_session):
    _, org, _, _, _, _, _ = make_base_records(db_session)
    name = f"Template {uuid.uuid4().hex}"

    db_session.add_all([
        CertificateTemplate(organization_id=org.id, name=name),
        CertificateTemplate(organization_id=org.id, name=name),
    ])

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_template_version_must_be_positive(db_session):
    _, _, _, _, _, template, _ = make_base_records(db_session)

    db_session.add(
        CertificateTemplateVersion(
            template_id=template.id,
            version_number=0,
            configuration={},
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_template_version_number_unique_per_template(db_session):
    _, _, _, _, _, template, _ = make_base_records(db_session)

    db_session.add(
        CertificateTemplateVersion(
            template_id=template.id,
            version_number=1,
            configuration={"title": "Duplicate"},
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_credential_can_be_created(db_session):
    records = make_base_records(db_session)
    credential = make_credential(records)

    db_session.add(credential)
    db_session.flush()

    assert credential.id is not None
    assert len(credential.credential_id) == 32
    assert len(credential.commitment) == 32
    assert credential.revoked_at is None
    assert credential.revocation_reason is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("credential_id", b"short"),
        ("commitment", b"short"),
    ],
)
def test_credential_rejects_invalid_32_byte_values(
    db_session, field, value
):
    records = make_base_records(db_session)
    credential = make_credential(records, **{field: value})
    db_session.add(credential)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_credential_id_must_be_unique(db_session):
    records = make_base_records(db_session)
    credential_id = secrets.token_bytes(32)

    db_session.add(make_credential(records, credential_id=credential_id))
    db_session.flush()

    db_session.add(make_credential(records, credential_id=credential_id))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_credential_requires_encrypted_blinding_value(db_session):
    records = make_base_records(db_session)
    credential = make_credential(records, blinding_value_encrypted=None)
    db_session.add(credential)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_credential_revocation_after_issuance(db_session):
    records = make_base_records(db_session)
    credential = make_credential(
        records,
        revoked_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(credential)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_credential_reason_requires_revocation(db_session):
    records = make_base_records(db_session)
    credential = make_credential(
        records,
        revocation_reason="Invalid issuance",
    )
    db_session.add(credential)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_credential_can_be_revoked_with_reason(db_session):
    records = make_base_records(db_session)
    credential = make_credential(
        records,
        revoked_at=datetime.now(timezone.utc) + timedelta(seconds=5),
        revocation_reason="Invalid issuance",
    )
    db_session.add(credential)
    db_session.flush()

    assert credential.revoked_at is not None
    assert credential.revocation_reason == "Invalid issuance"



def test_organization_rejects_multiple_active_owners(db_session):
    _, org, _, _, _, _, _ = make_base_records(db_session)
    second_user = User(email=f"{uuid.uuid4().hex}@example.com")
    db_session.add(second_user)
    db_session.flush()

    db_session.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=second_user.id,
            role="owner",
            is_active=True,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_separate_organizations_can_have_active_owners(db_session):
    first_records = make_base_records(db_session)
    second_records = make_base_records(db_session)

    db_session.flush()

    first_owner = first_records[2]
    second_owner = second_records[2]

    assert first_owner.role == "owner"
    assert second_owner.role == "owner"
    assert first_owner.organization_id != second_owner.organization_id


def test_inactive_owner_does_not_conflict_with_active_owner(db_session):
    _, org, old_owner, _, _, _, _ = make_base_records(db_session)
    old_owner.is_active = False

    new_user = User(email=f"{uuid.uuid4().hex}@example.com")
    db_session.add(new_user)
    db_session.flush()

    new_owner = OrganizationMembership(
        organization_id=org.id,
        user_id=new_user.id,
        role="owner",
        is_active=True,
    )
    db_session.add(new_owner)
    db_session.flush()

    assert old_owner.is_active is False
    assert new_owner.is_active is True
