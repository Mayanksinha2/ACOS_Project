from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(slots=True)
class MetricSummary:
    name: str
    count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    standard_deviation: float | None
    variance: float | None
    confidence_interval_low: float | None
    confidence_interval_high: float | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": self.mean,
            "median": self.median,
            "standard_deviation": (
                self.standard_deviation
            ),
            "variance": self.variance,
            "confidence_interval_low": (
                self.confidence_interval_low
            ),
            "confidence_interval_high": (
                self.confidence_interval_high
            ),
        }
