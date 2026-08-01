from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass(slots=True)
class AblationRunResult:
    variant_name: str
    repetition_index: int
    random_seed: int | None
    successful: bool
    execution_result: Any = None
    experiment_id: str = ""
    reward: float | None = None
    duration_seconds: float | None = None
    conflict_detected: bool = False
    negotiation_required: bool = False
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    run_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "variant_name": self.variant_name,
            "repetition_index": self.repetition_index,
            "random_seed": self.random_seed,
            "successful": self.successful,
            "experiment_id": self.experiment_id,
            "reward": self.reward,
            "duration_seconds": self.duration_seconds,
            "conflict_detected": (
                self.conflict_detected
            ),
            "negotiation_required": (
                self.negotiation_required
            ),
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class AblationBatchResult:
    runs: List[AblationRunResult] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    batch_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def successful(self) -> bool:
        return (
            not self.errors
            and all(run.successful for run in self.runs)
        )

    @property
    def successful_runs(self) -> int:
        return sum(
            1
            for run in self.runs
            if run.successful
        )

    @property
    def failed_runs(self) -> int:
        return len(self.runs) - self.successful_runs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "successful": self.successful,
            "total_runs": len(self.runs),
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "runs": [
                run.to_dict()
                for run in self.runs
            ],
            "errors": list(self.errors),
            "created_at": self.created_at,
        }
