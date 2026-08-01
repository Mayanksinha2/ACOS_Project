from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class PublicationConfig:
    publication_title: str = (
        "Autonomous Multi-Agent Commerce Optimization "
        "Framework Using Adaptive Negotiation Protocols"
    )
    publication_subtitle: str = (
        "Research Manuscript Generated from the ACOS "
        "Experimental Pipeline"
    )
    author_name: str = "ACOS Researcher"
    institution_name: str = "M.Tech Research Project"
    publication_format: str = "ieee"
    include_abstract: bool = True
    include_keywords: bool = True
    include_introduction: bool = True
    include_methodology: bool = True
    include_experimental_setup: bool = True
    include_results: bool = True
    include_discussion: bool = True
    include_reproducibility: bool = True
    include_limitations: bool = True
    include_conclusion: bool = True
    include_references: bool = True
    keywords: List[str] = field(
        default_factory=lambda: [
            "Autonomous Commerce Optimization",
            "Multi-Agent Systems",
            "Adaptive Negotiation",
            "MOCRA",
            "E-commerce Optimization",
            "Decision Intelligence",
        ]
    )
    additional_sections: List[str] = field(
        default_factory=list
    )
    decimal_places: int = 4

    def __post_init__(self) -> None:
        allowed_formats = {
            "ieee",
            "springer",
            "generic",
        }

        self.publication_format = (
            self.publication_format.strip().lower()
        )

        if self.publication_format not in allowed_formats:
            raise ValueError(
                "publication_format must be one of: "
                "ieee, springer, generic."
            )

        if self.decimal_places < 0:
            raise ValueError(
                "decimal_places cannot be negative."
            )
