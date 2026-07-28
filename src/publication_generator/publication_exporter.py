from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class PublicationExportResult:
    publication_id: str
    export_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    output_directory: str = ""
    markdown_path: str = ""
    latex_path: str = ""
    manifest_path: str = ""
    data_path: str = ""
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
            and bool(self.markdown_path)
            and bool(self.latex_path)
            and bool(self.manifest_path)
            and bool(self.data_path)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "export_id": self.export_id,
            "publication_id": self.publication_id,
            "successful": self.successful,
            "output_directory": (
                self.output_directory
            ),
            "markdown_path": self.markdown_path,
            "latex_path": self.latex_path,
            "manifest_path": self.manifest_path,
            "data_path": self.data_path,
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }


class PublicationExporter:
    def export(
        self,
        publication: Any,
        output_directory: str | Path,
    ) -> PublicationExportResult:
        publication_id = str(
            getattr(
                publication,
                "publication_id",
                "",
            )
        )

        result = PublicationExportResult(
            publication_id=publication_id
        )

        if publication is None:
            result.errors.append(
                "Publication result is missing."
            )
            return result

        if not bool(
            getattr(
                publication,
                "successful",
                False,
            )
        ):
            result.errors.append(
                "Only successful publication results "
                "can be exported."
            )
            return result

        try:
            directory = Path(output_directory)
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            markdown_path = (
                directory
                / "acos_publication_manuscript.md"
            )
            latex_path = (
                directory
                / "acos_publication_manuscript.tex"
            )
            manifest_path = (
                directory
                / "publication_manifest.json"
            )
            data_path = (
                directory
                / "publication_data.json"
            )

            markdown_path.write_text(
                publication.markdown_content,
                encoding="utf-8",
            )

            latex_path.write_text(
                publication.latex_content,
                encoding="utf-8",
            )

            manifest = publication.to_dict()

            manifest_path.write_text(
                json.dumps(
                    manifest,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )

            data_path.write_text(
                json.dumps(
                    publication.publication_data,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )

            result.output_directory = str(
                directory.resolve()
            )
            result.markdown_path = str(
                markdown_path.resolve()
            )
            result.latex_path = str(
                latex_path.resolve()
            )
            result.manifest_path = str(
                manifest_path.resolve()
            )
            result.data_path = str(
                data_path.resolve()
            )

        except Exception as error:
            result.errors.append(
                f"{type(error).__name__}: {error}"
            )

        return result
