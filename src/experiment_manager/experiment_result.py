from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .experiment_status import ExperimentStatus


@dataclass(slots=True)
class ExperimentResult:
    experiment_id: str
    experiment_name: str
    status: ExperimentStatus
    successful: bool = False
    reward: float | None = None
    decision: Any = None
    conflict_detected: bool = False
    negotiation_required: bool = False
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    bundle_path: str = ""
    report_path: str = ""
    publication_path: str = ""
    output_directory: str = ""
    run_index: int = 1
    random_seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_result: Any = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["decision"] = repr(self.decision)
        data["raw_result"] = repr(self.raw_result)
        data["warning_count"] = len(self.warnings)
        data["error_count"] = len(self.errors)
        return data
