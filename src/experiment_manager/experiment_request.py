from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .experiment_config import ExperimentConfig
from .experiment_status import ExperimentStatus


@dataclass(slots=True)
class ExperimentRequest:
    config: ExperimentConfig
    payload: Any = None
    output_directory: str | Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    experiment_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    status: ExperimentStatus = ExperimentStatus.PENDING
    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )
    cancelled: bool = False

    def __post_init__(self) -> None:
        if self.output_directory is not None:
            self.output_directory = str(
                Path(self.output_directory)
            )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["payload"] = repr(self.payload)
        return data
