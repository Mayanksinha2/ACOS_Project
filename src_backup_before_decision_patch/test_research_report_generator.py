from __future__ import annotations

import tempfile
from pathlib import Path

from report_generator import (
    ReportConfig,
    ReportExporter,
    ResearchReportGenerator,
)
from test_research_bundle import (
    build_research_bundle,
)


def print_mapping(
    title: str,
    values: dict,
) -> None:
    print()
    print(title)
    print("-" * 90)

    for key, value in values.items():
        print(
            f"{key:<32}: {value}"
        )


def test_report_generation() -> None:
    with tempfile.TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        config = ReportConfig(
            report_title=(
                "Autonomous Commerce "
                "Optimization System"
            ),
            report_subtitle=(
                "Benchmark and Statistical "
                "Evaluation Report"
            ),
            author_name="M.Tech Researcher",
            institution_name=(
                "Research Institution"
            ),
        )

        generator = ResearchReportGenerator(
            config=config
        )


        report = generator.generate(
            bundle
        )

        assert report.successful
        assert report.markdown_content
        assert report.bundle_id
        assert report.experiment_id

        assert (
            report.experiment_id
            == bundle.metadata.experiment_id
        )

        assert "# Autonomous Commerce" in (
            report.markdown_content
        )

        assert "## Executive Summary" in (
            report.markdown_content
        )

        assert "## Benchmark Evaluation" in (
            report.markdown_content
        )

        assert "## Statistical Evaluation" in (
            report.markdown_content
        )

        assert "## Visualizations" in (
            report.markdown_content
        )

        assert "## Bundle Validation" in (
            report.markdown_content
        )

        assert "## Conclusion" in (
            report.markdown_content
        )

        print_mapping(
            "REPORT GENERATION RESULT",
            report.summary(),
        )


def test_report_export() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        bundle = build_research_bundle(
            root
        )

        report = ResearchReportGenerator(
            ReportConfig(
                author_name=(
                    "M.Tech Researcher"
                ),
                institution_name=(
                    "Research Institution"
                ),
            )
        ).generate(
            bundle
        )

        export_directory = (
            root
            / "generated_report"
        )

        export_result = ReportExporter().export(
            report_result=report,
            output_directory=export_directory,
            report_name="acos_research_report",
        )

        assert export_result.successful

        assert export_result.markdown_path
        assert export_result.manifest_path
        assert export_result.data_path

        assert Path(
            export_result.markdown_path
        ).exists()

        assert Path(
            export_result.manifest_path
        ).exists()

        assert Path(
            export_result.data_path
        ).exists()

        markdown_content = Path(
            export_result.markdown_path
        ).read_text(
            encoding="utf-8"
        )

        assert "Benchmark Evaluation" in (
            markdown_content
        )

        print_mapping(
            "REPORT EXPORT RESULT",
            export_result.summary(),
        )


def test_invalid_bundle() -> None:
    report = ResearchReportGenerator().generate(
        None
    )

    assert not report.successful
    assert report.errors


def test_report_section_inventory() -> None:
    with tempfile.TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        report = ResearchReportGenerator().generate(
            bundle
        )

        expected_sections = [
            "Executive Summary",
            "Experiment Overview",
            "Benchmark Evaluation",
            "Statistical Evaluation",
            "Visualizations",
            "Analytics",
            "Explainability",
            "Bundle Validation",
            "Reproducibility Information",
            "Conclusion",
        ]

        for section in expected_sections:
            assert section in (
                report.section_titles
            )


def run_tests() -> None:
    test_report_generation()
    test_report_export()
    test_invalid_bundle()
    test_report_section_inventory()

    print()
    print(
        "Research Report Generator "
        "Framework tests passed."
    )


if __name__ == "__main__":
    run_tests()