from typing import Any

from stellar_sdk import scval
from stellar_sdk.contract import ContractClient
from stellar_sdk.network import Network

from app.core.config import settings


class SorobanNotConfiguredError(RuntimeError):
    pass


class SorobanUnavailableError(RuntimeError):
    pass


def _configured_contract_client() -> ContractClient:
    rpc_url = settings.soroban_rpc_url
    network_passphrase = settings.soroban_network_passphrase
    contract_id = settings.soroban_contract_id

    if not all((rpc_url, network_passphrase, contract_id)):
        raise SorobanNotConfiguredError(
            "Soroban RPC configuration is incomplete."
        )

    expected_passphrases = {
        "testnet": Network.TESTNET_NETWORK_PASSPHRASE,
        "public": Network.PUBLIC_NETWORK_PASSPHRASE,
    }
    expected_passphrase = expected_passphrases.get(
        settings.stellar_network.lower()
    )
    if expected_passphrase is None or network_passphrase != expected_passphrase:
        raise SorobanNotConfiguredError(
            "The configured Stellar network and passphrase do not match."
        )

    try:
        return ContractClient(
            contract_id=contract_id,
            rpc_url=rpc_url,
            network_passphrase=network_passphrase,
        )
    except Exception as exc:
        raise SorobanUnavailableError(
            "The Soroban client could not be initialized."
        ) from exc


def _invoke_read(function_name: str, parameters: list[Any]) -> Any:
    client = _configured_contract_client()
    try:
        assembled = client.invoke(
            function_name,
            parameters=parameters,
            parse_result_xdr_fn=scval.to_native,
        )
        # invoke() simulates by default; result() returns the simulated
        # contract result and does not submit a transaction.
        return assembled.result()
    except SorobanNotConfiguredError:
        raise
    except Exception as exc:
        # Do not expose RPC response bodies or internal endpoint details.
        raise SorobanUnavailableError(
            "The Soroban network query failed."
        ) from exc
    finally:
        try:
            client.server.close()
        except Exception:
            # A cleanup failure must not hide the RPC result or its exception.
            pass


def _normalise_optional_record(value: Any) -> dict[str, Any] | None:
    # Soroban Option<T> is encoded as a vector containing zero or one values.
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        if len(value) != 1:
            raise SorobanUnavailableError(
                "The Soroban contract returned an invalid credential value."
            )
        value = value[0]
    if not isinstance(value, dict):
        raise SorobanUnavailableError(
            "The Soroban contract returned an invalid credential value."
        )
    return value


def get_credential_record(credential_id: bytes) -> dict[str, Any] | None:
    if not isinstance(credential_id, bytes) or len(credential_id) != 32:
        raise ValueError("Credential ID must contain exactly 32 bytes.")

    value = _invoke_read(
        "get_credential",
        [scval.to_bytes(credential_id)],
    )
    record = _normalise_optional_record(value)
    if record is None:
        return None

    try:
        organization_id = record["organization_id"]
        commitment = record["commitment"]
        issuer = record["issuer"]
        issued_at = record["issued_at"]
        revoked = record["revoked"]

        # The SDK converts Soroban Address values to Address objects.
        issuer_address = issuer.address if hasattr(issuer, "address") else str(issuer)

        if (
            not isinstance(organization_id, bytes)
            or len(organization_id) != 32
            or not isinstance(commitment, bytes)
            or len(commitment) != 32
            or not isinstance(issued_at, int)
            or isinstance(issued_at, bool)
            or not isinstance(revoked, bool)
            or not issuer_address
        ):
            raise ValueError("Unexpected Soroban credential field types.")

        return {
            "organization_id": organization_id,
            "commitment": commitment,
            "issuer": issuer_address,
            "issued_at": issued_at,
            "revoked": revoked,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise SorobanUnavailableError(
            "The Soroban contract returned an invalid credential record."
        ) from exc


def is_issuer_authorized(
    organization_id: bytes,
    issuer_address: str,
) -> bool:
    if not isinstance(organization_id, bytes) or len(organization_id) != 32:
        raise ValueError("Organization ID must contain exactly 32 bytes.")

    try:
        issuer_value = scval.to_address(issuer_address)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid Stellar issuer address.") from exc

    value = _invoke_read(
        "is_issuer_authorized",
        [
            scval.to_bytes(organization_id),
            issuer_value,
        ],
    )
    if not isinstance(value, bool):
        raise SorobanUnavailableError(
            "The Soroban contract returned an invalid issuer status."
        )
    return value
