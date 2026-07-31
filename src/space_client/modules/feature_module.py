from __future__ import annotations

from typing import Any

from .. import _operations as operations
from .._result import Result
from ..types.models import FeatureEvaluationResult
from ._runner import AsyncRunner, SyncRunner


class _FeatureCalls:
    """The feature calls, written once.

    Each method says what to do and hands it to ``self._run``, which is the only
    part that differs between the synchronous and asynchronous clients. On
    :class:`FeatureModule` these methods return their value; on
    :class:`AsyncFeatureModule` they return an awaitable of that value.
    """

    _run: Any

    def evaluate(
        self,
        user_id: str,
        feature_id: str,
        expected_consumption: dict[str, int | float] | None = None,
        details: bool = False,
        server: bool = False,
    ) -> Result[FeatureEvaluationResult]:
        """Evaluate a feature for a user.

        Args:
            user_id (str): User identifier.
            feature_id (str): Feature identifier, usually `service-feature`.
            expected_consumption (dict[str, int | float] | None): Optional consumption
                projection used by Space for optimistic updates.
            details (bool): Whether to request detailed evaluation information.
            server (bool): Whether to force server-side evaluation mode.

        Returns:
            FeatureEvaluationResult: Evaluation outcome, including optional error payload.
        """
        return self._run(
            operations.evaluate(user_id, feature_id, expected_consumption, details, server)
        )

    def revert_evaluation(
        self, user_id: str, feature_id: str, revert_to_latest: bool = True
    ) -> Result[bool]:
        """Revert usage changes done by a previous optimistic evaluation.

        Args:
            user_id (str): User identifier.
            feature_id (str): Feature identifier.
            revert_to_latest (bool): True to restore latest value, False for earliest.

        Returns:
            bool: True when the revert request succeeds, otherwise False.
        """
        return self._run(operations.revert_evaluation(user_id, feature_id, revert_to_latest))

    def generate_user_pricing_token(self, user_id: str) -> Result[str | None]:
        """Generate a pricing token for a user.

        Args:
            user_id (str): User identifier.

        Returns:
            str | None: Token string on success, otherwise None.
        """
        return self._run(operations.generate_user_pricing_token(user_id))

    # Java compatibility aliases
    revertEvaluation = revert_evaluation
    generateUserPricingToken = generate_user_pricing_token


class FeatureModule(_FeatureCalls, SyncRunner):
    """Feature operations over the synchronous client."""


class AsyncFeatureModule(_FeatureCalls, AsyncRunner):
    """Feature operations over the asynchronous client.

    Same methods and same arguments as :class:`FeatureModule`; every one of them
    must be awaited.
    """
