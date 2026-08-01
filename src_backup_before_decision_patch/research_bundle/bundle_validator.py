from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BundleValidationResult:
    """
    Result of validating one research bundle.
    """

    valid: bool = True

    errors: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def add_error(
        self,
        message: str,
    ) -> None:
        self.errors.append(message)
        self.valid = False

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class BundleValidator:
    """
    Validates the structure and consistency
    of an ACOS ResearchBundle.
    """

    REQUIRED_COMPONENTS = (
        "metadata",
        "experiment",
        "benchmark_result",
        "statistical_result",
        "visualization_result",
    )

    def validate(
        self,
        bundle: Any,
    ) -> BundleValidationResult:
        result = BundleValidationResult()

        if bundle is None:
            result.add_error(
                "Research bundle is missing."
            )

            return result

        self._validate_required_components(
            bundle=bundle,
            result=result,
        )

        if result.error_count > 0:
            return result

        self._validate_metadata(
            bundle=bundle,
            result=result,
        )

        self._validate_success_status(
            component=bundle.benchmark_result,
            component_name="benchmark_result",
            result=result,
        )

        self._validate_success_status(
            component=bundle.statistical_result,
            component_name="statistical_result",
            result=result,
        )

        self._validate_success_status(
            component=bundle.visualization_result,
            component_name="visualization_result",
            result=result,
        )

        self._validate_experiment_consistency(
            bundle=bundle,
            result=result,
        )

        self._validate_optional_components(
            bundle=bundle,
            result=result,
        )

        return result

    def _validate_required_components(
        self,
        bundle: Any,
        result: BundleValidationResult,
    ) -> None:
        for component_name in (
            self.REQUIRED_COMPONENTS
        ):
            component = getattr(
                bundle,
                component_name,
                None,
            )

            if component is None:
                result.add_error(
                    f"Required component "
                    f"'{component_name}' is missing."
                )

    @staticmethod
    def _validate_metadata(
        bundle: Any,
        result: BundleValidationResult,
    ) -> None:
        metadata = bundle.metadata

        if not getattr(
            metadata,
            "bundle_id",
            None,
        ):
            result.add_error(
                "Bundle metadata has no bundle_id."
            )

        if not getattr(
            metadata,
            "experiment_id",
            None,
        ):
            result.add_warning(
                "Bundle metadata has no "
                "experiment_id."
            )

        if not getattr(
            metadata,
            "experiment_name",
            None,
        ):
            result.add_warning(
                "Bundle metadata has no "
                "experiment_name."
            )

    @staticmethod
    def _validate_success_status(
        component: Any,
        component_name: str,
        result: BundleValidationResult,
    ) -> None:
        successful = getattr(
            component,
            "successful",
            None,
        )

        if successful is False:
            result.add_error(
                f"Component '{component_name}' "
                "was not successful."
            )

        elif successful is None:
            result.add_warning(
                f"Component '{component_name}' "
                "does not expose a successful "
                "status."
            )

    def _validate_experiment_consistency(
        self,
        bundle: Any,
        result: BundleValidationResult,
    ) -> None:
        expected_experiment_id = getattr(
            bundle.metadata,
            "experiment_id",
            None,
        )

        if not expected_experiment_id:
            return

        components = {
            "experiment": bundle.experiment,
            "benchmark_result": (
                bundle.benchmark_result
            ),
            "statistical_result": (
                bundle.statistical_result
            ),
            "visualization_result": (
                bundle.visualization_result
            ),
        }

        for component_name, component in (
            components.items()
        ):
            component_experiment_id = (
                self._resolve_attribute(
                    component,
                    "experiment_id",
                )
            )

            if component_experiment_id is None:
                continue

            if (
                str(component_experiment_id)
                != str(expected_experiment_id)
            ):
                result.add_error(
                    f"Experiment ID mismatch in "
                    f"'{component_name}': "
                    f"expected "
                    f"{expected_experiment_id}, "
                    f"received "
                    f"{component_experiment_id}."
                )

    @staticmethod
    def _validate_optional_components(
        bundle: Any,
        result: BundleValidationResult,
    ) -> None:
        if bundle.analytics_result is None:
            result.add_warning(
                "Analytics result is not included."
            )

        if (
            bundle.explainability_result
            is None
        ):
            result.add_warning(
                "Explainability result is not "
                "included."
            )

    @staticmethod
    def _resolve_attribute(
        value: Any,
        attribute_name: str,
    ):
        if value is None:
            return None

        if isinstance(value, dict):
            return value.get(attribute_name)

        return getattr(
            value,
            attribute_name,
            None,
        )