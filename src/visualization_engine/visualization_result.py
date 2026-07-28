from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class GeneratedChart:
    """
    Metadata for one generated visualization.
    """

    chart_name: str
    chart_type: str
    metric_name: Optional[str]
    file_path: str

    title: str = ""
    successful: bool = True
    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    chart_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def exists(self) -> bool:
        return Path(self.file_path).exists()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "chart_name": self.chart_name,
            "chart_type": self.chart_type,
            "metric_name": self.metric_name,
            "file_path": self.file_path,
            "title": self.title,
            "successful": self.successful,
            "error": self.error,
            "file_exists": self.exists(),
            "metadata": dict(self.metadata),
        }


@dataclass
class VisualizationResult:
    """
    Complete visualization output for one
    ACOS benchmark experiment.
    """

    experiment_id: str
    experiment_name: str
    output_directory: str

    charts: List[GeneratedChart] = field(
        default_factory=list
    )

    successful: bool = True
    errors: List[str] = field(
        default_factory=list
    )

    visualization_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def generated_chart_count(self) -> int:
        return sum(
            1
            for chart in self.charts
            if chart.successful
        )

    @property
    def failed_chart_count(self) -> int:
        return sum(
            1
            for chart in self.charts
            if not chart.successful
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "visualization_id": (
                self.visualization_id
            ),
            "experiment_id": self.experiment_id,
            "experiment_name": (
                self.experiment_name
            ),
            "output_directory": (
                self.output_directory
            ),
            "successful": self.successful,
            "generated_chart_count": (
                self.generated_chart_count
            ),
            "failed_chart_count": (
                self.failed_chart_count
            ),
            "created_at": self.created_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "charts": [
                chart.to_dict()
                for chart in self.charts
            ],
            "errors": list(self.errors),
        }