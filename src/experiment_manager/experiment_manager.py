from __future__ import annotations

from pathlib import Path
from typing import Any

from .experiment_config import ExperimentConfig
from .experiment_history import ExperimentHistory
from .experiment_request import ExperimentRequest
from .experiment_result import ExperimentResult
from .experiment_runner import ExperimentRunner
from .experiment_scheduler import ExperimentScheduler
from .experiment_status import ExperimentStatus
from .experiment_summary import ExperimentSummary


class ExperimentManager:
    def __init__(
        self,
        runner: ExperimentRunner,
        scheduler: ExperimentScheduler | None = None,
        history: ExperimentHistory | None = None,
    ) -> None:
        self.runner = runner
        self.scheduler = (
            scheduler or ExperimentScheduler()
        )
        self.history_store = (
            history or ExperimentHistory()
        )
        self._requests: dict[
            str,
            ExperimentRequest,
        ] = {}

    def submit(
        self,
        config: ExperimentConfig,
        payload: Any = None,
        output_directory: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        request = ExperimentRequest(
            config=config,
            payload=payload,
            output_directory=output_directory,
            metadata=metadata or {},
        )

        self._requests[
            request.experiment_id
        ] = request

        return self.scheduler.submit(request)

    def run(
        self,
        experiment_id: str,
    ) -> list[ExperimentResult]:
        request = self._requests.get(
            experiment_id
        )

        if request is None:
            raise KeyError(
                "Unknown experiment_id: "
                f"{experiment_id}"
            )

        self.scheduler.remove(experiment_id)

        if request.cancelled:
            result = self.runner.run(request)
            self.history_store.add(result)
            return [result]

        results: list[ExperimentResult] = []

        for run_index in range(
            1,
            request.config.repetitions + 1,
        ):
            if request.cancelled:
                break

            seed = _derive_seed(
                request.config.random_seed,
                run_index,
            )

            result = self.runner.run(
                request=request,
                run_index=run_index,
                random_seed=seed,
            )

            self.history_store.add(result)
            results.append(result)

            if (
                not result.successful
                and request.config.stop_on_error
            ):
                break

        return results

    def run_all(
        self,
    ) -> list[ExperimentResult]:
        all_results: list[
            ExperimentResult
        ] = []

        while len(self.scheduler):
            request = self.scheduler.next()

            if request is None:
                break

            all_results.extend(
                self.run(request.experiment_id)
            )

        return all_results

    def cancel(
        self,
        experiment_id: str,
    ) -> bool:
        request = self._requests.get(
            experiment_id
        )

        if request is None:
            return False

        if request.status in {
            ExperimentStatus.SUCCESS,
            ExperimentStatus.FAILED,
            ExperimentStatus.CANCELLED,
        }:
            return False

        request.cancelled = True
        request.status = (
            ExperimentStatus.CANCELLED
        )
        self.scheduler.remove(experiment_id)
        return True

    def history(
        self,
    ) -> list[ExperimentResult]:
        return self.history_store.all()

    def summary(self) -> ExperimentSummary:
        return ExperimentSummary.from_results(
            self.history_store.all()
        )

    def request(
        self,
        experiment_id: str,
    ) -> ExperimentRequest | None:
        return self._requests.get(
            experiment_id
        )


def _derive_seed(
    base_seed: int | None,
    run_index: int,
) -> int | None:
    if base_seed is None:
        return None

    return base_seed + run_index - 1
