from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class ReportGenerationResult:
    """
    In-memory result produced by the research
    report generator.
    """

    bundle_id: str
    experiment_id: str
    report_title: str

    markdown_content: str = ""

    section_titles: List[str] = field(
        default_factory=list
    )

    report_data: Dict[str, Any] = field(
        default_factory=dict
    )

    warnings: List[str] = field(
        default_factory=list
    )

    errors: List[str] = field(
        default_factory=list
    )

    report_id: str = field(
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
            bool(self.markdown_content)
            and not self.errors
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "bundle_id": self.bundle_id,
            "experiment_id": self.experiment_id,
            "report_title": self.report_title,
            "successful": self.successful,
            "section_count": len(
                self.section_titles
            ),
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "created_at": self.created_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "section_titles": list(
                self.section_titles
            ),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "report_data": self.report_data,
            "markdown_content": (
                self.markdown_content
            ),
        }