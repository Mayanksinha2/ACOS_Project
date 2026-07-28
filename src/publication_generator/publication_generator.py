from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List

from publication_generator.publication_config import (
    PublicationConfig,
)
from publication_generator.publication_result import (
    PublicationGenerationResult,
)


class PublicationGenerator:
    """
    Generate publication-oriented Markdown and LaTeX
    manuscripts from an ACOS ReportGenerationResult.
    """

    def __init__(
        self,
        config: PublicationConfig | None = None,
    ) -> None:
        self.config = config or PublicationConfig()

    def generate(
        self,
        report: Any,
    ) -> PublicationGenerationResult:
        report_id = str(
            self._get_value(
                report,
                "report_id",
                "",
            )
        ).strip()

        bundle_id = str(
            self._get_value(
                report,
                "bundle_id",
                "",
            )
        ).strip()

        experiment_id = str(
            self._get_value(
                report,
                "experiment_id",
                "",
            )
        ).strip()

        result = PublicationGenerationResult(
            report_id=report_id,
            bundle_id=bundle_id,
            experiment_id=experiment_id,
            publication_title=(
                self.config.publication_title
            ),
        )

        if report is None:
            result.errors.append(
                "Report generation result is missing."
            )
            return result

        if not report_id:
            result.errors.append(
                "Report result does not contain a "
                "valid report_id."
            )

        if not bundle_id:
            result.errors.append(
                "Report result does not contain a "
                "valid bundle_id."
            )

        if not experiment_id:
            result.errors.append(
                "Report result does not contain a "
                "valid experiment_id."
            )

        successful = bool(
            self._get_value(
                report,
                "successful",
                False,
            )
        )

        if not successful:
            result.errors.append(
                "Publication generation requires a "
                "successful research report."
            )

        if result.errors:
            return result

        try:
            report_data = self._object_to_dict(
                self._get_value(
                    report,
                    "report_data",
                    {},
                )
            ) or {}

            validation = report_data.get(
                "validation",
                {},
            ) or {}

            result.warnings.extend(
                list(
                    validation.get(
                        "warnings",
                        [],
                    )
                    or []
                )
            )

            publication_data = (
                self._build_publication_data(
                    report=report,
                    report_data=report_data,
                )
            )

            sections = self._build_sections(
                publication_data
            )

            result.markdown_content = (
                "\n\n".join(
                    section.strip()
                    for section in sections
                    if section and section.strip()
                )
                + "\n"
            )

            result.section_titles = (
                self._extract_markdown_titles(
                    result.markdown_content
                )
            )

            result.latex_content = (
                self._build_latex_document(
                    publication_data
                )
            )

            result.publication_data = (
                publication_data
            )

        except Exception as error:
            result.errors.append(
                f"{type(error).__name__}: {error}"
            )

        return result

    def _build_publication_data(
        self,
        report: Any,
        report_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = report_data.get(
            "metadata",
            {},
        ) or {}

        benchmark = report_data.get(
            "benchmark",
            {},
        ) or {}

        statistics = report_data.get(
            "statistics",
            {},
        ) or {}

        experiment = report_data.get(
            "experiment",
            {},
        ) or {}

        visualizations = report_data.get(
            "visualizations",
            {},
        ) or {}

        return {
            "identity": {
                "report_id": str(
                    self._get_value(
                        report,
                        "report_id",
                        "",
                    )
                ),
                "bundle_id": str(
                    self._get_value(
                        report,
                        "bundle_id",
                        "",
                    )
                ),
                "experiment_id": str(
                    self._get_value(
                        report,
                        "experiment_id",
                        "",
                    )
                ),
            },
            "metadata": metadata,
            "experiment": experiment,
            "benchmark": benchmark,
            "statistics": statistics,
            "visualizations": visualizations,
            "analytics": report_data.get(
                "analytics"
            ),
            "explainability": report_data.get(
                "explainability"
            ),
            "validation": report_data.get(
                "validation",
                {},
            ),
        }

    def _build_sections(
        self,
        data: Dict[str, Any],
    ) -> List[str]:
        sections = [
            self._build_title(data),
        ]

        if self.config.include_abstract:
            sections.append(
                self._build_abstract(data)
            )

        if self.config.include_keywords:
            sections.append(
                self._build_keywords()
            )

        if self.config.include_introduction:
            sections.append(
                self._build_introduction()
            )

        if self.config.include_methodology:
            sections.append(
                self._build_methodology(data)
            )

        if (
            self.config
            .include_experimental_setup
        ):
            sections.append(
                self._build_experimental_setup(
                    data
                )
            )

        if self.config.include_results:
            sections.append(
                self._build_results(data)
            )

        if self.config.include_discussion:
            sections.append(
                self._build_discussion(data)
            )

        if (
            self.config
            .include_reproducibility
        ):
            sections.append(
                self._build_reproducibility(
                    data
                )
            )

        if self.config.include_limitations:
            sections.append(
                self._build_limitations()
            )

        for title in (
            self.config.additional_sections
        ):
            sections.append(
                f"## {title}\n\n"
                "This section is reserved for "
                "additional publication content."
            )

        if self.config.include_conclusion:
            sections.append(
                self._build_conclusion(data)
            )

        if self.config.include_references:
            sections.append(
                self._build_references()
            )

        return sections

    def _build_title(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]

        researcher = (
            metadata.get("researcher_name")
            or self.config.author_name
        )

        institution = (
            metadata.get("institution_name")
            or self.config.institution_name
        )

        return (
            f"# {self.config.publication_title}\n\n"
            f"**{self.config.publication_subtitle}**\n\n"
            f"**Author:** {researcher}  \n"
            f"**Institution:** {institution}  \n"
            f"**Publication format:** "
            f"{self.config.publication_format.upper()}"
        )

    def _build_abstract(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        total = benchmark.get(
            "total_scenarios",
            0,
        )
        successful = benchmark.get(
            "successful_scenarios",
            0,
        )

        best_reward = self._best_entry(
            benchmark.get(
                "average_reward",
                {},
            )
            or {},
            highest=True,
        )

        best_text = ""

        if best_reward:
            best_text = (
                f" The strongest average reward was "
                f"observed for {best_reward[0]} "
                f"({self._format_number(best_reward[1])})."
            )

        return (
            "## Abstract\n\n"
            "This study presents the Autonomous Commerce "
            "Optimization System (ACOS), a multi-agent "
            "framework for coordinating pricing, "
            "inventory, marketing, and related commerce "
            "decisions through adaptive negotiation and "
            "multi-criteria selection. The experimental "
            f"evaluation covered {total} scenarios, with "
            f"{successful} completed successfully."
            f"{best_text} The generated benchmark, "
            "statistical, visualization, and validation "
            "artifacts provide a reproducible basis for "
            "evaluating the proposed architecture."
        )

    def _build_keywords(self) -> str:
        return (
            "## Keywords\n\n"
            + ", ".join(self.config.keywords)
        )

    def _build_introduction(self) -> str:
        return (
            "## 1. Introduction\n\n"
            "Modern e-commerce optimization requires "
            "multiple objectives to be balanced "
            "simultaneously, including profitability, "
            "customer conversion, inventory health, "
            "marketing efficiency, operational risk, "
            "and execution speed. Conventional systems "
            "often optimize these objectives separately, "
            "which can produce conflicting actions.\n\n"
            "ACOS addresses this limitation through a "
            "coordinated multi-agent architecture in "
            "which specialized agents generate candidate "
            "actions, detect conflicts, negotiate, and "
            "select a final decision using a structured "
            "multi-criteria evaluation process."
        )

    def _build_methodology(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]
        additional = metadata.get(
            "additional_metadata",
            {},
        ) or {}

        decision_method = additional.get(
            "decision_method",
            "MOCRA",
        )

        negotiation_enabled = (
            additional.get(
                "negotiation_enabled",
                True,
            )
        )

        return (
            "## 2. Methodology\n\n"
            "The proposed framework uses autonomous "
            "agents representing distinct commerce "
            "functions. Each agent evaluates the shared "
            "business state and proposes an action with "
            "associated confidence, utility, and risk "
            "signals. A conflict detector identifies "
            "incompatible proposals. When required, an "
            "adaptive negotiation engine modifies or "
            "reconciles competing proposals before final "
            "selection.\n\n"
            f"The configured decision method was "
            f"**{decision_method}**. Adaptive negotiation "
            f"was **{'enabled' if negotiation_enabled else 'disabled'}** "
            "for the reported experiment."
        )

    def _build_experimental_setup(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]
        benchmark = data["benchmark"]

        rows = {
            "Experiment ID": (
                data["identity"]["experiment_id"]
            ),
            "Random seed": metadata.get(
                "random_seed",
                "Not available",
            ),
            "Total scenarios": benchmark.get(
                "total_scenarios",
                0,
            ),
            "Successful scenarios": (
                benchmark.get(
                    "successful_scenarios",
                    0,
                )
            ),
            "Failed scenarios": benchmark.get(
                "failed_scenarios",
                0,
            ),
            "Python version": metadata.get(
                "python_version",
                "Not available",
            ),
            "Operating system": metadata.get(
                "operating_system",
                "Not available",
            ),
        }

        return (
            "## 3. Experimental Setup\n\n"
            + self._table(rows)
        )

    def _build_results(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        lines = [
            "## 4. Results",
            "",
        ]

        metrics = [
            (
                "Average Reward",
                benchmark.get(
                    "average_reward",
                    {},
                ),
            ),
            (
                "Average Risk",
                benchmark.get(
                    "average_risk",
                    {},
                ),
            ),
            (
                "Average Confidence",
                benchmark.get(
                    "average_confidence",
                    {},
                ),
            ),
            (
                "Average Execution Time",
                benchmark.get(
                    "average_execution_time",
                    {},
                ),
            ),
        ]

        for title, values in metrics:
            if not isinstance(values, dict):
                continue

            if not values:
                continue

            lines.extend(
                [
                    f"### {title}",
                    "",
                    self._strategy_table(values),
                    "",
                ]
            )

        statistics = data["statistics"]

        if statistics:
            lines.extend(
                [
                    "### Statistical Evidence",
                    "",
                    "The statistical evaluation result "
                    "was included in the research bundle. "
                    "Pairwise comparisons, confidence "
                    "intervals, rankings, and effect sizes "
                    "should be interpreted together with "
                    "the benchmark metrics.",
                ]
            )

        return "\n".join(lines).strip()

    def _build_discussion(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        best_reward = self._best_entry(
            benchmark.get(
                "average_reward",
                {},
            )
            or {},
            highest=True,
        )

        lowest_risk = self._best_entry(
            benchmark.get(
                "average_risk",
                {},
            )
            or {},
            highest=False,
        )

        fastest = self._best_entry(
            benchmark.get(
                "average_execution_time",
                {},
            )
            or {},
            highest=False,
        )

        observations = []

        if best_reward:
            observations.append(
                f"the highest average reward was "
                f"produced by {best_reward[0]}"
            )

        if lowest_risk:
            observations.append(
                f"the lowest average risk was "
                f"produced by {lowest_risk[0]}"
            )

        if fastest:
            observations.append(
                f"the fastest average execution was "
                f"recorded for {fastest[0]}"
            )

        evidence = (
            "; ".join(observations)
            if observations
            else (
                "the benchmark data did not expose "
                "standard aggregate strategy metrics"
            )
        )

        return (
            "## 5. Discussion\n\n"
            f"The reported results indicate that {evidence}. "
            "These outcomes demonstrate that strategy "
            "quality cannot be assessed using reward "
            "alone. Risk, confidence, agreement, and "
            "execution cost must also be considered. "
            "The ACOS architecture is designed to make "
            "these trade-offs explicit through agent "
            "coordination and multi-criteria reasoning."
        )

    def _build_reproducibility(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]

        return (
            "## 6. Reproducibility\n\n"
            + self._table(
                {
                    "Report ID": (
                        data["identity"]["report_id"]
                    ),
                    "Bundle ID": (
                        data["identity"]["bundle_id"]
                    ),
                    "Experiment ID": (
                        data["identity"][
                            "experiment_id"
                        ]
                    ),
                    "Project version": (
                        metadata.get(
                            "project_version",
                            "Not available",
                        )
                    ),
                    "Framework version": (
                        metadata.get(
                            "framework_version",
                            "Not available",
                        )
                    ),
                    "Git commit": metadata.get(
                        "git_commit",
                        "Not available",
                    ),
                    "Random seed": metadata.get(
                        "random_seed",
                        "Not available",
                    ),
                }
            )
        )

    def _build_limitations(self) -> str:
        return (
            "## 7. Limitations\n\n"
            "The reported findings are limited by the "
            "scenario distributions, baseline strategies, "
            "agent configurations, and simulation "
            "assumptions used in the current experiment. "
            "External validity should therefore be tested "
            "using additional datasets, longer execution "
            "horizons, broader commerce environments, "
            "and real-world deployment studies."
        )

    def _build_conclusion(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        total = benchmark.get(
            "total_scenarios",
            0,
        )

        return (
            "## 8. Conclusion\n\n"
            "This work introduced ACOS as a reproducible "
            "multi-agent commerce optimization framework "
            "that combines specialized agent decisions, "
            "conflict detection, adaptive negotiation, "
            "and multi-criteria selection. The completed "
            f"evaluation across {total} scenarios produced "
            "benchmark, statistical, visualization, "
            "bundle, report, and publication artifacts. "
            "The framework provides a strong basis for "
            "future large-scale experiments, thesis "
            "development, and peer-reviewed publication."
        )

    def _build_references(self) -> str:
        return (
            "## References\n\n"
            "1. References should be added from the "
            "validated literature-review source used by "
            "the ACOS research project.\n"
            "2. Do not treat automatically generated "
            "placeholder references as publication-ready "
            "citations."
        )

    def _build_latex_document(
        self,
        data: Dict[str, Any],
    ) -> str:
        title = self._latex_escape(
            self.config.publication_title
        )
        author = self._latex_escape(
            data["metadata"].get(
                "researcher_name",
                self.config.author_name,
            )
        )
        institution = self._latex_escape(
            data["metadata"].get(
                "institution_name",
                self.config.institution_name,
            )
        )

        document_class = (
            "IEEEtran"
            if self.config.publication_format
            == "ieee"
            else "article"
        )

        total = data["benchmark"].get(
            "total_scenarios",
            0,
        )
        successful = data["benchmark"].get(
            "successful_scenarios",
            0,
        )

        keywords = ", ".join(
            self._latex_escape(item)
            for item in self.config.keywords
        )

        return f"""\\documentclass{{{document_class}}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{booktabs}}
\\usepackage{{hyperref}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\title{{{title}}}
\\author{{{author}\\\\{institution}}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
This study presents the Autonomous Commerce Optimization
System (ACOS), a multi-agent framework using adaptive
negotiation and multi-criteria decision selection. The
evaluation covered {total} scenarios, with {successful}
completed successfully. The resulting artifacts support
benchmarking, statistical analysis, visualization, and
reproducibility.
\\end{{abstract}}

\\textbf{{Keywords:}} {keywords}

\\section{{Introduction}}
Modern e-commerce optimization requires coordinated
decisions across pricing, inventory, marketing, and
customer-facing operations. ACOS addresses conflicts
among these objectives using specialized autonomous agents.

\\section{{Methodology}}
Agents generate candidate actions from a shared business
state. Conflicts are detected and, when required, resolved
through adaptive negotiation before multi-criteria
selection.

\\section{{Experimental Setup}}
Experiment ID: \\texttt{{{self._latex_escape(data["identity"]["experiment_id"])}}}.\\\\
Bundle ID: \\texttt{{{self._latex_escape(data["identity"]["bundle_id"])}}}.\\\\
Total scenarios: {total}.\\\\
Successful scenarios: {successful}.

\\section{{Results}}
The benchmark and statistical results are preserved in the
publication data artifact and should be interpreted across
reward, risk, confidence, agreement, and execution time.

\\section{{Discussion}}
The evidence demonstrates the need to evaluate commerce
decisions using multiple competing criteria rather than a
single performance measure.

\\section{{Conclusion}}
ACOS provides a reproducible research architecture for
multi-agent commerce optimization and establishes a basis
for expanded experimentation and peer-reviewed evaluation.

\\section{{References}}
Validated literature references must be inserted from the
project literature-review source before submission.

\\end{{document}}
"""

    def _table(
        self,
        values: Dict[str, Any],
    ) -> str:
        lines = [
            "| Field | Value |",
            "|---|---|",
        ]

        for key, value in values.items():
            lines.append(
                f"| {key} | "
                f"{self._format_value(value)} |"
            )

        return "\n".join(lines)

    def _strategy_table(
        self,
        values: Dict[str, Any],
    ) -> str:
        lines = [
            "| Strategy | Value |",
            "|---|---:|",
        ]

        for strategy, value in values.items():
            lines.append(
                f"| {strategy} | "
                f"{self._format_value(value)} |"
            )

        return "\n".join(lines)

    def _best_entry(
        self,
        values: Dict[str, Any],
        highest: bool,
    ) -> tuple[str, float] | None:
        numeric = {}

        for key, value in values.items():
            try:
                numeric[str(key)] = float(value)
            except (
                TypeError,
                ValueError,
            ):
                continue

        if not numeric:
            return None

        selector = max if highest else min

        key = selector(
            numeric,
            key=numeric.get,
        )

        return key, numeric[key]

    def _extract_markdown_titles(
        self,
        markdown: str,
    ) -> List[str]:
        titles = []

        for line in markdown.splitlines():
            stripped = line.strip()

            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()

                if title:
                    titles.append(title)

        return titles

    def _format_value(
        self,
        value: Any,
    ) -> str:
        if isinstance(value, bool):
            return "Yes" if value else "No"

        if isinstance(value, float):
            return self._format_number(value)

        if value is None:
            return "Not available"

        return str(value).replace(
            "|",
            "\\|",
        )

    def _format_number(
        self,
        value: Any,
    ) -> str:
        try:
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return str(value)

        return (
            f"{number:.{self.config.decimal_places}f}"
        )

    def _object_to_dict(
        self,
        value: Any,
    ) -> Any:
        if value is None:
            return None

        if isinstance(value, dict):
            return {
                str(key): self._object_to_dict(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                self._object_to_dict(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                self._object_to_dict(item)
                for item in value
            ]

        if is_dataclass(value):
            return self._object_to_dict(
                asdict(value)
            )

        to_dict = getattr(
            value,
            "to_dict",
            None,
        )

        if callable(to_dict):
            return self._object_to_dict(
                to_dict()
            )

        if hasattr(value, "__dict__"):
            return {
                key: self._object_to_dict(item)
                for key, item
                in vars(value).items()
                if not key.startswith("_")
            }

        return value

    @staticmethod
    def _get_value(
        value: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        if isinstance(value, dict):
            return value.get(name, default)

        return getattr(value, name, default)

    @staticmethod
    def _latex_escape(
        value: Any,
    ) -> str:
        text = str(value)

        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }

        return "".join(
            replacements.get(char, char)
            for char in text
        )
