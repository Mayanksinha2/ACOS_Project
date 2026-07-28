from __future__ import annotations

from typing import Any, Dict, Optional

from research_bundle.bundle_metadata import (
    BundleMetadata,
)
from research_bundle.research_bundle import (
    ResearchBundle,
)


class ResearchBundleBuilder:
    """
    Constructs internally consistent ACOS
    research bundles.
    """

    def __init__(
        self,
        project_version: str = "1.0.0",
        framework_version: str = "1.0.0",
        researcher_name: Optional[str] = None,
        institution_name: Optional[str] = None,
    ) -> None:
        self.project_version = project_version
        self.framework_version = (
            framework_version
        )
        self.researcher_name = researcher_name
        self.institution_name = (
            institution_name
        )

    def build(
        self,
        experiment: Any,
        benchmark_result: Any,
        statistical_result: Any,
        visualization_result: Any,
        analytics_result: Optional[Any] = None,
        explainability_result: Optional[Any] = None,
        random_seed: Optional[int] = None,
        git_commit: Optional[str] = None,
        additional_metadata: Optional[
            Dict[str, Any]
        ] = None,
        validate: bool = True,
    ) -> ResearchBundle:
        experiment_id = self._resolve_attribute(
            benchmark_result,
            "experiment_id",
        )

        if experiment_id is None:
            experiment_id = self._resolve_attribute(
                experiment,
                "experiment_id",
            )

        experiment_name = (
            self._resolve_attribute(
                benchmark_result,
                "experiment_name",
            )
        )

        if experiment_name is None:
            experiment_name = (
                self._resolve_attribute(
                    experiment,
                    "experiment_name",
                )
            )

        metadata = BundleMetadata(
            project_version=self.project_version,
            framework_version=(
                self.framework_version
            ),
            researcher_name=(
                self.researcher_name
            ),
            institution_name=(
                self.institution_name
            ),
            experiment_id=(
                str(experiment_id)
                if experiment_id is not None
                else None
            ),
            experiment_name=(
                str(experiment_name)
                if experiment_name is not None
                else None
            ),
            git_commit=git_commit,
            random_seed=random_seed,
            additional_metadata=(
                dict(additional_metadata or {})
            ),
        )

        bundle = ResearchBundle(
            metadata=metadata,
            experiment=experiment,
            benchmark_result=benchmark_result,
            statistical_result=(
                statistical_result
            ),
            visualization_result=(
                visualization_result
            ),
            analytics_result=analytics_result,
            explainability_result=(
                explainability_result
            ),
        )

        if validate:
            validation = bundle.validate()

            if not validation.valid:
                joined_errors = "; ".join(
                    validation.errors
                )

                raise ValueError(
                    "Research bundle validation "
                    f"failed: {joined_errors}"
                )

        return bundle

    @staticmethod
    def _resolve_attribute(
        value: Any,
        attribute_name: str,
    ) -> Optional[Any]:
        if value is None:
            return None

        attribute = getattr(
            value,
            attribute_name,
            None,
        )

        if attribute is not None:
            return attribute

        if isinstance(value, dict):
            return value.get(attribute_name)

        return None