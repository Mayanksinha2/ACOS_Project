from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ReportConfig:
    """
    Configuration used while generating an ACOS
    research report.
    """

    report_title: str = (
        "Autonomous Commerce Optimization System"
    )

    report_subtitle: str = (
        "Experimental Research Report"
    )

    author_name: str = "Researcher"
    institution_name: str = "Institution"

    include_executive_summary: bool = True
    include_experiment_overview: bool = True
    include_benchmark_results: bool = True
    include_statistical_results: bool = True
    include_visualizations: bool = True
    include_analytics: bool = True
    include_explainability: bool = True
    include_validation: bool = True
    include_reproducibility: bool = True
    include_conclusion: bool = True

    decimal_places: int = 6

    additional_sections: List[str] = field(
        default_factory=list
    )