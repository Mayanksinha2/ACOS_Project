from __future__ import annotations

import math
from statistics import (
    mean,
    median,
    stdev,
    variance,
)
from typing import Iterable, List, Tuple


class StatisticalUtils:
    """
    Reusable statistical calculations.

    Uses Python's standard library and does not
    require SciPy.
    """

    @staticmethod
    def clean_values(
        values: Iterable[float],
    ) -> List[float]:
        cleaned: List[float] = []

        for value in values:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue

            if math.isfinite(numeric):
                cleaned.append(numeric)

        return cleaned

    @classmethod
    def descriptive(
        cls,
        values: Iterable[float],
        confidence_level: float = 0.95,
    ) -> dict:
        cleaned = cls.clean_values(values)

        sample_size = len(cleaned)

        if sample_size == 0:
            return {
                "sample_size": 0,
                "mean": 0.0,
                "median": 0.0,
                "standard_deviation": 0.0,
                "variance": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
                "confidence_interval_lower": 0.0,
                "confidence_interval_upper": 0.0,
            }

        sample_mean = mean(cleaned)
        sample_median = median(cleaned)

        if sample_size > 1:
            sample_stdev = stdev(cleaned)
            sample_variance = variance(cleaned)
        else:
            sample_stdev = 0.0
            sample_variance = 0.0

        lower, upper = cls.confidence_interval(
            cleaned,
            confidence_level=confidence_level,
        )

        return {
            "sample_size": sample_size,
            "mean": round(sample_mean, 6),
            "median": round(sample_median, 6),
            "standard_deviation": round(
                sample_stdev,
                6,
            ),
            "variance": round(
                sample_variance,
                6,
            ),
            "minimum": round(
                min(cleaned),
                6,
            ),
            "maximum": round(
                max(cleaned),
                6,
            ),
            "confidence_interval_lower": round(
                lower,
                6,
            ),
            "confidence_interval_upper": round(
                upper,
                6,
            ),
        }

    @classmethod
    def confidence_interval(
        cls,
        values: Iterable[float],
        confidence_level: float = 0.95,
    ) -> Tuple[float, float]:
        cleaned = cls.clean_values(values)

        sample_size = len(cleaned)

        if sample_size == 0:
            return 0.0, 0.0

        sample_mean = mean(cleaned)

        if sample_size == 1:
            return sample_mean, sample_mean

        sample_stdev = stdev(cleaned)

        if sample_stdev == 0.0:
            return sample_mean, sample_mean

        critical_value = cls._critical_value(
            sample_size=sample_size,
            confidence_level=confidence_level,
        )

        standard_error = (
            sample_stdev
            / math.sqrt(sample_size)
        )

        margin = (
            critical_value
            * standard_error
        )

        return (
            sample_mean - margin,
            sample_mean + margin,
        )

    @staticmethod
    def _critical_value(
        sample_size: int,
        confidence_level: float,
    ) -> float:
        """
        Approximate two-tailed t critical values
        for a 95% confidence interval.

        For larger samples, this approaches 1.96.
        """

        if confidence_level != 0.95:
            return 1.96

        degrees_of_freedom = max(
            1,
            sample_size - 1,
        )

        lookup = {
            1: 12.706,
            2: 4.303,
            3: 3.182,
            4: 2.776,
            5: 2.571,
            6: 2.447,
            7: 2.365,
            8: 2.306,
            9: 2.262,
            10: 2.228,
            11: 2.201,
            12: 2.179,
            13: 2.160,
            14: 2.145,
            15: 2.131,
            16: 2.120,
            17: 2.110,
            18: 2.101,
            19: 2.093,
            20: 2.086,
            21: 2.080,
            22: 2.074,
            23: 2.069,
            24: 2.064,
            25: 2.060,
            26: 2.056,
            27: 2.052,
            28: 2.048,
            29: 2.045,
            30: 2.042,
        }

        if degrees_of_freedom in lookup:
            return lookup[degrees_of_freedom]

        if degrees_of_freedom <= 40:
            return 2.021

        if degrees_of_freedom <= 60:
            return 2.000

        if degrees_of_freedom <= 120:
            return 1.980

        return 1.960

    @classmethod
    def paired_t_test(
        cls,
        reference_values: Iterable[float],
        comparison_values: Iterable[float],
    ) -> Tuple[float, float]:
        """
        Paired t-test using a normal-distribution
        approximation for the two-tailed p-value.

        Returns:
            t_statistic, p_value
        """

        reference = cls.clean_values(
            reference_values
        )

        comparison = cls.clean_values(
            comparison_values
        )

        sample_size = min(
            len(reference),
            len(comparison),
        )

        if sample_size < 2:
            return 0.0, 1.0

        differences = [
            reference[index]
            - comparison[index]
            for index in range(sample_size)
        ]

        difference_mean = mean(differences)

        difference_stdev = stdev(differences)

        if difference_stdev == 0.0:
            if difference_mean == 0.0:
                return 0.0, 1.0

            return (
                math.copysign(
                    float("inf"),
                    difference_mean,
                ),
                0.0,
            )

        standard_error = (
            difference_stdev
            / math.sqrt(sample_size)
        )

        t_statistic = (
            difference_mean
            / standard_error
        )

        p_value = (
            2.0
            * (
                1.0
                - cls._normal_cdf(
                    abs(t_statistic)
                )
            )
        )

        p_value = max(
            0.0,
            min(1.0, p_value),
        )

        return (
            round(t_statistic, 6),
            round(p_value, 6),
        )

    @classmethod
    def paired_cohens_d(
        cls,
        reference_values: Iterable[float],
        comparison_values: Iterable[float],
    ) -> float:
        """
        Cohen's dz for paired observations.
        """

        reference = cls.clean_values(
            reference_values
        )

        comparison = cls.clean_values(
            comparison_values
        )

        sample_size = min(
            len(reference),
            len(comparison),
        )

        if sample_size < 2:
            return 0.0

        differences = [
            reference[index]
            - comparison[index]
            for index in range(sample_size)
        ]

        difference_stdev = stdev(differences)

        if difference_stdev == 0.0:
            return 0.0

        effect_size = (
            mean(differences)
            / difference_stdev
        )

        return round(effect_size, 6)

    @staticmethod
    def interpret_effect_size(
        effect_size: float,
    ) -> str:
        absolute = abs(effect_size)

        if absolute < 0.2:
            return "negligible"

        if absolute < 0.5:
            return "small"

        if absolute < 0.8:
            return "medium"

        return "large"

    @staticmethod
    def _normal_cdf(value: float) -> float:
        return (
            1.0
            + math.erf(
                value / math.sqrt(2.0)
            )
        ) / 2.0