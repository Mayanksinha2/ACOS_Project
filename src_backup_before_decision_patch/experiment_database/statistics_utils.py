from __future__ import annotations

import math
from statistics import median
from typing import Iterable, Sequence

from .statistics_models import (
    NumericStatistics,
    RateStatistics,
)


def safe_rate(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return (numerator / denominator) * 100.0


def compute_numeric_statistics(
    values: Iterable[float | int | None],
) -> NumericStatistics:
    numbers = [
        float(value)
        for value in values
        if value is not None
    ]

    count = len(numbers)

    if count == 0:
        return NumericStatistics(
            count=0,
            mean=None,
            median=None,
            minimum=None,
            maximum=None,
            variance=None,
            standard_deviation=None,
        )

    mean_value = sum(numbers) / count
    variance_value = (
        sum(
            (value - mean_value) ** 2
            for value in numbers
        )
        / count
    )

    return NumericStatistics(
        count=count,
        mean=mean_value,
        median=float(median(numbers)),
        minimum=min(numbers),
        maximum=max(numbers),
        variance=variance_value,
        standard_deviation=math.sqrt(
            variance_value
        ),
    )


def compute_rate_statistics(
    values: Sequence[bool],
) -> RateStatistics:
    total_count = len(values)
    positive_count = sum(
        1
        for value in values
        if bool(value)
    )
    negative_count = (
        total_count - positive_count
    )

    return RateStatistics(
        total_count=total_count,
        positive_count=positive_count,
        negative_count=negative_count,
        positive_rate=safe_rate(
            positive_count,
            total_count,
        ),
        negative_rate=safe_rate(
            negative_count,
            total_count,
        ),
    )
