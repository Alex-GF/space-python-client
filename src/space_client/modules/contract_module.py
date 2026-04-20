from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.models import Contract, ContractToCreate, Subscription

if TYPE_CHECKING:
    from ..space_client import SpaceClient


class ContractModule:
    def __init__(self, space_client: "SpaceClient") -> None:
        self._space_client = space_client

    def get_contract(self, user_id: str) -> Contract | None:
        cache = self._space_client.cache
        cache_key = cache.get_contract_key(user_id)

        if cache.is_enabled():
            cached = cache.get(cache_key, parser=Contract.from_dict)
            if cached is not None:
                return cached

        payload = self._space_client._request_json("GET", f"/contracts/{user_id}")
        if payload is None:
            return None

        contract = Contract.from_dict(payload)
        if cache.is_enabled():
            cache.set(cache_key, payload)
        return contract

    def add_contract(self, contract_to_create: ContractToCreate) -> Contract | None:
        payload = self._space_client._request_json("POST", "/contracts", json=contract_to_create.to_dict())
        if payload is None:
            return None

        contract = Contract.from_dict(payload)
        cache = self._space_client.cache
        if cache.is_enabled() and contract.user_id is not None:
            cache.invalidate_user(contract.user_id)
            cache.set(cache.get_contract_key(contract.user_id), payload)
        return contract

    def update_contract_subscription(self, user_id: str, new_subscription: Subscription) -> Contract | None:
        payload = self._space_client._request_json(
            "PUT",
            f"/contracts/{user_id}",
            json=new_subscription.to_dict(),
        )
        if payload is None:
            return None

        contract = Contract.from_dict(payload)
        cache = self._space_client.cache
        if cache.is_enabled():
            cache.invalidate_user(user_id)
            cache.set(cache.get_contract_key(user_id), payload)
        return contract

    def update_contract_subscription_by_group_id(
        self,
        group_id: str,
        new_subscription: Subscription,
    ) -> list[Contract] | None:
        payload = self._space_client._request_json(
            "PUT",
            f"/contracts?groupId={group_id}",
            json=new_subscription.to_dict(),
        )
        if payload is None or not isinstance(payload, list):
            return None

        contracts = [Contract.from_dict(item) for item in payload]
        cache = self._space_client.cache
        if cache.is_enabled():
            for contract, raw in zip(contracts, payload):
                if contract.user_id is None:
                    continue
                cache.invalidate_user(contract.user_id)
                cache.set(cache.get_contract_key(contract.user_id), raw)
        return contracts

    def update_contract_usage_levels(
        self,
        user_id: str,
        service_name: str,
        usage_levels_novations: dict[str, int | float],
    ) -> Contract | None:
        payload = self._space_client._request_json(
            "PUT",
            f"/contracts/{user_id}/usageLevels",
            json={service_name: usage_levels_novations},
        )
        if payload is None:
            return None

        contract = Contract.from_dict(payload)
        cache = self._space_client.cache
        if cache.is_enabled():
            cache.invalidate_user(user_id)
            cache.set(cache.get_contract_key(user_id), payload)
        return contract

    def remove_contract(self, user_id: str) -> None:
        response_ok = self._space_client._request_no_content("DELETE", f"/contracts/{user_id}")
        if not response_ok:
            return
        if self._space_client.cache.is_enabled():
            self._space_client.cache.invalidate_user(user_id)

    # Java compatibility aliases
    getContract = get_contract
    addContract = add_contract
    updateContractSubscription = update_contract_subscription
    updateContractSubscriptionByGroupId = update_contract_subscription_by_group_id
    updateContractUsageLevels = update_contract_usage_levels
    removeContract = remove_contract
