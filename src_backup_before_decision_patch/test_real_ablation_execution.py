from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from ablation_execution import (
    AblationExecutor,
    get_active_feature_flags,
)


@dataclass
class MockExperimentRequest:
    experiment_id: str
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MockExecutionResult:
    experiment_id: str
    successful: bool
    reward: float
    duration_seconds: float
    conflict_detected: bool
    negotiation_required: bool
    metadata: Dict[str, Any]
    warnings: list[str] = field(
        default_factory=list
    )
    errors: list[str] = field(
        default_factory=list
    )


def mock_real_acos_execution(
    request: MockExperimentRequest,
    run_index: int,
    random_seed: int | None,
) -> MockExecutionResult:
    flags = get_active_feature_flags()

    reward = 0.82

    if not flags.enable_conflict_detection:
        reward -= 0.08

    if not flags.enable_negotiation:
        reward -= 0.12

    if not flags.enable_mocra:
        reward -= 0.10

    if not flags.enable_adaptive_learning:
        reward -= 0.05

    if not flags.enable_outcome_evaluation:
        reward -= 0.03

    return MockExecutionResult(
        experiment_id=(
            f"{request.experiment_id}-"
            f"{request.metadata['ablation_variant']}-"
            f"{run_index}"
        ),
        successful=True,
        reward=round(reward, 4),
        duration_seconds=0.01,
        conflict_detected=(
            flags.enable_conflict_detection
        ),
        negotiation_required=(
            flags.enable_negotiation
            and flags.enable_conflict_detection
        ),
        metadata=dict(request.metadata),
    )


def test_registry_and_context_isolation() -> None:
    executor = AblationExecutor(
        execute=mock_real_acos_execution
    )

    base_request = MockExperimentRequest(
        experiment_id="ABLATION"
    )

    batch = executor.execute_batch(
        base_request=base_request,
        variant_names=[
            "baseline",
            "without_conflict_detection",
            "without_negotiation",
            "without_mocra",
            "without_adaptive_learning",
            "without_outcome_evaluation",
        ],
        repetitions=2,
        base_seed=100,
    )

    assert batch.successful
    assert len(batch.runs) == 12

    grouped = {}

    for run in batch.runs:
        grouped.setdefault(
            run.variant_name,
            [],
        ).append(run)

        assert run.successful
        assert (
            run.metadata["ablation_variant"]
            == run.variant_name
        )

    baseline_reward = grouped[
        "baseline"
    ][0].reward

    assert baseline_reward == 0.82

    assert (
        grouped["without_negotiation"][0].reward
        < baseline_reward
    )

    assert (
        grouped["without_mocra"][0].reward
        < baseline_reward
    )

    assert not grouped[
        "without_conflict_detection"
    ][0].conflict_detected

    assert not grouped[
        "without_negotiation"
    ][0].negotiation_required

    restored_flags = get_active_feature_flags()

    assert restored_flags.enable_negotiation
    assert restored_flags.enable_mocra


def print_result() -> None:
    executor = AblationExecutor(
        execute=mock_real_acos_execution
    )

    batch = executor.execute_batch(
        base_request=MockExperimentRequest(
            experiment_id="ABLATION"
        ),
        variant_names=[
            "baseline",
            "without_negotiation",
            "without_mocra",
        ],
        repetitions=2,
        base_seed=200,
    )

    print()
    print("REAL ABLATION EXECUTION RESULT")
    print("-" * 90)
    print(
        f"batch_id               : "
        f"{batch.batch_id}"
    )
    print(
        f"successful             : "
        f"{batch.successful}"
    )
    print(
        f"total_runs             : "
        f"{len(batch.runs)}"
    )
    print(
        f"successful_runs        : "
        f"{batch.successful_runs}"
    )
    print(
        f"failed_runs            : "
        f"{batch.failed_runs}"
    )

    for run in batch.runs:
        print(
            f"{run.variant_name:<28} "
            f"run={run.repetition_index} "
            f"seed={run.random_seed} "
            f"reward={run.reward} "
            f"conflict={run.conflict_detected} "
            f"negotiation={run.negotiation_required}"
        )


def run_tests() -> None:
    test_registry_and_context_isolation()
    print_result()

    print()
    print(
        "Real Ablation Execution Framework "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
