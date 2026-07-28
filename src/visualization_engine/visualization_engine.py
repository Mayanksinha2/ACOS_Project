from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from benchmarking.benchmark_result import (
    BenchmarkExperimentResult,
)
from statistics_engine.statistical_result import (
    StatisticalEvaluationResult,
)
from visualization_engine.visualization_result import (
    GeneratedChart,
    VisualizationResult,
)


class VisualizationEngine:
    """
    Generates publication-ready visualizations
    from ACOS benchmark and statistical results.
    """

    DEFAULT_DPI = 300

    def __init__(
        self,
        output_root: str = "outputs/visualizations",
        dpi: int = DEFAULT_DPI,
    ) -> None:
        self.output_root = Path(output_root)
        self.dpi = dpi

    def generate_all(
        self,
        benchmark_result: BenchmarkExperimentResult,
        statistical_result: StatisticalEvaluationResult,
    ) -> VisualizationResult:
        output_directory = self._build_output_directory(
            experiment_id=str(
                benchmark_result.experiment_id
            ),
            experiment_name=str(
                benchmark_result.experiment_name
            ),
        )

        result = VisualizationResult(
            experiment_id=str(
                benchmark_result.experiment_id
            ),
            experiment_name=str(
                benchmark_result.experiment_name
            ),
            output_directory=str(
                output_directory.resolve()
            ),
        )

        chart_generators = [
            lambda: self._generate_metric_bar_chart(
                statistical_result=statistical_result,
                metric_name="reward",
                output_directory=output_directory,
                title=(
                    "Average Reward by Strategy"
                ),
                y_label="Average Reward",
            ),
            lambda: self._generate_metric_bar_chart(
                statistical_result=statistical_result,
                metric_name="risk",
                output_directory=output_directory,
                title=(
                    "Average Risk by Strategy"
                ),
                y_label="Average Risk",
            ),
            lambda: self._generate_metric_bar_chart(
                statistical_result=statistical_result,
                metric_name="confidence",
                output_directory=output_directory,
                title=(
                    "Average Confidence by Strategy"
                ),
                y_label="Average Confidence",
            ),
            lambda: self._generate_metric_bar_chart(
                statistical_result=statistical_result,
                metric_name=(
                    "execution_time_seconds"
                ),
                output_directory=output_directory,
                title=(
                    "Average Execution Time "
                    "by Strategy"
                ),
                y_label="Execution Time (seconds)",
            ),
            lambda: (
                self._generate_confidence_interval_chart(
                    statistical_result=statistical_result,
                    metric_name="reward",
                    output_directory=output_directory,
                    title=(
                        "Reward Mean and "
                        "95% Confidence Interval"
                    ),
                    y_label="Reward",
                )
            ),
            lambda: self._generate_win_frequency_chart(
                benchmark_result=benchmark_result,
                frequency_attribute=(
                    "reward_win_frequency"
                ),
                output_directory=output_directory,
                chart_name=(
                    "reward_win_frequency"
                ),
                title=(
                    "Reward Win Frequency "
                    "by Strategy"
                ),
                y_label="Number of Scenario Wins",
            ),
            lambda: self._generate_win_frequency_chart(
                benchmark_result=benchmark_result,
                frequency_attribute=(
                    "risk_win_frequency"
                ),
                output_directory=output_directory,
                chart_name="risk_win_frequency",
                title=(
                    "Risk Win Frequency "
                    "by Strategy"
                ),
                y_label="Number of Scenario Wins",
            ),
            lambda: self._generate_effect_size_chart(
                statistical_result=statistical_result,
                metric_name="reward",
                output_directory=output_directory,
                title=(
                    "ACOS Reward Effect Size "
                    "Against Baselines"
                ),
            ),
        ]

        for generator in chart_generators:
            try:
                chart = generator()
                result.charts.append(chart)

                if not chart.successful:
                    result.errors.append(
                        chart.error
                        or (
                            f"Failed to generate "
                            f"{chart.chart_name}."
                        )
                    )

            except Exception as error:
                result.errors.append(
                    f"{type(error).__name__}: "
                    f"{error}"
                )

        result.successful = (
            result.failed_chart_count == 0
            and len(result.errors) == 0
        )

        return result

    def _generate_metric_bar_chart(
        self,
        statistical_result: StatisticalEvaluationResult,
        metric_name: str,
        output_directory: Path,
        title: str,
        y_label: str,
    ) -> GeneratedChart:
        statistics_by_strategy = (
            statistical_result
            .descriptive_statistics
            .get(metric_name, {})
        )

        chart_name = (
            f"{metric_name}_strategy_comparison"
        )

        file_path = (
            output_directory
            / f"{chart_name}.png"
        )

        if not statistics_by_strategy:
            return self._failed_chart(
                chart_name=chart_name,
                chart_type="bar",
                metric_name=metric_name,
                file_path=file_path,
                title=title,
                error=(
                    f"No descriptive statistics "
                    f"available for {metric_name}."
                ),
            )

        strategy_names = list(
            statistics_by_strategy.keys()
        )

        means = [
            statistics_by_strategy[
                strategy_name
            ].mean
            for strategy_name in strategy_names
        ]

        figure, axis = plt.subplots(
            figsize=(10, 6)
        )

        bars = axis.bar(
            strategy_names,
            means,
        )

        axis.set_title(
            title,
            fontsize=14,
            fontweight="bold",
        )

        axis.set_xlabel("Strategy")
        axis.set_ylabel(y_label)

        axis.grid(
            axis="y",
            alpha=0.25,
        )

        axis.tick_params(
            axis="x",
            rotation=15,
        )

        self._add_bar_labels(
            axis=axis,
            bars=bars,
            precision=6,
        )

        figure.tight_layout()

        self._save_and_close(
            figure=figure,
            file_path=file_path,
        )

        return GeneratedChart(
            chart_name=chart_name,
            chart_type="bar",
            metric_name=metric_name,
            file_path=str(file_path.resolve()),
            title=title,
            metadata={
                "strategies": strategy_names,
                "values": means,
            },
        )

    def _generate_confidence_interval_chart(
        self,
        statistical_result: StatisticalEvaluationResult,
        metric_name: str,
        output_directory: Path,
        title: str,
        y_label: str,
    ) -> GeneratedChart:
        statistics_by_strategy = (
            statistical_result
            .descriptive_statistics
            .get(metric_name, {})
        )

        chart_name = (
            f"{metric_name}_confidence_intervals"
        )

        file_path = (
            output_directory
            / f"{chart_name}.png"
        )

        if not statistics_by_strategy:
            return self._failed_chart(
                chart_name=chart_name,
                chart_type="errorbar",
                metric_name=metric_name,
                file_path=file_path,
                title=title,
                error=(
                    f"No confidence interval data "
                    f"available for {metric_name}."
                ),
            )

        strategy_names = list(
            statistics_by_strategy.keys()
        )

        means: List[float] = []
        lower_errors: List[float] = []
        upper_errors: List[float] = []

        for strategy_name in strategy_names:
            statistics = (
                statistics_by_strategy[
                    strategy_name
                ]
            )

            means.append(statistics.mean)

            lower_errors.append(
                max(
                    0.0,
                    statistics.mean
                    - (
                        statistics
                        .confidence_interval_lower
                    ),
                )
            )

            upper_errors.append(
                max(
                    0.0,
                    (
                        statistics
                        .confidence_interval_upper
                    )
                    - statistics.mean,
                )
            )

        x_positions = list(
            range(len(strategy_names))
        )

        figure, axis = plt.subplots(
            figsize=(10, 6)
        )

        axis.errorbar(
            x_positions,
            means,
            yerr=[
                lower_errors,
                upper_errors,
            ],
            fmt="o",
            capsize=6,
            markersize=7,
        )

        axis.set_xticks(
            x_positions
        )

        axis.set_xticklabels(
            strategy_names,
            rotation=15,
        )

        axis.set_title(
            title,
            fontsize=14,
            fontweight="bold",
        )

        axis.set_xlabel("Strategy")
        axis.set_ylabel(y_label)

        axis.grid(
            axis="y",
            alpha=0.25,
        )

        figure.tight_layout()

        self._save_and_close(
            figure=figure,
            file_path=file_path,
        )

        return GeneratedChart(
            chart_name=chart_name,
            chart_type="errorbar",
            metric_name=metric_name,
            file_path=str(file_path.resolve()),
            title=title,
            metadata={
                "strategies": strategy_names,
                "means": means,
                "lower_errors": lower_errors,
                "upper_errors": upper_errors,
            },
        )

    def _generate_win_frequency_chart(
        self,
        benchmark_result: BenchmarkExperimentResult,
        frequency_attribute: str,
        output_directory: Path,
        chart_name: str,
        title: str,
        y_label: str,
    ) -> GeneratedChart:
        file_path = (
            output_directory
            / f"{chart_name}.png"
        )

        frequency = getattr(
            benchmark_result,
            frequency_attribute,
            None,
        )

        if not frequency:
            return self._failed_chart(
                chart_name=chart_name,
                chart_type="bar",
                metric_name=None,
                file_path=file_path,
                title=title,
                error=(
                    f"No data available for "
                    f"{frequency_attribute}."
                ),
            )

        strategy_names = list(
            frequency.keys()
        )

        win_counts = [
            frequency[strategy_name]
            for strategy_name in strategy_names
        ]

        figure, axis = plt.subplots(
            figsize=(10, 6)
        )

        bars = axis.bar(
            strategy_names,
            win_counts,
        )

        axis.set_title(
            title,
            fontsize=14,
            fontweight="bold",
        )

        axis.set_xlabel("Strategy")
        axis.set_ylabel(y_label)

        axis.grid(
            axis="y",
            alpha=0.25,
        )

        axis.tick_params(
            axis="x",
            rotation=15,
        )

        self._add_bar_labels(
            axis=axis,
            bars=bars,
            precision=0,
        )

        figure.tight_layout()

        self._save_and_close(
            figure=figure,
            file_path=file_path,
        )

        return GeneratedChart(
            chart_name=chart_name,
            chart_type="bar",
            metric_name=None,
            file_path=str(file_path.resolve()),
            title=title,
            metadata={
                "strategies": strategy_names,
                "win_counts": win_counts,
            },
        )

    def _generate_effect_size_chart(
        self,
        statistical_result: StatisticalEvaluationResult,
        metric_name: str,
        output_directory: Path,
        title: str,
    ) -> GeneratedChart:
        comparisons = (
            statistical_result
            .pairwise_comparisons
            .get(metric_name, {})
        )

        chart_name = (
            f"{metric_name}_effect_sizes"
        )

        file_path = (
            output_directory
            / f"{chart_name}.png"
        )

        if not comparisons:
            return self._failed_chart(
                chart_name=chart_name,
                chart_type="bar",
                metric_name=metric_name,
                file_path=file_path,
                title=title,
                error=(
                    f"No pairwise comparisons "
                    f"available for {metric_name}."
                ),
            )

        baseline_names = list(
            comparisons.keys()
        )

        effect_sizes = [
            comparisons[
                baseline_name
            ].effect_size
            for baseline_name in baseline_names
        ]

        figure, axis = plt.subplots(
            figsize=(10, 6)
        )

        bars = axis.bar(
            baseline_names,
            effect_sizes,
        )

        axis.axhline(
            y=0.0,
            linewidth=1.0,
        )

        axis.axhline(
            y=0.2,
            linestyle="--",
            linewidth=0.8,
        )

        axis.axhline(
            y=-0.2,
            linestyle="--",
            linewidth=0.8,
        )

        axis.axhline(
            y=0.5,
            linestyle="--",
            linewidth=0.8,
        )

        axis.axhline(
            y=-0.5,
            linestyle="--",
            linewidth=0.8,
        )

        axis.axhline(
            y=0.8,
            linestyle="--",
            linewidth=0.8,
        )

        axis.axhline(
            y=-0.8,
            linestyle="--",
            linewidth=0.8,
        )

        axis.set_title(
            title,
            fontsize=14,
            fontweight="bold",
        )

        axis.set_xlabel("Baseline Strategy")
        axis.set_ylabel(
            "Paired Cohen's d "
            "(Positive Favors ACOS)"
        )

        axis.grid(
            axis="y",
            alpha=0.25,
        )

        axis.tick_params(
            axis="x",
            rotation=15,
        )

        self._add_bar_labels(
            axis=axis,
            bars=bars,
            precision=4,
        )

        figure.tight_layout()

        self._save_and_close(
            figure=figure,
            file_path=file_path,
        )

        return GeneratedChart(
            chart_name=chart_name,
            chart_type="bar",
            metric_name=metric_name,
            file_path=str(file_path.resolve()),
            title=title,
            metadata={
                "baselines": baseline_names,
                "effect_sizes": effect_sizes,
            },
        )

    def _build_output_directory(
        self,
        experiment_id: str,
        experiment_name: str,
    ) -> Path:
        safe_experiment_name = (
            self._sanitize_filename(
                experiment_name
            )
        )

        safe_experiment_id = (
            self._sanitize_filename(
                experiment_id
            )
        )

        output_directory = (
            self.output_root
            / (
                f"{safe_experiment_name}_"
                f"{safe_experiment_id}"
            )
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output_directory

    @staticmethod
    def _sanitize_filename(
        value: str,
    ) -> str:
        cleaned = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            str(value).strip(),
        )

        cleaned = cleaned.strip(
            "._-"
        )

        return cleaned or "acos_experiment"

    def _save_and_close(
        self,
        figure,
        file_path: Path,
    ) -> None:
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        figure.savefig(
            file_path,
            dpi=self.dpi,
            bbox_inches="tight",
        )

        plt.close(figure)

    @staticmethod
    def _add_bar_labels(
        axis,
        bars: Iterable,
        precision: int,
    ) -> None:
        for bar in bars:
            height = bar.get_height()

            if not math.isfinite(
                float(height)
            ):
                continue

            if precision == 0:
                label = str(
                    int(round(height))
                )
            else:
                label = (
                    f"{height:.{precision}f}"
                ).rstrip("0").rstrip(".")

            vertical_alignment = (
                "bottom"
                if height >= 0
                else "top"
            )

            offset = (
                3
                if height >= 0
                else -3
            )

            axis.annotate(
                label,
                xy=(
                    bar.get_x()
                    + bar.get_width() / 2,
                    height,
                ),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                va=vertical_alignment,
                fontsize=8,
            )

    @staticmethod
    def _failed_chart(
        chart_name: str,
        chart_type: str,
        metric_name: Optional[str],
        file_path: Path,
        title: str,
        error: str,
    ) -> GeneratedChart:
        return GeneratedChart(
            chart_name=chart_name,
            chart_type=chart_type,
            metric_name=metric_name,
            file_path=str(file_path.resolve()),
            title=title,
            successful=False,
            error=error,
        )