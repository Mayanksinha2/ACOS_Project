from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class PublicationGenerationResult:
    report_id: str
    bundle_id: str
    experiment_id: str
    publication_title: str
    publication_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    markdown_content: str = ""
    latex_content: str = ""
    section_titles: List[str] = field(
        default_factory=list
    )
    publication_data: Dict[str, Any] = field(
        default_factory=dict
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
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
            and bool(self.markdown_content.strip())
            and bool(self.latex_content.strip())
        )

    @property
    def section_count(self) -> int:
        return len(self.section_titles)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "publication_id": self.publication_id,
            "report_id": self.report_id,
            "bundle_id": self.bundle_id,
            "experiment_id": self.experiment_id,
            "publication_title": (
                self.publication_title
            ),
            "successful": self.successful,
            "section_count": self.section_count,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }
