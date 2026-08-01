from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ExperimentConfig:
    experiment_name: str = "ACOS Experiment"
    repetitions: int = 1
    random_seed: int | None = 42
    parallel: bool = False
    save_bundle: bool = True
    save_report: bool = True
    save_publication: bool = False
    stop_on_error: bool = False
    tags: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.experiment_name = self.experiment_name.strip()

        if not self.experiment_name:
            raise ValueError("experiment_name cannot be empty.")

        if self.repetitions < 1:
            raise ValueError("repetitions must be at least 1.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
