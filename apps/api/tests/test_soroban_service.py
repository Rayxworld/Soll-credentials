from types import SimpleNamespace

import pytest
from stellar_sdk.network import Network

from app.core.config import settings
from app.services import soroban


def test_network_passphrase_must_match_network_setting(monkeypatch):
    monkeypatch.setattr(settings, "soroban_rpc_url", "https://rpc.example")
    monkeypatch.setattr(settings, "soroban_contract_id", "C" + "A" * 55)
    monkeypatch.setattr(
        settings,
        "soroban_network_passphrase",
        Network.PUBLIC_NETWORK_PASSPHRASE,
    )
    monkeypatch.setattr(settings, "stellar_network", "testnet")

    with pytest.raises(soroban.SorobanNotConfiguredError):
        soroban._configured_contract_client()


def test_network_passphrase_accepts_matching_testnet(monkeypatch):
    monkeypatch.setattr(settings, "soroban_rpc_url", "https://rpc.example")
    monkeypatch.setattr(settings, "soroban_contract_id", "C" + "A" * 55)
    monkeypatch.setattr(
        settings,
        "soroban_network_passphrase",
        Network.TESTNET_NETWORK_PASSPHRASE,
    )
    monkeypatch.setattr(settings, "stellar_network", "testnet")

    class FakeClient:
        pass

    monkeypatch.setattr(soroban, "ContractClient", lambda **_: FakeClient())

    assert isinstance(soroban._configured_contract_client(), FakeClient)


def test_invoke_read_returns_simulated_result_and_closes_client(monkeypatch):
    class FakeServer:
        closed = False

        def close(self):
            self.closed = True

    class FakeAssembled:
        def result(self):
            return {"active": True}

    class FakeClient:
        def __init__(self):
            self.server = FakeServer()
            self.invoked = None

        def invoke(self, function_name, **kwargs):
            self.invoked = (function_name, kwargs)
            return FakeAssembled()

    client = FakeClient()
    monkeypatch.setattr(soroban, "_configured_contract_client", lambda: client)

    result = soroban._invoke_read("get_organization", [])

    assert result == {"active": True}
    assert client.invoked[0] == "get_organization"
    assert client.invoked[1]["parse_result_xdr_fn"] is soroban.scval.to_native
    assert client.server.closed is True


def test_normalise_optional_record_handles_none_and_some():
    record = {"revoked": False}

    assert soroban._normalise_optional_record(None) is None
    assert soroban._normalise_optional_record([]) is None
    assert soroban._normalise_optional_record([record]) == record


def test_normalise_optional_record_rejects_invalid_option_shape():
    with pytest.raises(soroban.SorobanUnavailableError):
        soroban._normalise_optional_record([{}, {}])


def test_get_credential_record_converts_contract_fields(monkeypatch):
    issuer = "GCJ22TNGAVLGOEI6OS4RUUK2KPLYQFDGRPNXTZH2YJCAH3DBWWESEMD2"
    monkeypatch.setattr(
        soroban,
        "_invoke_read",
        lambda *_: {
            "organization_id": bytes.fromhex("11" * 32),
            "commitment": bytes.fromhex("22" * 32),
            "issuer": SimpleNamespace(address=issuer),
            "issued_at": 123456,
            "revoked": False,
        },
    )

    result = soroban.get_credential_record(bytes.fromhex("33" * 32))

    assert result == {
        "organization_id": bytes.fromhex("11" * 32),
        "commitment": bytes.fromhex("22" * 32),
        "issuer": issuer,
        "issued_at": 123456,
        "revoked": False,
    }


def test_get_credential_record_rejects_wrong_id_length():
    with pytest.raises(ValueError):
        soroban.get_credential_record(b"too-short")


def test_issuer_authorization_requires_boolean_result(monkeypatch):
    monkeypatch.setattr(soroban, "_invoke_read", lambda *_: "true")

    with pytest.raises(soroban.SorobanUnavailableError):
        soroban.is_issuer_authorized(
            bytes.fromhex("11" * 32),
            "GCJ22TNGAVLGOEI6OS4RUUK2KPLYQFDGRPNXTZH2YJCAH3DBWWESEMD2",
        )
