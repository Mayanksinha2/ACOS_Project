from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from report_generator.report_result import (
    ReportGenerationResult,
)


@dataclass
class ReportExportResult:
    """
    Result of exporting a generated research report.
    """

    report_id: str
    output_directory: str

    markdown_path: str | None = None
    manifest_path: str | None = None
    data_path: str | None = None

    errors: List[str] = field(
        default_factory=list
    )

    export_id: str = field(
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
            and self.markdown_path is not None
            and self.manifest_path is not None
            and self.data_path is not None
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "export_id": self.export_id,
            "report_id": self.report_id,
            "successful": self.successful,
            "output_directory": (
                self.output_directory
            ),
            "markdown_path": self.markdown_path,
            "manifest_path": self.manifest_path,
            "data_path": self.data_path,
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }


class ReportExporter:
    """
    Export a generated report into Markdown and JSON
    research artifacts.
    """

    def export(
        self,
        report_result: ReportGenerationResult,
        output_directory: str | Path,
        report_name: str = "acos_research_report",
    ) -> ReportExportResult:
        output_path = Path(
            output_directory
        ).expanduser().resolve()

        result = ReportExportResult(
            report_id=report_result.report_id,
            output_directory=str(output_path),
        )

        try:
            if not report_result.successful:
                raise ValueError(
                    "Cannot export an unsuccessful "
                    "report generation result."
                )

            output_path.mkdir(
                parents=True,
                exist_ok=True,
            )

            safe_name = self._safe_filename(
                report_name
            )

            markdown_path = (
                output_path
                / f"{safe_name}.md"
            )

            manifest_path = (
                output_path
                / "report_manifest.json"
            )

            data_path = (
                output_path
                / "report_data.json"
            )

            markdown_path.write_text(
                report_result.markdown_content,
                encoding="utf-8",
            )

            self._write_json(
                manifest_path,
                report_result.summary(),
            )

            self._write_json(
                data_path,
                report_result.report_data,
            )

            result.markdown_path = str(
                markdown_path
            )

            result.manifest_path = str(
                manifest_path
            )

            result.data_path = str(
                data_path
            )

        except Exception as error:
            result.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return result

    @staticmethod
    def _write_json(
        path: Path,
        value: Dict[str, Any],
    ) -> None:
        path.write_text(
            json.dumps(
                value,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _safe_filename(
        value: str,
    ) -> str:
        cleaned = "".join(
            character
            if (
                character.isalnum()
                or character in {"-", "_"}
            )
            else "_"
            for character in value.strip()
        )

        return (
            cleaned
            or "acos_research_report"
        )