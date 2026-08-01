from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .models import ExperimentRecord, RunRecord


@dataclass(slots=True)
class ExperimentSearchCriteria:
    experiment_id: str | None = None
    name_contains: str | None = None
    status: str | None = None
    created_from: str | None = None
    created_to: str | None = None
    metadata_contains: Dict[str, Any] = field(
        default_factory=dict
    )
    limit: int | None = None
    offset: int = 0
    direction: str = "DESC"


@dataclass(slots=True)
class RunSearchCriteria:
    run_id: str | None = None
    experiment_id: str | None = None
    variant_name: str | None = None
    status: str | None = None
    successful: bool | None = None
    conflict_detected: bool | None = None
    negotiation_required: bool | None = None
    min_reward: float | None = None
    max_reward: float | None = None
    created_from: str | None = None
    created_to: str | None = None
    metadata_contains: Dict[str, Any] = field(
        default_factory=dict
    )
    limit: int | None = None
    offset: int = 0
    direction: str = "DESC"


@dataclass(slots=True)
class ExperimentSearchResult:
    items: List[ExperimentRecord]
    total_count: int
    limit: int | None
    offset: int


@dataclass(slots=True)
class RunSearchResult:
    items: List[RunRecord]
    total_count: int
    limit: int | None
    offset: int
