from __future__ import annotations

import json
import pickle
import shutil
from pathlib import Path
from typing import Any, Dict, Optional


class BundleExporter:
    """
    Exports ACOS research bundles into
    reproducible research artifacts.
    """

    def __init__(
        self,
        output_root: str = "outputs/research_bundles",
    ) -> None:
        self.output_root = Path(output_root)

    def export(
        self,
        bundle,
        bundle_name: Optional[str] = None,
        include_pickle: bool = True,
        create_archive: bool = True,
    ) -> Dict[str, Any]:
        validation = bundle.validate()

        if not validation.valid:
            raise ValueError(
                "Cannot export an invalid "
                "research bundle: "
                + "; ".join(validation.errors)
            )

        directory_name = (
            bundle_name
            or self._default_bundle_name(bundle)
        )

        output_directory = (
            self.output_root / directory_name
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_path = (
            output_directory / "bundle.json"
        )

        validation_path = (
            output_directory
            / "validation.json"
        )

        summary_path = (
            output_directory
            / "summary.json"
        )

        self._write_json(
            json_path,
            bundle.to_dict(
                include_full_results=True
            ),
        )

        self._write_json(
            validation_path,
            validation.to_dict(),
        )

        self._write_json(
            summary_path,
            bundle.summary(),
        )

        pickle_path = None

        if include_pickle:
            pickle_path = (
                output_directory / "bundle.pkl"
            )

            with pickle_path.open("wb") as file:
                pickle.dump(
                    bundle,
                    file,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

        archive_path = None

        if create_archive:
            archive_base = (
                output_directory.parent
                / output_directory.name
            )

            archive_path_value = (
                shutil.make_archive(
                    base_name=str(archive_base),
                    format="zip",
                    root_dir=str(
                        output_directory.parent
                    ),
                    base_dir=(
                        output_directory.name
                    ),
                )
            )

            archive_path = Path(
                archive_path_value
            )

        return {
            "successful": True,
            "bundle_id": (
                bundle.metadata.bundle_id
            ),
            "output_directory": str(
                output_directory.resolve()
            ),
            "json_path": str(
                json_path.resolve()
            ),
            "summary_path": str(
                summary_path.resolve()
            ),
            "validation_path": str(
                validation_path.resolve()
            ),
            "pickle_path": (
                str(pickle_path.resolve())
                if pickle_path is not None
                else None
            ),
            "archive_path": (
                str(archive_path.resolve())
                if archive_path is not None
                else None
            ),
        }

    @staticmethod
    def load_pickle(
        file_path: str,
    ):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Bundle file not found: {path}"
            )

        with path.open("rb") as file:
            return pickle.load(file)

    @staticmethod
    def load_json(
        file_path: str,
    ) -> Dict[str, Any]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Bundle file not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    @staticmethod
    def _write_json(
        file_path: Path,
        data: Dict[str, Any],
    ) -> None:
        with file_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
                default=(
                    BundleExporter
                    ._json_default
                ),
            )

    @staticmethod
    def _json_default(value: Any):
        to_dict_method = getattr(
            value,
            "to_dict",
            None,
        )

        if callable(to_dict_method):
            return to_dict_method()

        summary_method = getattr(
            value,
            "summary",
            None,
        )

        if callable(summary_method):
            return summary_method()

        if isinstance(value, Path):
            return str(value)

        if hasattr(value, "__dict__"):
            return vars(value)

        return str(value)

    @staticmethod
    def _default_bundle_name(
        bundle,
    ) -> str:
        experiment_name = (
            bundle.metadata.experiment_name
            or "acos_experiment"
        )

        bundle_id = (
            bundle.metadata.bundle_id
        )

        safe_name = "".join(
            character
            if (
                character.isalnum()
                or character in "-_"
            )
            else "_"
            for character in experiment_name
        ).strip("_")

        return (
            f"{safe_name}_"
            f"{bundle_id}"
        )