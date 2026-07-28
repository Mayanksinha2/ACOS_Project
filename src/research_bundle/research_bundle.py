from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from research_bundle.bundle_metadata import (
    BundleMetadata,
)


@dataclass
class ResearchBundle:
    """
    Unified ACOS research artifact.

    This object contains the outputs required by
    reporting, publication, patent, dashboard,
    and reproducibility modules.
    """

    metadata: BundleMetadata

    experiment: Any
    benchmark_result: Any
    statistical_result: Any
    visualization_result: Any

    analytics_result: Optional[Any] = None
    explainability_result: Optional[Any] = None

    def validate(self):
        """
        Validate this bundle using BundleValidator.

        Imported locally to avoid circular imports.
        """

        from research_bundle.bundle_validator import (
            BundleValidator,
        )

        return BundleValidator().validate(self)

    def summary(self) -> Dict[str, Any]:
        validation = self.validate()

        return {
            "bundle_id": self.metadata.bundle_id,
            "project_name": (
                self.metadata.project_name
            ),
            "project_version": (
                self.metadata.project_version
            ),
            "experiment_id": (
                self.metadata.experiment_id
            ),
            "experiment_name": (
                self.metadata.experiment_name
            ),
            "created_at": self.metadata.created_at,
            "valid": validation.valid,
            "error_count": (
                validation.error_count
            ),
            "warning_count": (
                validation.warning_count
            ),
            "has_analytics": (
                self.analytics_result is not None
            ),
            "has_explainability": (
                self.explainability_result
                is not None
            ),
        }

    def to_dict(
        self,
        include_full_results: bool = True,
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "metadata": self.metadata.to_dict(),
            "summary": self.summary(),
        }

        if include_full_results:
            result.update(
                {
                    "experiment": (
                        self._serialize_value(
                            self.experiment
                        )
                    ),
                    "benchmark_result": (
                        self._serialize_value(
                            self.benchmark_result
                        )
                    ),
                    "statistical_result": (
                        self._serialize_value(
                            self.statistical_result
                        )
                    ),
                    "visualization_result": (
                        self._serialize_value(
                            self.visualization_result
                        )
                    ),
                    "analytics_result": (
                        self._serialize_value(
                            self.analytics_result
                        )
                    ),
                    "explainability_result": (
                        self._serialize_value(
                            self.explainability_result
                        )
                    ),
                }
            )

        return result

    @staticmethod
    def _serialize_value(
        value: Any,
    ) -> Any:
        if value is None:
            return None

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

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
                list,
                tuple,
                dict,
            ),
        ):
            return value

        return {
            "object_type": (
                type(value).__name__
            ),
            "representation": repr(value),
        }