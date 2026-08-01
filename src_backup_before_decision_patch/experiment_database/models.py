from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class ExperimentRecord:
    experiment_id: str
    name: str
    status: str
    description: str = ""
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class RunRecord:
    run_id: str
    experiment_id: str
    variant_name: str
    repetition_index: int
    random_seed: int | None
    status: str
    successful: bool
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
    created_at: str = ""


@dataclass(slots=True)
class ArtifactRecord:
    artifact_id: str
    experiment_id: str
    artifact_type: str
    path: str
    run_id: str | None = None
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    created_at: str = ""


@dataclass(slots=True)
class ReportRecord:
    report_id: str
    experiment_id: str
    run_id: str | None = None
    markdown_path: str | None = None
    html_path: str | None = None
    manifest_path: str | None = None
    data_path: str | None = None
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    created_at: str = ""


@dataclass(slots=True)
class PublicationRecord:
    publication_id: str
    experiment_id: str
    run_id: str | None = None
    markdown_path: str | None = None
    latex_path: str | None = None
    manifest_path: str | None = None
    data_path: str | None = None
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    created_at: str = ""


@dataclass(slots=True)
class AggregatedEvaluationRecord:
    evaluation_id: str
    experiment_id: str
    metrics: Dict[str, Any]
    groups: Dict[str, Any] = field(
        default_factory=dict
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    created_at: str = ""


@dataclass(slots=True)
class AblationResultRecord:
    ablation_id: str
    experiment_id: str
    baseline_group: str
    primary_metric: str
    best_group: str | None = None
    worst_group: str | None = None
    ranking: List[str] = field(
        default_factory=list
    )
    comparisons: List[Dict[str, Any]] = field(
        default_factory=list
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    created_at: str = ""
