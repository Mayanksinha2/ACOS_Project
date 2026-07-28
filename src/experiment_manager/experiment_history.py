from __future__ import annotations

from .experiment_result import ExperimentResult
from .experiment_status import ExperimentStatus


class ExperimentHistory:
    def __init__(self) -> None:
        self._results: list[
            ExperimentResult
        ] = []

    def add(
        self,
        result: ExperimentResult,
    ) -> None:
        self._results.append(result)

    def all(self) -> list[ExperimentResult]:
        return list(self._results)

    def last(
        self,
    ) -> ExperimentResult | None:
        if not self._results:
            return None
        return self._results[-1]

    def successful(
        self,
    ) -> list[ExperimentResult]:
        return [
            result
            for result in self._results
            if result.status
            == ExperimentStatus.SUCCESS
        ]

    def failed(
        self,
    ) -> list[ExperimentResult]:
        return [
            result
            for result in self._results
            if result.status
            == ExperimentStatus.FAILED
        ]

    def cancelled(
        self,
    ) -> list[ExperimentResult]:
        return [
            result
            for result in self._results
            if result.status
            == ExperimentStatus.CANCELLED
        ]

    def find(
        self,
        experiment_id: str,
    ) -> list[ExperimentResult]:
        return [
            result
            for result in self._results
            if result.experiment_id
            == experiment_id
        ]

    def clear(self) -> None:
        self._results.clear()

    def __len__(self) -> int:
        return len(self._results)
