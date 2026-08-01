from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from .experiment_request import ExperimentRequest
from .experiment_result import ExperimentResult
from .experiment_status import ExperimentStatus
from .utils import first_non_empty, get_value


RunCallable = Callable[
    [ExperimentRequest, int, int | None],
    Any,
]


class ExperimentRunner:
    """
    Executes one ExperimentRequest.

    The runner is intentionally framework-agnostic. Pass an
    execution callable that invokes your existing ACOS pipeline.

    Callable signature:
        execute(request, run_index, random_seed) -> Any
    """

    def __init__(
        self,
        execute: RunCallable,
    ) -> None:
        if not callable(execute):
            raise TypeError(
                "execute must be callable."
            )

        self._execute = execute

    def run(
        self,
        request: ExperimentRequest,
        run_index: int = 1,
        random_seed: int | None = None,
    ) -> ExperimentResult:
        if request.cancelled:
            request.status = (
                ExperimentStatus.CANCELLED
            )

            return ExperimentResult(
                experiment_id=request.experiment_id,
                experiment_name=(
                    request.config.experiment_name
                ),
                status=ExperimentStatus.CANCELLED,
                successful=False,
                run_index=run_index,
                random_seed=random_seed,
                metadata=dict(request.metadata),
                errors=[
                    "Experiment was cancelled before "
                    "execution."
                ],
            )

        started = datetime.now(timezone.utc)
        timer = perf_counter()
        request.status = ExperimentStatus.RUNNING

        if random_seed is not None:
            random.seed(random_seed)

        try:
            raw_result = self._execute(
                request,
                run_index,
                random_seed,
            )

            successful = bool(
                first_non_empty(
                    get_value(
                        raw_result,
                        "successful",
                        None,
                    ),
                    get_value(
                        raw_result,
                        "success",
                        None,
                    ),
                    True,
                )
            )

            errors = list(
                get_value(
                    raw_result,
                    "errors",
                    [],
                )
                or []
            )

            warnings = list(
                get_value(
                    raw_result,
                    "warnings",
                    [],
                )
                or []
            )

            if errors:
                successful = False

            status = (
                ExperimentStatus.SUCCESS
                if successful
                else ExperimentStatus.FAILED
            )

            request.status = status

            output_directory = str(
                first_non_empty(
                    get_value(
                        raw_result,
                        "output_directory",
                        None,
                    ),
                    request.output_directory,
                    "",
                )
            )

            result = ExperimentResult(
                experiment_id=(
                    request.experiment_id
                ),
                experiment_name=(
                    request.config.experiment_name
                ),
                status=status,
                successful=successful,
                reward=_optional_float(
                    first_non_empty(
                        get_value(
                            raw_result,
                            "reward",
                            None,
                        ),
                        get_value(
                            raw_result,
                            "final_reward",
                            None,
                        ),
                        get_value(
                            get_value(
                                raw_result,
                                "outcome",
                                None,
                            ),
                            "reward",
                            None,
                        ),
                    )
                ),
                decision=first_non_empty(
                    get_value(
                        raw_result,
                        "decision",
                        None,
                    ),
                    get_value(
                        raw_result,
                        "final_decision",
                        None,
                    ),
                ),
                conflict_detected=bool(
                    first_non_empty(
                        get_value(
                            raw_result,
                            "conflict_detected",
                            None,
                        ),
                        get_value(
                            raw_result,
                            "has_conflict",
                            None,
                        ),
                        False,
                    )
                ),
                negotiation_required=bool(
                    first_non_empty(
                        get_value(
                            raw_result,
                            "negotiation_required",
                            None,
                        ),
                        get_value(
                            raw_result,
                            "negotiated",
                            None,
                        ),
                        False,
                    )
                ),
                bundle_path=str(
                    get_value(
                        raw_result,
                        "bundle_path",
                        "",
                    )
                    or ""
                ),
                report_path=str(
                    get_value(
                        raw_result,
                        "report_path",
                        "",
                    )
                    or ""
                ),
                publication_path=str(
                    get_value(
                        raw_result,
                        "publication_path",
                        "",
                    )
                    or ""
                ),
                output_directory=output_directory,
                run_index=run_index,
                random_seed=random_seed,
                metadata=dict(request.metadata),
                raw_result=raw_result,
                warnings=warnings,
                errors=errors,
            )

        except Exception as error:
            request.status = ExperimentStatus.FAILED

            result = ExperimentResult(
                experiment_id=(
                    request.experiment_id
                ),
                experiment_name=(
                    request.config.experiment_name
                ),
                status=ExperimentStatus.FAILED,
                successful=False,
                output_directory=str(
                    request.output_directory or ""
                ),
                run_index=run_index,
                random_seed=random_seed,
                metadata=dict(request.metadata),
                errors=[
                    f"{type(error).__name__}: {error}"
                ],
            )

        finished = datetime.now(timezone.utc)

        result.started_at = started.isoformat()
        result.finished_at = finished.isoformat()
        result.duration_seconds = round(
            perf_counter() - timer,
            6,
        )

        return result


def _optional_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
