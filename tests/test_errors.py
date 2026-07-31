from __future__ import annotations

from typing import Any

import httpx
import pytest

from space_client import SpaceApiError, SpaceConnectionError
from space_client.space_client import SpaceClient
from space_client.types import (
    BillingPeriodToCreate,
    ContractToCreate,
    SpaceConnectionOptions,
    UserContact,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: Any = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


def a_client() -> SpaceClient:
    return SpaceClient(SpaceConnectionOptions(url="http://localhost:3000", api_key="api-key"))


def a_contract() -> ContractToCreate:
    return ContractToCreate(
        user_contact=UserContact(user_id="user1", username="u1"),
        billing_period=BillingPeriodToCreate(auto_renew=True, renewal_days=30),
        contracted_services={"svc": "1.0.0"},
        subscription_plans={"svc": "FREE"},
        subscription_add_ons={},
    )


def responding(monkeypatch, client: SpaceClient, response):
    def fake_request(method, url, headers=None, json=None):
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(client._http_client, "request", fake_request)


# -- A refusal is not an absence -------------------------------------------


def test_a_refused_contract_raises_instead_of_returning_none(monkeypatch):
    """The failure this whole change exists for.

    Space refuses a contract whose plan is not in the registered pricing. The
    client returned None, which is also what it returns for "created, no body",
    so an application carried on believing its user was subscribed.
    """
    client = a_client()
    responding(
        monkeypatch,
        client,
        FakeResponse(
            400,
            {"error": "Invalid subscription: Plan FREE for service svc not found"},
        ),
    )

    with pytest.raises(SpaceApiError) as error:
        client.contracts.add_contract(a_contract())

    assert error.value.status_code == 400
    # The body is where Space explains itself, and it was being discarded.
    assert "Plan FREE for service svc not found" in str(error.value)


def test_the_error_says_which_call_was_refused(monkeypatch):
    client = a_client()
    responding(monkeypatch, client, FakeResponse(404, {"error": "not found"}))

    with pytest.raises(SpaceApiError) as error:
        client.contracts.get_contract("nobody")

    assert error.value.method == "GET"
    assert error.value.path == "/contracts/nobody"


def test_an_unauthorised_call_is_not_silently_empty(monkeypatch):
    # A wrong or missing API key produced the same None as an empty result, so
    # a misconfigured deployment looked like an empty one.
    client = a_client()
    responding(
        monkeypatch,
        client,
        FakeResponse(401, {"error": "API Key not found."}),
    )

    with pytest.raises(SpaceApiError) as error:
        client.contracts.get_contract("user1")

    assert error.value.status_code == 401


def test_a_refusal_with_details_keeps_both_parts(monkeypatch):
    client = a_client()
    responding(
        monkeypatch,
        client,
        FakeResponse(403, {"error": "Forbidden", "details": "scope MANAGEMENT required"}),
    )

    with pytest.raises(SpaceApiError) as error:
        client.contracts.get_contract("user1")

    assert "Forbidden" in str(error.value)
    assert "MANAGEMENT" in str(error.value)


def test_a_refusal_whose_body_is_not_json_still_reports_something(monkeypatch):
    client = a_client()
    responding(monkeypatch, client, FakeResponse(502, None, text="<html>bad gateway</html>"))

    with pytest.raises(SpaceApiError) as error:
        client.contracts.get_contract("user1")

    assert error.value.status_code == 502
    assert "bad gateway" in str(error.value)


# -- An outage is not a refusal either --------------------------------------


def test_an_unreachable_space_is_reported_as_such(monkeypatch):
    """Three situations used to share one return value.

    A caller could not tell "Space said no" from "Space was not there" from
    "there was nothing to return", so the only options were to treat every
    failure as absence or to guess.
    """
    client = a_client()
    responding(monkeypatch, client, httpx.ConnectError("connection refused"))

    with pytest.raises(SpaceConnectionError) as error:
        client.contracts.get_contract("user1")

    assert "localhost:3000" in str(error.value)


def test_a_timeout_is_a_connection_problem_not_an_answer(monkeypatch):
    client = a_client()
    responding(monkeypatch, client, httpx.ReadTimeout("timed out"))

    with pytest.raises(SpaceConnectionError):
        client.contracts.get_contract("user1")


# -- Success is unchanged ---------------------------------------------------


def test_a_successful_call_still_returns_its_payload(monkeypatch):
    client = a_client()
    responding(
        monkeypatch,
        client,
        FakeResponse(200, {"userContact": {"userId": "user1", "username": "u1"}}),
    )

    contract = client.contracts.get_contract("user1")

    assert contract is not None
    assert contract.user_id == "user1"


def test_a_success_with_no_json_body_is_still_none(monkeypatch):
    # The one meaning None keeps: Space accepted the call and sent nothing
    # decodable. It no longer stands in for a refusal as well.
    client = a_client()
    responding(monkeypatch, client, FakeResponse(204, None, text=""))

    assert client.contracts.get_contract("user1") is None


def test_errors_share_a_base_for_callers_who_do_not_care_which(monkeypatch):
    from space_client import SpaceError

    assert issubclass(SpaceApiError, SpaceError)
    assert issubclass(SpaceConnectionError, SpaceError)
