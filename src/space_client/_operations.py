"""What each call does, with the transport left out.

The synchronous and asynchronous clients differ in exactly one respect: how a
request is sent and awaited. Everything else - which cache key to look under,
what to send, how to read the answer back, which cache entries the answer
invalidates - is the same in both, and lives here so it is written once.

An :class:`Operation` is a description, not a call. It says what to look for in
the cache before asking Space, what request to make, and what to do with the
body that comes back. The runners in :mod:`space_client.modules` supply the one
part that must differ.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from .types.models import Contract, ContractToCreate, EvaluationError, FeatureEvaluationResult, Subscription

if TYPE_CHECKING:
    from .modules.cache_module import CacheModule

T = TypeVar("T")


@dataclass(frozen=True)
class Operation(Generic[T]):
    """One call to Space, described rather than made.

    Attributes:
        method: HTTP method.
        path: Path below ``/api/v1``.
        json: Body to send, if any.
        no_content: True when the call answers with a status rather than a body,
            in which case ``parse`` receives the boolean from the transport.
        cache_hit: Consulted before the request; a non-None result is returned
            to the caller and the request is never made. Only set for calls that
            are safe to serve from cache.
        parse: Turns what came back into the caller's result, and applies
            whatever the answer implies for the cache.
    """

    method: str
    path: str
    json: Any | None = None
    no_content: bool = False
    cache_hit: Callable[["CacheModule"], T | None] | None = None
    parse: Callable[["CacheModule", Any], T] = field(
        default=lambda _cache, payload: payload  # type: ignore[assignment,return-value]
    )


# --------------------------------------------------------------------------
# Contracts
# --------------------------------------------------------------------------


def get_contract(user_id: str) -> Operation[Contract | None]:
    def hit(cache: "CacheModule") -> Contract | None:
        return cache.get(cache.get_contract_key(user_id), parser=Contract.from_dict)

    def parse(cache: "CacheModule", payload: Any) -> Contract | None:
        if payload is None:
            return None
        contract = Contract.from_dict(payload)
        if cache.is_enabled():
            cache.set(cache.get_contract_key(user_id), payload)
        return contract

    return Operation("GET", f"/contracts/{user_id}", cache_hit=hit, parse=parse)


def add_contract(contract_to_create: ContractToCreate) -> Operation[Contract | None]:
    def parse(cache: "CacheModule", payload: Any) -> Contract | None:
        if payload is None:
            return None
        contract = Contract.from_dict(payload)
        if cache.is_enabled() and contract.user_id is not None:
            cache.invalidate_user(contract.user_id)
            cache.set(cache.get_contract_key(contract.user_id), payload)
        return contract

    return Operation("POST", "/contracts", json=contract_to_create.to_dict(), parse=parse)


def update_contract_subscription(user_id: str, new_subscription: Subscription) -> Operation[Contract | None]:
    return Operation(
        "PUT",
        f"/contracts/{user_id}",
        json=new_subscription.to_dict(),
        parse=_replace_one(user_id),
    )


def update_contract_subscription_by_group_id(
    group_id: str,
    new_subscription: Subscription,
) -> Operation[list[Contract] | None]:
    def parse(cache: "CacheModule", payload: Any) -> list[Contract] | None:
        if payload is None or not isinstance(payload, list):
            return None
        contracts = [Contract.from_dict(item) for item in payload]
        if cache.is_enabled():
            for contract, raw in zip(contracts, payload):
                if contract.user_id is None:
                    continue
                cache.invalidate_user(contract.user_id)
                cache.set(cache.get_contract_key(contract.user_id), raw)
        return contracts

    return Operation(
        "PUT",
        f"/contracts?groupId={group_id}",
        json=new_subscription.to_dict(),
        parse=parse,
    )


def update_contract_usage_levels(
    user_id: str,
    service_name: str,
    usage_levels_novations: dict[str, int | float],
) -> Operation[Contract | None]:
    return Operation(
        "PUT",
        f"/contracts/{user_id}/usageLevels",
        json={service_name: usage_levels_novations},
        parse=_replace_one(user_id),
    )


def remove_contract(user_id: str) -> Operation[None]:
    def parse(cache: "CacheModule", accepted: Any) -> None:
        if not accepted:
            return None
        if cache.is_enabled():
            cache.invalidate_user(user_id)
        return None

    return Operation("DELETE", f"/contracts/{user_id}", no_content=True, parse=parse)


def _replace_one(user_id: str) -> Callable[["CacheModule", Any], Contract | None]:
    """The answer is this user's whole contract: forget what we knew, keep it."""

    def parse(cache: "CacheModule", payload: Any) -> Contract | None:
        if payload is None:
            return None
        contract = Contract.from_dict(payload)
        if cache.is_enabled():
            cache.invalidate_user(user_id)
            cache.set(cache.get_contract_key(user_id), payload)
        return contract

    return parse


# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------


def evaluate(
    user_id: str,
    feature_id: str,
    expected_consumption: dict[str, int | float] | None = None,
    details: bool = False,
    server: bool = False,
) -> Operation[FeatureEvaluationResult]:
    expected_consumption = expected_consumption or {}

    # An evaluation that spends nothing can be answered from cache; one that
    # spends something has to reach Space, and invalidates what we held.
    is_read_only = len(expected_consumption) == 0

    def hit(cache: "CacheModule") -> FeatureEvaluationResult | None:
        if not is_read_only:
            return None
        return cache.get(
            cache.get_feature_key(user_id, feature_id),
            parser=FeatureEvaluationResult.from_dict,
        )

    def parse(cache: "CacheModule", payload: Any) -> FeatureEvaluationResult:
        if payload is None:
            return FeatureEvaluationResult(
                eval=False,
                used={},
                limit={},
                error=EvaluationError(code="IO_ERROR", message="Error while evaluating feature"),
            )

        result = FeatureEvaluationResult.from_dict(payload)

        if cache.is_enabled():
            if is_read_only:
                cache.set(cache.get_feature_key(user_id, feature_id), payload, ttl=60)
            else:
                cache.delete(cache.get_feature_key(user_id, feature_id))
                cache.delete(cache.get_contract_key(user_id))
                cache.delete(cache.get_pricing_token_key(user_id))

        return result

    query_params: list[str] = []
    if details:
        query_params.append("details=true")
    if server:
        query_params.append("server=true")
    query = "?" + "&".join(query_params) if query_params else ""

    return Operation(
        "POST",
        f"/features/{user_id}/{feature_id}{query}",
        json=expected_consumption,
        cache_hit=hit,
        parse=parse,
    )


def revert_evaluation(user_id: str, feature_id: str, revert_to_latest: bool = True) -> Operation[bool]:
    def parse(cache: "CacheModule", accepted: Any) -> bool:
        if not accepted:
            return False
        if cache.is_enabled():
            cache.delete(cache.get_feature_key(user_id, feature_id))
            cache.delete(cache.get_contract_key(user_id))
            cache.delete(cache.get_pricing_token_key(user_id))
        return True

    return Operation(
        "POST",
        f"/features/{user_id}?revert=true&latest={str(revert_to_latest).lower()}",
        json={},
        no_content=True,
        parse=parse,
    )


def generate_user_pricing_token(user_id: str) -> Operation[str | None]:
    def hit(cache: "CacheModule") -> str | None:
        cached = cache.get(cache.get_pricing_token_key(user_id))
        return cached if isinstance(cached, str) else None

    def parse(cache: "CacheModule", payload: Any) -> str | None:
        if payload is None:
            return None
        token = payload.get("pricingToken") if isinstance(payload, dict) else None
        if cache.is_enabled() and token is not None:
            cache.set(cache.get_pricing_token_key(user_id), token, ttl=900)
        return token

    return Operation(
        "POST",
        f"/features/{user_id}/pricing-token",
        json={},
        cache_hit=hit,
        parse=parse,
    )


def healthcheck() -> Operation[bool]:
    def parse(_cache: "CacheModule", payload: Any) -> bool:
        return isinstance(payload, dict) and "message" in payload

    return Operation("GET", "/healthcheck", parse=parse)
