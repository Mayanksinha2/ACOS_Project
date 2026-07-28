from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any, Dict, Iterable, List

from .aggregated_result import (
    AggregatedEvaluationResult,
    GroupEvaluationResult,
)
from .evaluation_config import (
    AggregatedEvaluationConfig,
)
from .metric_summary import MetricSummary
from .utils import (
    first_non_empty,
    get_value,
    safe_bool,
    safe_float,
)


class AggregatedEvaluator:
    def __init__(
        self,
        config: AggregatedEvaluationConfig | None = None,
    ) -> None:
        self.config = (
            config
            or AggregatedEvaluationConfig()
        )

    def evaluate(
        self,
        experiment_results: Iterable[Any],
    ) -> AggregatedEvaluationResult:
        results = list(experiment_results)

        aggregate = self._evaluate_group(
            group_name="all",
            results=results,
        )

        output = AggregatedEvaluationResult(
            total_experiments=aggregate.experiment_count,
            successful_count=aggregate.successful_count,
            failed_count=aggregate.failed_count,
            cancelled_count=aggregate.cancelled_count,
            success_rate=aggregate.success_rate,
            failure_rate=aggregate.failure_rate,
            conflict_count=aggregate.conflict_count,
            negotiation_count=aggregate.negotiation_count,
            conflict_rate=aggregate.conflict_rate,
            negotiation_rate=aggregate.negotiation_rate,
            metrics=aggregate.metrics,
        )

        if not results:
            output.warnings.append(
                "No experiment results were provided."
            )
            return output

        grouped_results: Dict[str, List[Any]] = (
            defaultdict(list)
        )

        for result in results:
            grouped_results[
                self._extract_group_name(result)
            ].append(result)

        for group_name, group_items in grouped_results.items():
            if (
                len(group_items)
                < self.config.minimum_group_size
            ):
                output.warnings.append(
                    f"Group '{group_name}' was skipped because "
                    f"it contains only {len(group_items)} result(s)."
                )
                continue

            output.groups[group_name] = (
                self._evaluate_group(
                    group_name=group_name,
                    results=group_items,
                )
            )

        return output

    def _evaluate_group(
        self,
        group_name: str,
        results: List[Any],
    ) -> GroupEvaluationResult:
        total = len(results)

        successful_count = sum(
            1 for result in results
            if self._is_successful(result)
        )

        cancelled_count = sum(
            1 for result in results
            if self._status_name(result) == "cancelled"
        )

        failed_count = max(
            0,
            total
            - successful_count
            - cancelled_count,
        )

        conflict_count = sum(
            1 for result in results
            if safe_bool(
                get_value(
                    result,
                    "conflict_detected",
                    False,
                )
            )
        )

        negotiation_count = sum(
            1 for result in results
            if safe_bool(
                get_value(
                    result,
                    "negotiation_required",
                    False,
                )
            )
        )

        metric_values: Dict[str, List[float]] = (
            defaultdict(list)
        )

        for result in results:
            self._collect_metrics(
                result=result,
                metric_values=metric_values,
            )

        metrics = {
            metric_name: self._summarize_metric(
                metric_name,
                values,
            )
            for metric_name, values in metric_values.items()
        }

        experiment_ids = [
            str(
                first_non_empty(
                    get_value(
                        result,
                        "experiment_id",
                        None,
                    ),
                    "",
                )
            )
            for result in results
        ]

        return GroupEvaluationResult(
            group_name=group_name,
            experiment_count=total,
            successful_count=successful_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            success_rate=self._percentage(
                successful_count,
                total,
            ),
            failure_rate=self._percentage(
                failed_count,
                total,
            ),
            conflict_count=conflict_count,
            negotiation_count=negotiation_count,
            conflict_rate=self._percentage(
                conflict_count,
                total,
            ),
            negotiation_rate=self._percentage(
                negotiation_count,
                total,
            ),
            metrics=metrics,
            experiment_ids=experiment_ids,
        )

    def _collect_metrics(
        self,
        result: Any,
        metric_values: Dict[str, List[float]],
    ) -> None:
        successful = self._is_successful(result)

        if "successful" in self.config.metric_names:
            metric_values["successful"].append(
                1.0 if successful else 0.0
            )

        if "conflict_detected" in self.config.metric_names:
            metric_values["conflict_detected"].append(
                1.0
                if safe_bool(
                    get_value(
                        result,
                        "conflict_detected",
                        False,
                    )
                )
                else 0.0
            )

        if (
            "negotiation_required"
            in self.config.metric_names
        ):
            metric_values[
                "negotiation_required"
            ].append(
                1.0
                if safe_bool(
                    get_value(
                        result,
                        "negotiation_required",
                        False,
                    )
                )
                else 0.0
            )

        if "duration_seconds" in self.config.metric_names:
            duration = safe_float(
                get_value(
                    result,
                    "duration_seconds",
                    None,
                )
            )

            if duration is not None:
                metric_values[
                    "duration_seconds"
                ].append(duration)

        if "reward" in self.config.metric_names:
            reward = safe_float(
                get_value(
                    result,
                    "reward",
                    None,
                )
            )

            if reward is not None:
                metric_values["reward"].append(
                    reward
                )

            elif (
                not successful
                and self.config.include_failed_rewards
            ):
                metric_values["reward"].append(
                    self.config.reward_failure_value
                )

    def _summarize_metric(
        self,
        name: str,
        values: List[float],
    ) -> MetricSummary:
        count = len(values)

        if count == 0:
            return MetricSummary(
                name=name,
                count=0,
                minimum=None,
                maximum=None,
                mean=None,
                median=None,
                standard_deviation=None,
                variance=None,
                confidence_interval_low=None,
                confidence_interval_high=None,
            )

        mean = statistics.fmean(values)
        median = statistics.median(values)

        if count > 1:
            standard_deviation = statistics.stdev(
                values
            )
            variance = statistics.variance(
                values
            )
            margin = (
                self._z_value(
                    self.config.confidence_level
                )
                * standard_deviation
                / math.sqrt(count)
            )
        else:
            standard_deviation = 0.0
            variance = 0.0
            margin = 0.0

        return MetricSummary(
            name=name,
            count=count,
            minimum=min(values),
            maximum=max(values),
            mean=mean,
            median=median,
            standard_deviation=standard_deviation,
            variance=variance,
            confidence_interval_low=mean - margin,
            confidence_interval_high=mean + margin,
        )

    def _extract_group_name(
        self,
        result: Any,
    ) -> str:
        metadata = get_value(
            result,
            "metadata",
            {},
        )

        value = get_value(
            metadata,
            self.config.group_by_metadata_key,
            None,
        )

        if value is None:
            value = get_value(
                result,
                self.config.group_by_metadata_key,
                None,
            )

        if value is None:
            return "default"

        return str(value)

    @staticmethod
    def _status_name(
        result: Any,
    ) -> str:
        status = get_value(
            result,
            "status",
            "",
        )

        status_value = get_value(
            status,
            "value",
            status,
        )

        return str(status_value).strip().lower()

    def _is_successful(
        self,
        result: Any,
    ) -> bool:
        explicit = get_value(
            result,
            "successful",
            None,
        )

        if explicit is not None:
            return safe_bool(explicit)

        return self._status_name(result) == "success"

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            100.0 * numerator / denominator,
            6,
        )

    @staticmethod
    def _z_value(
        confidence_level: float,
    ) -> float:
        common_values = {
            0.80: 1.281552,
            0.90: 1.644854,
            0.95: 1.959964,
            0.98: 2.326348,
            0.99: 2.575829,
        }

        rounded = round(
            confidence_level,
            2,
        )

        return common_values.get(
            rounded,
            1.959964,
        )
