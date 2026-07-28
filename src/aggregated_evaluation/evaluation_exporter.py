from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from .ablation_result import (
    AblationEvaluationResult,
)
from .aggregated_result import (
    AggregatedEvaluationResult,
)


@dataclass(slots=True)
class EvaluationExportResult:
    output_directory: str
    aggregated_path: str = ""
    ablation_path: str = ""
    manifest_path: str = ""
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
            and bool(self.aggregated_path)
            and bool(self.manifest_path)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "export_id": self.export_id,
            "successful": self.successful,
            "output_directory": self.output_directory,
            "aggregated_path": self.aggregated_path,
            "ablation_path": self.ablation_path,
            "manifest_path": self.manifest_path,
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }


class EvaluationExporter:
    def export(
        self,
        aggregated_result: AggregatedEvaluationResult,
        output_directory: str | Path,
        ablation_result: (
            AblationEvaluationResult | None
        ) = None,
    ) -> EvaluationExportResult:
        directory = Path(
            output_directory
        ).expanduser().resolve()

        result = EvaluationExportResult(
            output_directory=str(directory)
        )

        try:
            if not aggregated_result.successful:
                raise ValueError(
                    "Only successful aggregated evaluation "
                    "results can be exported."
                )

            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            aggregated_path = (
                directory
                / "aggregated_evaluation.json"
            )

            manifest_path = (
                directory
                / "evaluation_manifest.json"
            )

            self._write_json(
                aggregated_path,
                aggregated_result.to_dict(),
            )

            result.aggregated_path = str(
                aggregated_path
            )

            if ablation_result is not None:
                ablation_path = (
                    directory
                    / "ablation_evaluation.json"
                )

                self._write_json(
                    ablation_path,
                    ablation_result.to_dict(),
                )

                result.ablation_path = str(
                    ablation_path
                )

            manifest = {
                "export_id": result.export_id,
                "evaluation_id": (
                    aggregated_result.evaluation_id
                ),
                "ablation_id": (
                    ablation_result.ablation_id
                    if ablation_result is not None
                    else None
                ),
                "aggregated_path": (
                    result.aggregated_path
                ),
                "ablation_path": (
                    result.ablation_path
                ),
                "created_at": result.created_at,
            }

            self._write_json(
                manifest_path,
                manifest,
            )

            result.manifest_path = str(
                manifest_path
            )

        except Exception as error:
            result.errors.append(
                f"{type(error).__name__}: {error}"
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
