from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict

from aggregated_evaluation import (
    AblationConfig,
    AblationEvaluator,
    AggregatedEvaluationConfig,
    AggregatedEvaluator,
    EvaluationExporter,
)


@dataclass
class MockExperimentResult:
    experiment_id: str
    successful: bool
    reward: float | None
    duration_seconds: float
    conflict_detected: bool
    negotiation_required: bool
    status: str = "success"
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


def print_mapping(
    title: str,
    values: Dict[str, Any],
) -> None:
    print()
    print(title)
    print("-" * 90)

    for key, value in values.items():
        if key in {
            "metrics",
            "groups",
            "comparisons",
        }:
            continue

        print(f"{key:<32}: {value}")


def build_results() -> list[MockExperimentResult]:
    return [
        MockExperimentResult(
            experiment_id="BASE-001",
            successful=True,
            reward=0.82,
            duration_seconds=0.12,
            conflict_detected=True,
            negotiation_required=True,
            metadata={
                "ablation_variant": "baseline"
            },
        ),
        MockExperimentResult(
            experiment_id="BASE-002",
            successful=True,
            reward=0.80,
            duration_seconds=0.11,
            conflict_detected=True,
            negotiation_required=True,
            metadata={
                "ablation_variant": "baseline"
            },
        ),
        MockExperimentResult(
            experiment_id="NO-NEG-001",
            successful=True,
            reward=0.71,
            duration_seconds=0.08,
            conflict_detected=True,
            negotiation_required=False,
            metadata={
                "ablation_variant": (
                    "without_negotiation"
                )
            },
        ),
        MockExperimentResult(
            experiment_id="NO-NEG-002",
            successful=True,
            reward=0.69,
            duration_seconds=0.07,
            conflict_detected=True,
            negotiation_required=False,
            metadata={
                "ablation_variant": (
                    "without_negotiation"
                )
            },
        ),
        MockExperimentResult(
            experiment_id="NO-MOCRA-001",
            successful=True,
            reward=0.75,
            duration_seconds=0.09,
            conflict_detected=True,
            negotiation_required=True,
            metadata={
                "ablation_variant": (
                    "without_mocra"
                )
            },
        ),
        MockExperimentResult(
            experiment_id="NO-MOCRA-002",
            successful=False,
            reward=None,
            duration_seconds=0.06,
            conflict_detected=False,
            negotiation_required=False,
            status="failed",
            metadata={
                "ablation_variant": (
                    "without_mocra"
                )
            },
        ),
    ]


def test_aggregated_evaluation() -> None:
    evaluator = AggregatedEvaluator(
        AggregatedEvaluationConfig(
            confidence_level=0.95,
            include_failed_rewards=True,
            reward_failure_value=0.0,
            group_by_metadata_key=(
                "ablation_variant"
            ),
            minimum_group_size=1,
        )
    )

    result = evaluator.evaluate(
        build_results()
    )

    print_mapping(
        "AGGREGATED EVALUATION RESULT",
        result.to_dict(),
    )

    assert result.successful
    assert result.total_experiments == 6
    assert result.successful_count == 5
    assert result.failed_count == 1
    assert len(result.groups) == 3
    assert "baseline" in result.groups
    assert "without_negotiation" in result.groups
    assert "without_mocra" in result.groups

    reward_metric = result.metrics["reward"]

    assert reward_metric.count == 6
    assert reward_metric.mean is not None
    assert (
        reward_metric.confidence_interval_low
        is not None
    )
    assert (
        reward_metric.confidence_interval_high
        is not None
    )


def test_ablation_evaluation() -> None:
    aggregated = AggregatedEvaluator(
        AggregatedEvaluationConfig(
            include_failed_rewards=True,
            reward_failure_value=0.0,
        )
    ).evaluate(
        build_results()
    )

    result = AblationEvaluator(
        AblationConfig(
            baseline_group="baseline",
            primary_metric="reward",
            higher_is_better=True,
            minimum_group_size=1,
        )
    ).evaluate(
        aggregated
    )

    print_mapping(
        "ABLATION EVALUATION RESULT",
        result.to_dict(),
    )

    assert result.successful
    assert result.baseline_group == "baseline"
    assert result.best_group == "baseline"
    assert result.worst_group == "without_mocra"
    assert result.comparisons
    assert result.ranking[0] == "baseline"

    negotiation_comparison = next(
        item
        for item in result.comparisons
        if (
            item.variant_group
            == "without_negotiation"
            and item.metric_name == "reward"
        )
    )

    assert negotiation_comparison.absolute_change < 0
    assert (
        negotiation_comparison.interpretation
        == "variant_degraded"
    )


def test_evaluation_export() -> None:
    aggregated = AggregatedEvaluator(
        AggregatedEvaluationConfig(
            include_failed_rewards=True,
            reward_failure_value=0.0,
        )
    ).evaluate(
        build_results()
    )

    ablation = AblationEvaluator(
        AblationConfig(
            baseline_group="baseline",
            primary_metric="reward",
        )
    ).evaluate(
        aggregated
    )

    with TemporaryDirectory() as temporary:
        output_directory = (
            Path(temporary)
            / "evaluation_exports"
        )

        export_result = EvaluationExporter().export(
            aggregated_result=aggregated,
            ablation_result=ablation,
            output_directory=output_directory,
        )

        print_mapping(
            "EVALUATION EXPORT RESULT",
            export_result.to_dict(),
        )

        assert export_result.successful
        assert Path(
            export_result.aggregated_path
        ).exists()
        assert Path(
            export_result.ablation_path
        ).exists()
        assert Path(
            export_result.manifest_path
        ).exists()
        assert not export_result.errors


def run_tests() -> None:
    test_aggregated_evaluation()
    test_ablation_evaluation()
    test_evaluation_export()

    print()
    print(
        "Aggregated Evaluation and Ablation "
        "Framework tests passed."
    )


if __name__ == "__main__":
    run_tests()
