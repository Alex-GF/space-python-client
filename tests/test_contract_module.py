from __future__ import annotations

from typing import Any

from space_client.space_client import SpaceClient
from space_client.types import BillingPeriodToCreate, ContractToCreate, SpaceConnectionOptions, Subscription, UserContact


class FakeResponse:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_contract_crud_and_group_update(monkeypatch):
    client = SpaceClient(SpaceConnectionOptions(url="http://localhost:3000", api_key="api-key"))

    def fake_request(method, url, headers=None, json=None):
        if method == "GET" and url.endswith("/api/v1/contracts/user1"):
            return FakeResponse(200, {"userContact": {"userId": "user1", "username": "u1"}})

        if method == "POST" and url.endswith("/api/v1/contracts"):
            return FakeResponse(200, {"userContact": {"userId": json["userContact"]["userId"], "username": "u2"}})

        if method == "PUT" and url.endswith("/api/v1/contracts/user1"):
            return FakeResponse(200, {"userContact": {"userId": "user1", "username": "u1"}, "subscriptionPlans": json["subscriptionPlans"]})

        if method == "PUT" and url.endswith("/api/v1/contracts?groupId=groupA"):
            return FakeResponse(
                200,
                [
                    {"userContact": {"userId": "uA1", "username": "a1"}, "groupId": "groupA"},
                    {"userContact": {"userId": "uA2", "username": "a2"}, "groupId": "groupA"},
                ],
            )

        if method == "PUT" and url.endswith("/api/v1/contracts/user1/usageLevels"):
            return FakeResponse(200, {"userContact": {"userId": "user1", "username": "u1"}, "usageLevels": json})

        if method == "DELETE" and url.endswith("/api/v1/contracts/user1"):
            return FakeResponse(204, {})

        return FakeResponse(500, {"error": "unexpected"})

    monkeypatch.setattr(client._http_client, "request", fake_request)

    contract = client.contracts.get_contract("user1")
    assert contract is not None
    assert contract.user_id == "user1"

    to_create = ContractToCreate(
        user_contact=UserContact(user_id="user2", username="u2"),
        billing_period=BillingPeriodToCreate(auto_renew=True, renewal_days=30),
        contracted_services={"zoom": "2025"},
    )
    created = client.contracts.add_contract(to_create)
    assert created is not None
    assert created.user_id == "user2"

    updated = client.contracts.update_contract_subscription(
        "user1",
        Subscription(subscription_plans={"zoom": "ENTERPRISE"}),
    )
    assert updated is not None
    assert updated.subscription_plans["zoom"] == "ENTERPRISE"

    by_group = client.contracts.update_contract_subscription_by_group_id(
        "groupA",
        Subscription(subscription_plans={"zoom": "PRO"}),
    )
    assert by_group is not None
    assert len(by_group) == 2

    usage_updated = client.contracts.update_contract_usage_levels("user1", "zoom", {"seats": 10})
    assert usage_updated is not None

    client.contracts.remove_contract("user1")
