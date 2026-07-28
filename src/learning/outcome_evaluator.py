from typing import Dict

from models.outcome_metrics import OutcomeMetrics


class OutcomeEvaluator:
    """
    Evaluates the business impact of an executed decision.

    It compares business metrics before and after execution
    and produces a normalized reward between -1.0 and 1.0.
    """

    DEFAULT_WEIGHTS = {
        "revenue": 0.25,
        "profit": 0.30,
        "conversion": 0.20,
        "inventory_health": 0.15,
        "customer_satisfaction": 0.10
    }

    def __init__(
        self,
        weights: Dict[str, float] | None = None
    ):
        self.weights = (
            weights.copy()
            if weights is not None
            else self.DEFAULT_WEIGHTS.copy()
        )

        self._validate_weights()

    def evaluate(
        self,
        decision_id: str,
        target: str,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float]
    ) -> OutcomeMetrics:
        """
        Compare metrics before and after execution.

        Required metric keys:

        revenue
        profit
        conversion_rate
        inventory_health
        customer_satisfaction
        """

        self._validate_metrics(
            before_metrics,
            "before_metrics"
        )

        self._validate_metrics(
            after_metrics,
            "after_metrics"
        )

        revenue_change = self._percentage_change(
            before_metrics["revenue"],
            after_metrics["revenue"]
        )

        profit_change = self._percentage_change(
            before_metrics["profit"],
            after_metrics["profit"]
        )

        conversion_change = self._percentage_change(
            before_metrics["conversion_rate"],
            after_metrics["conversion_rate"]
        )

        inventory_health_change = round(
           after_metrics["inventory_health"]
           - before_metrics["inventory_health"],
            4
       )

        customer_satisfaction_change = round(
            after_metrics["customer_satisfaction"]
            - before_metrics["customer_satisfaction"],
            4
        )

        metric_scores = {
            "revenue": self._normalize_percentage(
                revenue_change
            ),
            "profit": self._normalize_percentage(
                profit_change
            ),
            "conversion": self._normalize_percentage(
                conversion_change
            ),
            "inventory_health": self._clamp(
                inventory_health_change
            ),
            "customer_satisfaction": self._clamp(
                customer_satisfaction_change
            )
        }

        overall_reward = self._calculate_reward(
            metric_scores
        )

        outcome_status = self._classify_outcome(
            overall_reward
        )

        return OutcomeMetrics(
            decision_id=decision_id,
            target=target,
            revenue_change_percentage=revenue_change,
            profit_change_percentage=profit_change,
            conversion_change_percentage=conversion_change,
            inventory_health_change=inventory_health_change,
            customer_satisfaction_change=(
                customer_satisfaction_change
            ),
            overall_reward=overall_reward,
            outcome_status=outcome_status,
            metric_scores=metric_scores
        )

    def _calculate_reward(
        self,
        metric_scores: Dict[str, float]
    ) -> float:
        """
        Calculate the weighted business reward.
        """

        reward = (
            metric_scores["revenue"]
            * self.weights["revenue"]
            + metric_scores["profit"]
            * self.weights["profit"]
            + metric_scores["conversion"]
            * self.weights["conversion"]
            + metric_scores["inventory_health"]
            * self.weights["inventory_health"]
            + metric_scores["customer_satisfaction"]
            * self.weights["customer_satisfaction"]
        )

        return round(
            self._clamp(reward),
            4
        )

    @staticmethod
    def _percentage_change(
        old_value: float,
        new_value: float
    ) -> float:
        """
        Calculate percentage change safely.
        """

        if old_value == 0:
            if new_value == 0:
                return 0.0

            return 100.0 if new_value > 0 else -100.0

        change = (
            (new_value - old_value)
            / abs(old_value)
        ) * 100

        return round(change, 4)

    @staticmethod
    def _normalize_percentage(
        percentage: float,
        maximum_expected_change: float = 20.0
    ) -> float:
        """
        Convert a percentage change into a normalized
        score between -1.0 and 1.0.

        A change of +20% or greater becomes +1.0.
        A change of -20% or lower becomes -1.0.
        """

        normalized = (
            percentage
            / maximum_expected_change
        )

        return OutcomeEvaluator._clamp(
            normalized
        )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = -1.0,
        maximum: float = 1.0
    ) -> float:
        """
        Restrict a value to the given range.
        """

        return max(
            minimum,
            min(value, maximum)
        )

    @staticmethod
    def _classify_outcome(
        reward: float
    ) -> str:
        """
        Classify the final business outcome.
        """

        if reward >= 0.20:
            return "SUCCESS"

        if reward <= -0.20:
            return "FAILURE"

        return "NEUTRAL"

    def _validate_weights(self) -> None:
        """
        Validate evaluator weight configuration.
        """

        required_keys = set(
            self.DEFAULT_WEIGHTS.keys()
        )

        received_keys = set(
            self.weights.keys()
        )

        if received_keys != required_keys:
            missing = required_keys - received_keys
            extra = received_keys - required_keys

            raise ValueError(
                "Invalid evaluator weights. "
                f"Missing: {missing}, Extra: {extra}"
            )

        for name, value in self.weights.items():
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Weight '{name}' must be numeric."
                )

            if value < 0:
                raise ValueError(
                    f"Weight '{name}' cannot be negative."
                )

        total_weight = sum(
            self.weights.values()
        )

        if abs(total_weight - 1.0) > 0.0001:
            raise ValueError(
                "Outcome evaluator weights must sum to 1.0. "
                f"Current total: {total_weight}"
            )

    @staticmethod
    def _validate_metrics(
        metrics: Dict[str, float],
        argument_name: str
    ) -> None:
        """
        Validate business metric dictionaries.
        """

        if not isinstance(metrics, dict):
            raise TypeError(
                f"{argument_name} must be a dictionary."
            )

        required_metrics = {
            "revenue",
            "profit",
            "conversion_rate",
            "inventory_health",
            "customer_satisfaction"
        }

        missing_metrics = (
            required_metrics
            - set(metrics.keys())
        )

        if missing_metrics:
            raise ValueError(
                f"{argument_name} is missing metrics: "
                f"{sorted(missing_metrics)}"
            )

        for metric_name in required_metrics:
            metric_value = metrics[metric_name]

            if not isinstance(
                metric_value,
                (int, float)
            ):
                raise TypeError(
                    f"Metric '{metric_name}' must be numeric."
                )