from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .experiment_result import ExperimentResult
from .experiment_summary import ExperimentSummary
from .utils import json_safe


@dataclass(slots=True)
class ExperimentExportResult:
    export_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    successful: bool = False
    output_directory: str = ""
    history_path: str = ""
    summary_path: str = ""
    error_count: int = 0
    errors: list[str] = field(
        default_factory=list
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["error_count"] = len(self.errors)
        return data


class ExperimentExporter:
    def export(
        self,
        results: list[ExperimentResult],
        summary: ExperimentSummary,
        output_directory: str | Path,
    ) -> ExperimentExportResult:
        output = Path(output_directory)
        export_result = ExperimentExportResult(
            output_directory=str(output)
        )

        try:
            output.mkdir(
                parents=True,
                exist_ok=True,
            )

            history_path = (
                output
                / "experiment_history.json"
            )

            summary_path = (
                output
                / "experiment_summary.json"
            )

            history_payload = {
                "exported_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "result_count": len(results),
                "results": [
                    json_safe(result)
                    for result in results
                ],
            }

            summary_payload = json_safe(
                summary
            )

            history_path.write_text(
                json.dumps(
                    history_payload,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            summary_path.write_text(
                json.dumps(
                    summary_payload,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            export_result.history_path = str(
                history_path
            )
            export_result.summary_path = str(
                summary_path
            )
            export_result.successful = True

        except Exception as error:
            export_result.errors.append(
                f"{type(error).__name__}: {error}"
            )

        export_result.error_count = len(
            export_result.errors
        )

        return export_result
