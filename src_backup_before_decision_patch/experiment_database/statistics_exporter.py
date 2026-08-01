from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .utils import json_dumps


class StatisticsExporter:
    """
    Exports statistics dataclasses as JSON-ready
    dictionaries or JSON files.
    """

    def to_dict(
        self,
        value: Any,
    ) -> dict:
        if is_dataclass(value):
            return asdict(value)

        if isinstance(value, dict):
            return {
                str(key): (
                    asdict(item)
                    if is_dataclass(item)
                    else item
                )
                for key, item in value.items()
            }

        raise TypeError(
            "Expected a dataclass or dictionary."
        )

    def export_json(
        self,
        value: Any,
        output_path: str | Path,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json_dumps(
                self.to_dict(value)
            ),
            encoding="utf-8",
        )

        return path
