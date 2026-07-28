from __future__ import annotations

from collections import deque

from .experiment_request import ExperimentRequest


class ExperimentScheduler:
    def __init__(self) -> None:
        self._queue: deque[
            ExperimentRequest
        ] = deque()

    def submit(
        self,
        request: ExperimentRequest,
    ) -> str:
        self._queue.append(request)
        return request.experiment_id

    def next(
        self,
    ) -> ExperimentRequest | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def remove(
        self,
        experiment_id: str,
    ) -> bool:
        for request in list(self._queue):
            if (
                request.experiment_id
                == experiment_id
            ):
                self._queue.remove(request)
                return True
        return False

    def find(
        self,
        experiment_id: str,
    ) -> ExperimentRequest | None:
        for request in self._queue:
            if (
                request.experiment_id
                == experiment_id
            ):
                return request
        return None

    def all(
        self,
    ) -> list[ExperimentRequest]:
        return list(self._queue)

    def __len__(self) -> int:
        return len(self._queue)
