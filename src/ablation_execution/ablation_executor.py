from __future__ import annotations

import inspect
from time import perf_counter
from typing import Any, Callable, Iterable, List

from .ablation_request import AblationRunRequest
from .ablation_result import (
    AblationBatchResult,
    AblationRunResult,
)
from .request_adapter import (
    clone_request_with_metadata,
)
from .result_adapter import (
    extract_conflict_detected,
    extract_duration,
    extract_experiment_id,
    extract_negotiation_required,
    extract_reward,
    extract_successful,
    normalize_messages,
)
from .utils import get_value
from .variant_registry import (
    AblationVariantRegistry,
)
from .feature_flags import use_feature_flags


ExecutionCallable = Callable[..., Any]


class AblationExecutor:
    """
    Execute real ACOS variants through one existing execution
    adapter, such as execute_acos_experiment().
    """

    def __init__(
        self,
        execute: ExecutionCallable,
        registry: (
            AblationVariantRegistry | None
        ) = None,
    ) -> None:
        self.execute = execute
        self.registry = (
            registry
            or AblationVariantRegistry()
        )

    def execute_variant(
        self,
        request: AblationRunRequest,
    ) -> AblationRunResult:
        variant = self.registry.get(
            request.variant_name
        )

        metadata = {
            **variant.to_metadata(),
            **dict(request.metadata),
            "ablation_repetition": (
                request.repetition_index
            ),
            "ablation_seed": request.random_seed,
        }

        execution_request = (
            clone_request_with_metadata(
                request.base_request,
                metadata,
            )
        )

        started = perf_counter()

        try:
            with use_feature_flags(
                variant.feature_flags
            ):
                execution_result = (
                    self._invoke_execution(
                        request=execution_request,
                        repetition_index=(
                            request.repetition_index
                        ),
                        random_seed=(
                            request.random_seed
                        ),
                    )
                )

            elapsed = perf_counter() - started

            warnings = normalize_messages(
                get_value(
                    execution_result,
                    "warnings",
                    [],
                )
            )

            errors = normalize_messages(
                get_value(
                    execution_result,
                    "errors",
                    [],
                )
            )

            successful = (
                extract_successful(
                    execution_result
                )
                and not errors
            )

            duration = extract_duration(
                execution_result
            )

            return AblationRunResult(
                variant_name=variant.name,
                repetition_index=(
                    request.repetition_index
                ),
                random_seed=request.random_seed,
                successful=successful,
                execution_result=execution_result,
                experiment_id=extract_experiment_id(
                    execution_result
                ),
                reward=extract_reward(
                    execution_result
                ),
                duration_seconds=(
                    duration
                    if duration is not None
                    else elapsed
                ),
                conflict_detected=(
                    extract_conflict_detected(
                        execution_result
                    )
                ),
                negotiation_required=(
                    extract_negotiation_required(
                        execution_result
                    )
                ),
                metadata=metadata,
                warnings=warnings,
                errors=errors,
            )

        except Exception as error:
            elapsed = perf_counter() - started

            return AblationRunResult(
                variant_name=variant.name,
                repetition_index=(
                    request.repetition_index
                ),
                random_seed=request.random_seed,
                successful=False,
                duration_seconds=elapsed,
                metadata=metadata,
                errors=[
                    f"{type(error).__name__}: {error}"
                ],
            )

    def execute_batch(
        self,
        base_request: Any,
        variant_names: Iterable[str],
        repetitions: int,
        base_seed: int | None = None,
    ) -> AblationBatchResult:
        if repetitions < 1:
            raise ValueError(
                "repetitions must be at least 1."
            )

        batch = AblationBatchResult()

        for variant_name in variant_names:
            self.registry.get(variant_name)

            for repetition_index in range(
                1,
                repetitions + 1,
            ):
                random_seed = (
                    None
                    if base_seed is None
                    else (
                        base_seed
                        + repetition_index
                        - 1
                    )
                )

                run_request = AblationRunRequest(
                    variant_name=variant_name,
                    repetition_index=(
                        repetition_index
                    ),
                    random_seed=random_seed,
                    base_request=base_request,
                )

                batch.runs.append(
                    self.execute_variant(
                        run_request
                    )
                )

        return batch

    def _invoke_execution(
        self,
        request: Any,
        repetition_index: int,
        random_seed: int | None,
    ) -> Any:
        """
        Supports the ACOS execution adapter signature:

            execute(request, run_index, random_seed)

        It also supports simpler callables for testing.
        """

        signature = inspect.signature(
            self.execute
        )

        parameter_count = len(
            signature.parameters
        )

        if parameter_count >= 3:
            return self.execute(
                request,
                repetition_index,
                random_seed,
            )

        if parameter_count == 2:
            return self.execute(
                request,
                random_seed,
            )

        return self.execute(request)
