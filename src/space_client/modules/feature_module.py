from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.models import EvaluationError, FeatureEvaluationResult

if TYPE_CHECKING:
    from ..space_client import SpaceClient


class FeatureModule:
    def __init__(self, space_client: "SpaceClient") -> None:
        self._space_client = space_client

    def evaluate(
        self,
        user_id: str,
        feature_id: str,
        expected_consumption: dict[str, int | float] | None = None,
        details: bool = False,
        server: bool = False,
    ) -> FeatureEvaluationResult:
        expected_consumption = expected_consumption or {}
        cache = self._space_client.cache
        is_read_only = len(expected_consumption) == 0
        cache_key = cache.get_feature_key(user_id, feature_id)

        if is_read_only and cache.is_enabled():
            cached = cache.get(cache_key, parser=FeatureEvaluationResult.from_dict)
            if cached is not None:
                return cached

        query_params: list[str] = []
        if details:
            query_params.append("details=true")
        if server:
            query_params.append("server=true")
        query = "?" + "&".join(query_params) if query_params else ""

        payload = self._space_client._request_json(
            "POST",
            f"/features/{user_id}/{feature_id}{query}",
            json=expected_consumption,
        )
        if payload is None:
            return FeatureEvaluationResult(
                eval=False,
                used={},
                limit={},
                error=EvaluationError(code="IO_ERROR", message="Error while evaluating feature"),
            )

        result = FeatureEvaluationResult.from_dict(payload)

        if is_read_only and cache.is_enabled():
            cache.set(cache_key, payload, ttl=60)
        elif cache.is_enabled():
            cache.delete(cache_key)
            cache.delete(cache.get_contract_key(user_id))
            cache.delete(cache.get_pricing_token_key(user_id))

        return result

    def revert_evaluation(self, user_id: str, feature_id: str, revert_to_latest: bool = True) -> bool:
        success = self._space_client._request_no_content(
            "POST",
            f"/features/{user_id}?revert=true&latest={str(revert_to_latest).lower()}",
            json={},
        )
        if not success:
            return False

        cache = self._space_client.cache
        if cache.is_enabled():
            cache.delete(cache.get_feature_key(user_id, feature_id))
            cache.delete(cache.get_contract_key(user_id))
            cache.delete(cache.get_pricing_token_key(user_id))

        return True

    def generate_user_pricing_token(self, user_id: str) -> str | None:
        cache = self._space_client.cache
        cache_key = cache.get_pricing_token_key(user_id)

        if cache.is_enabled():
            cached = cache.get(cache_key)
            if isinstance(cached, str):
                return cached

        payload = self._space_client._request_json("POST", f"/features/{user_id}/pricing-token", json={})
        if payload is None:
            return None

        token = payload.get("pricingToken") if isinstance(payload, dict) else None
        if cache.is_enabled() and token is not None:
            cache.set(cache_key, token, ttl=900)

        return token

    # Java compatibility aliases
    revertEvaluation = revert_evaluation
    generateUserPricingToken = generate_user_pricing_token
