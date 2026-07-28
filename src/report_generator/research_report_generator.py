from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List

from report_generator.report_config import (
    ReportConfig,
)
from report_generator.report_result import (
    ReportGenerationResult,
)


class ResearchReportGenerator:
    """
    Generate a structured Markdown research report
    from a validated ACOS ResearchBundle.
    """

    def __init__(
        self,
        config: ReportConfig | None = None,
    ) -> None:
        self.config = config or ReportConfig()

    def generate(
        self,
        bundle: Any,
    ) -> ReportGenerationResult:
        metadata = self._get_value(
            bundle,
            "metadata",
            None,
        )

        bundle_id = str(
            self._first_non_empty(
                self._get_value(
                    metadata,
                    "bundle_id",
                    None,
                ),
                self._get_value(
                    bundle,
                    "bundle_id",
                    None,
                ),
                "",
            )
        ).strip()

        experiment_id = str(
            self._first_non_empty(
                self._get_value(
                    metadata,
                    "experiment_id",
                    None,
                ),
                self._get_value(
                    bundle,
                    "experiment_id",
                    None,
                ),
                self._get_nested_value(
                    bundle,
                    [
                        "benchmark_result",
                        "experiment_id",
                    ],
                    "",
                ),
            )
        )

        result = ReportGenerationResult(
            bundle_id=bundle_id,
            experiment_id=experiment_id,
            report_title=(
                self.config.report_title
            ),
        )

        if not bundle_id:
            result.errors.append(
                "Research bundle does not contain "
                "a valid bundle_id."
            )
            return result

        if not experiment_id:
            result.errors.append(
                "Research bundle does not contain "
                "a valid experiment_id."
            )
            return result

        try:
            validation_result = self._validate_bundle(
                bundle
            )

            if not validation_result["valid"]:
                result.errors.extend(
                    validation_result["errors"]
                )
                return result

            result.warnings.extend(
                validation_result["warnings"]
            )

            report_data = self._build_report_data(
                bundle=bundle,
                validation_result=validation_result,
            )

            sections: List[str] = []

            sections.append(
                self._build_title_section(
                    report_data
                )
            )

            if (
                self.config
                .include_executive_summary
            ):
                sections.append(
                    self._build_executive_summary(
                        report_data
                    )
                )

            if (
                self.config
                .include_experiment_overview
            ):
                sections.append(
                    self._build_experiment_overview(
                        report_data
                    )
                )

            if (
                self.config
                .include_benchmark_results
            ):
                sections.append(
                    self._build_benchmark_section(
                        report_data
                    )
                )

            if (
                self.config
                .include_statistical_results
            ):
                sections.append(
                    self._build_statistical_section(
                        report_data
                    )
                )

            if (
                self.config
                .include_visualizations
            ):
                sections.append(
                    self._build_visualization_section(
                        report_data
                    )
                )

            if self.config.include_analytics:
                sections.append(
                    self._build_analytics_section(
                        report_data
                    )
                )

            if (
                self.config
                .include_explainability
            ):
                sections.append(
                    self._build_explainability_section(
                        report_data
                    )
                )

            if self.config.include_validation:
                sections.append(
                    self._build_validation_section(
                        report_data
                    )
                )

            if (
                self.config
                .include_reproducibility
            ):
                sections.append(
                    self._build_reproducibility_section(
                        report_data
                    )
                )

            for custom_section in (
                self.config.additional_sections
            ):
                sections.append(
                    f"## {custom_section}\n\n"
                    "This section is reserved for "
                    "additional research content."
                )

            if self.config.include_conclusion:
                sections.append(
                    self._build_conclusion_section(
                        report_data
                    )
                )

            sections = [
                section.strip()
                for section in sections
                if section and section.strip()
            ]

            result.markdown_content = (
                "\n\n---\n\n".join(sections)
                + "\n"
            )

            result.section_titles = (
                self._extract_section_titles(
                    result.markdown_content
                )
            )

            result.report_data = report_data

        except Exception as error:
            result.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return result

    def _validate_bundle(
        self,
        bundle: Any,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if bundle is None:
            return {
                "valid": False,
                "errors": [
                    "Research bundle is missing."
                ],
                "warnings": [],
            }

        validate_method = getattr(
            bundle,
            "validate",
            None,
        )

        if callable(validate_method):
            validation = validate_method()

            valid = bool(
                self._get_value(
                    validation,
                    "valid",
                    False,
                )
            )

            errors.extend(
                list(
                    self._get_value(
                        validation,
                        "errors",
                        [],
                    )
                    or []
                )
            )

            warnings.extend(
                list(
                    self._get_value(
                        validation,
                        "warnings",
                        [],
                    )
                    or []
                )
            )

            return {
                "valid": valid,
                "errors": errors,
                "warnings": warnings,
            }

        required_components = [
            "metadata",
            "experiment",
            "benchmark_result",
            "statistical_result",
            "visualization_result",
        ]

        for component_name in (
            required_components
        ):
            component = self._get_value(
                bundle,
                component_name,
                None,
            )

            if component is None:
                errors.append(
                    "Required bundle component "
                    f"'{component_name}' is missing."
                )

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _build_report_data(
        self,
        bundle: Any,
        validation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = self._object_to_dict(
            self._get_value(
                bundle,
                "metadata",
                {},
            )
        )

        experiment = self._object_to_dict(
            self._get_value(
                bundle,
                "experiment",
                {},
            )
        )

        benchmark = self._object_to_dict(
            self._get_value(
                bundle,
                "benchmark_result",
                {},
            )
        )

        statistics = self._object_to_dict(
            self._get_value(
                bundle,
                "statistical_result",
                {},
            )
        )

        visualizations = self._object_to_dict(
            self._get_value(
                bundle,
                "visualization_result",
                {},
            )
        )

        analytics_object = self._get_value(
            bundle,
            "analytics_result",
            None,
        )

        explainability_object = self._get_value(
            bundle,
            "explainability_result",
            None,
        )

        analytics = (
            self._object_to_dict(
                analytics_object
            )
            if analytics_object is not None
            else None
        )

        explainability = (
            self._object_to_dict(
                explainability_object
            )
            if explainability_object is not None
            else None
        )

        return {
            "bundle": {
                "bundle_id": str(
                    self._first_non_empty(
                        metadata.get("bundle_id"),
                        self._get_value(
                            bundle,
                            "bundle_id",
                            None,
                        ),
                        "",
                    )
                ).strip(),
                "summary": self._safe_summary(
                    bundle
                ),
            },
            "metadata": metadata,
            "experiment": experiment,
            "benchmark": benchmark,
            "statistics": statistics,
            "visualizations": visualizations,
            "analytics": analytics,
            "explainability": explainability,
            "validation": validation_result,
        }

    def _build_title_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]

        experiment_name = self._first_non_empty(
            metadata.get("experiment_name"),
            data["experiment"].get(
                "experiment_name"
            ),
            "ACOS Experiment",
        )

        project_name = self._first_non_empty(
            metadata.get("project_name"),
            self.config.report_title,
        )

        created_at = self._first_non_empty(
            metadata.get("created_at"),
            data["bundle"]["summary"].get(
                "created_at"
            ),
            "Not available",
        )

        return (
            f"# {project_name}\n\n"
            f"## {self.config.report_subtitle}\n\n"
            f"**Experiment:** {experiment_name}  \n"
            f"**Author:** "
            f"{self.config.author_name}  \n"
            f"**Institution:** "
            f"{self.config.institution_name}  \n"
            f"**Generated at:** {created_at}"
        )

    def _build_executive_summary(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        total_scenarios = benchmark.get(
            "total_scenarios",
            0,
        )

        successful_scenarios = benchmark.get(
            "successful_scenarios",
            0,
        )

        average_reward = benchmark.get(
            "average_reward",
            {},
        ) or {}

        reward_wins = benchmark.get(
            "reward_win_frequency",
            {},
        ) or {}

        highest_average_reward = (
            self._best_mapping_entry(
                average_reward,
                highest=True,
            )
        )

        most_reward_wins = (
            self._best_mapping_entry(
                reward_wins,
                highest=True,
            )
        )

        lines = [
            "## Executive Summary",
            "",
            (
                "This report presents the experimental "
                "evaluation of the Autonomous Commerce "
                "Optimization System against multiple "
                "baseline decision strategies."
            ),
            "",
            (
                f"The benchmark evaluated "
                f"**{total_scenarios} scenarios**, of "
                f"which **{successful_scenarios}** were "
                "processed successfully."
            ),
        ]

        if highest_average_reward:
            strategy, value = (
                highest_average_reward
            )

            lines.append(
                ""
            )

            lines.append(
                f"The highest average reward was "
                f"achieved by **{strategy}** with a "
                f"value of "
                f"**{self._format_number(value)}**."
            )

        if most_reward_wins:
            strategy, value = most_reward_wins

            lines.append("")

            lines.append(
                f"The strategy with the greatest "
                f"number of reward wins was "
                f"**{strategy}**, with "
                f"**{value}** winning scenarios."
            )

        lines.extend(
            [
                "",
                (
                    "The statistical and visualization "
                    "components provide additional "
                    "evidence for comparing strategy "
                    "performance, risk, confidence, and "
                    "execution efficiency."
                ),
            ]
        )

        return "\n".join(lines)

    def _build_experiment_overview(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]
        experiment = data["experiment"]

        rows = {
            "Experiment ID": (
                self._first_non_empty(
                    metadata.get(
                        "experiment_id"
                    ),
                    experiment.get(
                        "experiment_id"
                    ),
                    "Not available",
                )
            ),
            "Experiment name": (
                self._first_non_empty(
                    metadata.get(
                        "experiment_name"
                    ),
                    experiment.get(
                        "experiment_name"
                    ),
                    "Not available",
                )
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
            "Researcher": (
                self._first_non_empty(
                    metadata.get(
                        "researcher_name"
                    ),
                    self.config.author_name,
                )
            ),
            "Institution": (
                self._first_non_empty(
                    metadata.get(
                        "institution_name"
                    ),
                    self.config.institution_name,
                )
            ),
        }

        return (
            "## Experiment Overview\n\n"
            + self._mapping_to_markdown_table(
                rows
            )
        )

    def _build_benchmark_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        lines = [
            "## Benchmark Evaluation",
            "",
            "### Benchmark execution summary",
            "",
        ]

        summary_rows = {
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
            "Benchmark successful": (
                benchmark.get(
                    "successful",
                    False,
                )
            ),
        }

        lines.append(
            self._mapping_to_markdown_table(
                summary_rows
            )
        )

        metric_groups = [
            (
                "Average reward",
                benchmark.get(
                    "average_reward",
                    {},
                ),
            ),
            (
                "Average risk",
                benchmark.get(
                    "average_risk",
                    {},
                ),
            ),
            (
                "Average confidence",
                benchmark.get(
                    "average_confidence",
                    {},
                ),
            ),
            (
                "Average execution time",
                benchmark.get(
                    "average_execution_time",
                    {},
                ),
            ),
            (
                "Reward win frequency",
                benchmark.get(
                    "reward_win_frequency",
                    {},
                ),
            ),
            (
                "Risk win frequency",
                benchmark.get(
                    "risk_win_frequency",
                    {},
                ),
            ),
            (
                "Confidence win frequency",
                benchmark.get(
                    "confidence_win_frequency",
                    {},
                ),
            ),
            (
                "Speed win frequency",
                benchmark.get(
                    "speed_win_frequency",
                    {},
                ),
            ),
            (
                "Agreement with ACOS",
                benchmark.get(
                    "acos_agreement_rate",
                    {},
                ),
            ),
        ]

        for title, values in metric_groups:
            if not values:
                continue

            lines.extend(
                [
                    "",
                    f"### {title}",
                    "",
                    self._strategy_metric_table(
                        values
                    ),
                ]
            )

        return "\n".join(lines)

    def _build_statistical_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        statistics = data["statistics"]

        lines = [
            "## Statistical Evaluation",
            "",
        ]

        if not statistics:
            lines.append(
                "No statistical evaluation result "
                "was available."
            )
            return "\n".join(lines)

        summary = statistics.get(
            "summary",
            {},
        )

        if not summary:
            summary = {
                key: value
                for key, value
                in statistics.items()
                if key
                not in {
                    "pairwise_comparisons",
                    "rankings",
                    "metric_statistics",
                }
                and self._is_scalar(value)
            }

        if summary:
            lines.extend(
                [
                    "### Statistical summary",
                    "",
                    self._mapping_to_markdown_table(
                        summary
                    ),
                ]
            )

        rankings = statistics.get(
            "rankings",
            {},
        ) or {}

        if rankings:
            lines.extend(
                [
                    "",
                    "### Strategy rankings",
                    "",
                ]
            )

            for metric, ranking in (
                rankings.items()
            ):
                lines.append(
                    f"#### {self._humanize(metric)}"
                )
                lines.append("")

                if isinstance(ranking, dict):
                    lines.append(
                        self._strategy_metric_table(
                            ranking
                        )
                    )
                elif isinstance(
                    ranking,
                    list,
                ):
                    lines.append(
                        self._list_to_numbered_text(
                            ranking
                        )
                    )
                else:
                    lines.append(str(ranking))

                lines.append("")

        pairwise = statistics.get(
            "pairwise_comparisons",
            {},
        )

        if pairwise:
            lines.extend(
                [
                    "### Pairwise comparisons",
                    "",
                    (
                        "Pairwise statistical results "
                        "were generated for the benchmark "
                        "strategies. Detailed values are "
                        "preserved in `report_data.json`."
                    ),
                ]
            )

        effect_sizes = statistics.get(
            "effect_sizes",
            {},
        )

        if effect_sizes:
            lines.extend(
                [
                    "",
                    "### Effect sizes",
                    "",
                    self._nested_mapping_summary(
                        effect_sizes
                    ),
                ]
            )

        confidence_intervals = statistics.get(
            "confidence_intervals",
            {},
        )

        if confidence_intervals:
            lines.extend(
                [
                    "",
                    "### Confidence intervals",
                    "",
                    self._nested_mapping_summary(
                        confidence_intervals
                    ),
                ]
            )

        if len(lines) == 2:
            lines.append(
                "Statistical data was included in the "
                "bundle, but no standard summary fields "
                "were detected. The complete result is "
                "available in `report_data.json`."
            )

        return "\n".join(lines)

    def _build_visualization_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        visualizations = data[
            "visualizations"
        ]

        lines = [
            "## Visualizations",
            "",
        ]

        chart_paths = (
            visualizations.get(
                "chart_paths"
            )
            or visualizations.get(
                "generated_charts"
            )
            or visualizations.get(
                "charts"
            )
            or []
        )

        generated_count = visualizations.get(
            "generated_chart_count",
            None,
        )

        if generated_count is None:
            if isinstance(chart_paths, dict):
                generated_count = len(
                    chart_paths
                )
            elif isinstance(chart_paths, list):
                generated_count = len(
                    chart_paths
                )
            else:
                generated_count = 0

        failed_count = visualizations.get(
            "failed_chart_count",
            0,
        )

        lines.append(
            self._mapping_to_markdown_table(
                {
                    "Generated charts": (
                        generated_count
                    ),
                    "Failed charts": failed_count,
                }
            )
        )

        normalized_paths = (
            self._normalize_chart_paths(
                chart_paths
            )
        )

        if normalized_paths:
            lines.extend(
                [
                    "",
                    "### Generated chart files",
                    "",
                ]
            )

            for index, chart in enumerate(
                normalized_paths,
                start=1,
            ):
                title = chart["title"]
                path = chart["path"]

                lines.append(
                    f"{index}. **{title}** — `{path}`"
                )
        else:
            lines.extend(
                [
                    "",
                    (
                        "No chart paths were detected in "
                        "the visualization result."
                    ),
                ]
            )

        return "\n".join(lines)

    def _build_analytics_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        analytics = data["analytics"]

        if analytics is None:
            return (
                "## Analytics\n\n"
                "The analytics result was not included "
                "in this research bundle."
            )

        return (
            "## Analytics\n\n"
            "Analytics data was included in the bundle. "
            "The complete structured analytics result is "
            "available in `report_data.json`.\n\n"
            + self._object_preview_table(
                analytics
            )
        )

    def _build_explainability_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        explainability = data[
            "explainability"
        ]

        if explainability is None:
            return (
                "## Explainability\n\n"
                "The explainability result was not "
                "included in this research bundle."
            )

        return (
            "## Explainability\n\n"
            "Explainability information was included in "
            "the bundle. This evidence supports the "
            "interpretation of ACOS decisions and agent "
            "selection behaviour.\n\n"
            + self._object_preview_table(
                explainability
            )
        )

    def _build_validation_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        validation = data["validation"]

        rows = {
            "Bundle valid": validation.get(
                "valid",
                False,
            ),
            "Error count": len(
                validation.get(
                    "errors",
                    [],
                )
            ),
            "Warning count": len(
                validation.get(
                    "warnings",
                    [],
                )
            ),
        }

        lines = [
            "## Bundle Validation",
            "",
            self._mapping_to_markdown_table(
                rows
            ),
        ]

        errors = validation.get(
            "errors",
            [],
        )

        warnings = validation.get(
            "warnings",
            [],
        )

        if errors:
            lines.extend(
                [
                    "",
                    "### Validation errors",
                    "",
                ]
            )

            lines.extend(
                f"- {error}"
                for error in errors
            )

        if warnings:
            lines.extend(
                [
                    "",
                    "### Validation warnings",
                    "",
                ]
            )

            lines.extend(
                f"- {warning}"
                for warning in warnings
            )

        return "\n".join(lines)

    def _build_reproducibility_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        metadata = data["metadata"]

        rows = {
            "Bundle ID": data["bundle"].get(
                "bundle_id",
                "Not available",
            ),
            "Experiment ID": (
                self._first_non_empty(
                    metadata.get(
                        "experiment_id"
                    ),
                    data["benchmark"].get(
                        "experiment_id"
                    ),
                    "Not available",
                )
            ),
            "Python version": metadata.get(
                "python_version",
                "Not available",
            ),
            "Operating system": metadata.get(
                "operating_system",
                "Not available",
            ),
            "Project version": metadata.get(
                "project_version",
                "Not available",
            ),
            "Framework version": metadata.get(
                "framework_version",
                "Not available",
            ),
        }

        return (
            "## Reproducibility Information\n\n"
            "The following identifiers and environment "
            "details support experiment traceability and "
            "reproduction.\n\n"
            + self._mapping_to_markdown_table(
                rows
            )
        )

    def _build_conclusion_section(
        self,
        data: Dict[str, Any],
    ) -> str:
        benchmark = data["benchmark"]

        average_reward = benchmark.get(
            "average_reward",
            {},
        ) or {}

        average_risk = benchmark.get(
            "average_risk",
            {},
        ) or {}

        fastest = self._best_mapping_entry(
            benchmark.get(
                "average_execution_time",
                {},
            )
            or {},
            highest=False,
        )

        best_reward = self._best_mapping_entry(
            average_reward,
            highest=True,
        )

        lowest_risk = self._best_mapping_entry(
            average_risk,
            highest=False,
        )

        lines = [
            "## Conclusion",
            "",
            (
                "The ACOS experimental pipeline "
                "successfully generated benchmark, "
                "statistical, and visualization evidence "
                "within a validated and reproducible "
                "research bundle."
            ),
        ]

        if best_reward:
            lines.append(
                ""
            )
            lines.append(
                f"The highest observed average reward "
                f"was produced by "
                f"**{best_reward[0]}**."
            )

        if lowest_risk:
            lines.append("")
            lines.append(
                f"The lowest observed average risk was "
                f"produced by "
                f"**{lowest_risk[0]}**."
            )

        if fastest:
            lines.append("")
            lines.append(
                f"The lowest average execution time was "
                f"recorded for "
                f"**{fastest[0]}**."
            )

        lines.extend(
            [
                "",
                (
                    "These findings should be interpreted "
                    "together with the statistical "
                    "comparisons, confidence intervals, "
                    "effect sizes, and scenario-level "
                    "results preserved in the research "
                    "bundle."
                ),
            ]
        )

        return "\n".join(lines)

    def _mapping_to_markdown_table(
        self,
        values: Dict[str, Any],
    ) -> str:
        lines = [
            "| Field | Value |",
            "|---|---|",
        ]

        for key, value in values.items():
            lines.append(
                f"| {self._humanize(str(key))} | "
                f"{self._format_value(value)} |"
            )

        return "\n".join(lines)

    def _strategy_metric_table(
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

    def _object_preview_table(
        self,
        value: Dict[str, Any],
    ) -> str:
        preview = {}

        for key, item in value.items():
            if self._is_scalar(item):
                preview[key] = item

            if len(preview) >= 12:
                break

        if not preview:
            return (
                "The result contains nested structured "
                "data. See `report_data.json` for the "
                "complete representation."
            )

        return self._mapping_to_markdown_table(
            preview
        )

    def _nested_mapping_summary(
        self,
        values: Dict[str, Any],
    ) -> str:
        lines: List[str] = []

        for key, value in values.items():
            lines.append(
                f"#### {self._humanize(str(key))}"
            )
            lines.append("")

            if isinstance(value, dict):
                if all(
                    self._is_scalar(item)
                    for item in value.values()
                ):
                    lines.append(
                        self._strategy_metric_table(
                            value
                        )
                    )
                else:
                    lines.append(
                        "Detailed nested values are "
                        "available in "
                        "`report_data.json`."
                    )
            else:
                lines.append(
                    self._format_value(value)
                )

            lines.append("")

        return "\n".join(lines).strip()

    def _normalize_chart_paths(
        self,
        chart_paths: Any,
    ) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []

        if isinstance(chart_paths, dict):
            for title, path in (
                chart_paths.items()
            ):
                normalized.append(
                    {
                        "title": self._humanize(
                            str(title)
                        ),
                        "path": str(path),
                    }
                )

        elif isinstance(chart_paths, list):
            for index, item in enumerate(
                chart_paths,
                start=1,
            ):
                if isinstance(item, dict):
                    title = (
                        item.get("title")
                        or item.get("name")
                        or item.get("chart_name")
                        or f"Chart {index}"
                    )

                    path = (
                        item.get("path")
                        or item.get("file_path")
                        or item.get("chart_path")
                        or str(item)
                    )
                else:
                    title = f"Chart {index}"
                    path = str(item)

                normalized.append(
                    {
                        "title": str(title),
                        "path": str(path),
                    }
                )

        return normalized

    def _extract_section_titles(
        self,
        markdown: str,
    ) -> List[str]:
        titles = []

        for line in markdown.splitlines():
            stripped = line.strip()

            if stripped.startswith("#"):
                title = stripped.lstrip(
                    "#"
                ).strip()

                if title:
                    titles.append(title)

        return titles

    def _best_mapping_entry(
        self,
        values: Dict[str, Any],
        highest: bool,
    ) -> tuple[str, float] | None:
        numeric_values = {}

        for key, value in values.items():
            try:
                numeric_values[str(key)] = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        if not numeric_values:
            return None

        selector = max if highest else min

        selected_key = selector(
            numeric_values,
            key=numeric_values.get,
        )

        return (
            selected_key,
            numeric_values[selected_key],
        )

    def _safe_summary(
        self,
        value: Any,
    ) -> Dict[str, Any]:
        summary_method = getattr(
            value,
            "summary",
            None,
        )

        if callable(summary_method):
            summary = summary_method()

            if isinstance(summary, dict):
                return self._object_to_dict(
                    summary
                )

        return {}

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

        to_dict_method = getattr(
            value,
            "to_dict",
            None,
        )

        if callable(to_dict_method):
            return self._object_to_dict(
                to_dict_method()
            )

        if hasattr(value, "__dict__"):
            return {
                key: self._object_to_dict(
                    item
                )
                for key, item
                in vars(value).items()
                if not key.startswith("_")
            }

        return value

    def _get_nested_value(
        self,
        value: Any,
        path: Iterable[str],
        default: Any = None,
    ) -> Any:
        current = value

        for name in path:
            current = self._get_value(
                current,
                name,
                None,
            )

            if current is None:
                return default

        return current

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
    def _first_non_empty(
        *values: Any,
    ) -> Any:
        for value in values:
            if value not in (
                None,
                "",
                [],
                {},
            ):
                return value

        return ""

    @staticmethod
    def _is_scalar(
        value: Any,
    ) -> bool:
        return isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
                type(None),
            ),
        )

    def _format_value(
        self,
        value: Any,
    ) -> str:
        if isinstance(value, float):
            return self._format_number(value)

        if isinstance(value, bool):
            return "Yes" if value else "No"

        if value is None:
            return "Not available"

        if isinstance(value, (list, tuple)):
            return ", ".join(
                str(item)
                for item in value
            )

        if isinstance(value, dict):
            return ", ".join(
                f"{key}: {item}"
                for key, item in value.items()
            )

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

    @staticmethod
    def _humanize(
        value: str,
    ) -> str:
        return value.replace(
            "_",
            " ",
        ).strip().title()

    @staticmethod
    def _list_to_numbered_text(
        values: List[Any],
    ) -> str:
        return "\n".join(
            f"{index}. {value}"
            for index, value in enumerate(
                values,
                start=1,
            )
        )