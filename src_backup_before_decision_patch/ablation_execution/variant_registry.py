from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable, List

from .ablation_variant import AblationVariant
from .feature_flags import ACOSFeatureFlags


class AblationVariantRegistry:
    """
    Registry for predefined and custom ACOS variants.
    """

    def __init__(
        self,
        include_defaults: bool = True,
    ) -> None:
        self._variants: Dict[
            str,
            AblationVariant,
        ] = OrderedDict()

        if include_defaults:
            self._register_defaults()

    def register(
        self,
        variant: AblationVariant,
        replace: bool = False,
    ) -> None:
        if (
            variant.name in self._variants
            and not replace
        ):
            raise ValueError(
                f"Ablation variant "
                f"'{variant.name}' is already registered."
            )

        self._variants[variant.name] = variant

    def get(
        self,
        name: str,
    ) -> AblationVariant:
        try:
            return self._variants[name]
        except KeyError as error:
            available = ", ".join(
                self._variants.keys()
            )

            raise KeyError(
                f"Unknown ablation variant '{name}'. "
                f"Available variants: {available}"
            ) from error

    def names(self) -> List[str]:
        return list(
            self._variants.keys()
        )

    def values(self) -> List[AblationVariant]:
        return list(
            self._variants.values()
        )

    def select(
        self,
        names: Iterable[str],
    ) -> List[AblationVariant]:
        return [
            self.get(name)
            for name in names
        ]

    def _register_defaults(self) -> None:
        defaults = [
            AblationVariant(
                name="baseline",
                description=(
                    "Complete ACOS architecture with every "
                    "research component enabled."
                ),
                feature_flags=ACOSFeatureFlags(),
            ),
            AblationVariant(
                name="without_conflict_detection",
                description=(
                    "Disables explicit conflict detection."
                ),
                feature_flags=ACOSFeatureFlags(
                    enable_conflict_detection=False,
                ),
            ),
            AblationVariant(
                name="without_negotiation",
                description=(
                    "Disables adaptive negotiation while "
                    "keeping conflict detection enabled."
                ),
                feature_flags=ACOSFeatureFlags(
                    enable_negotiation=False,
                ),
            ),
            AblationVariant(
                name="without_mocra",
                description=(
                    "Disables MOCRA multi-criteria decision "
                    "selection."
                ),
                feature_flags=ACOSFeatureFlags(
                    enable_mocra=False,
                ),
            ),
            AblationVariant(
                name="without_adaptive_learning",
                description=(
                    "Disables adaptive learning and weight "
                    "updates."
                ),
                feature_flags=ACOSFeatureFlags(
                    enable_adaptive_learning=False,
                ),
            ),
            AblationVariant(
                name="without_outcome_evaluation",
                description=(
                    "Disables post-decision outcome "
                    "evaluation."
                ),
                feature_flags=ACOSFeatureFlags(
                    enable_outcome_evaluation=False,
                ),
            ),
        ]

        for variant in defaults:
            self.register(variant)
