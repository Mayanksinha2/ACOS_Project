from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from publication_generator import (
    PublicationConfig,
    PublicationExporter,
    PublicationGenerator,
)
from report_generator import (
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
        print(f"{key:<32}: {value}")


def build_report():
    """
    Build a temporary research bundle and generate
    a successful research report from it.
    """

    with TemporaryDirectory() as temporary:
        output_directory = (
            Path(temporary)
            / "research_bundle"
        )

        bundle = build_research_bundle(
            output_directory
        )

        report_generator = (
            ResearchReportGenerator()
        )

        report = report_generator.generate(
            bundle
        )

        assert report.successful
        assert report.report_id
        assert report.bundle_id
        assert report.experiment_id
        assert report.markdown_content
        assert report.report_data
        assert not report.errors

        return report


def test_publication_generation() -> None:
    report = build_report()

    config = PublicationConfig(
        publication_format="ieee",
    )

    generator = PublicationGenerator(
        config=config
    )

    publication = generator.generate(
        report
    )

    print_mapping(
        "PUBLICATION GENERATION RESULT",
        publication.to_dict(),
    )

    assert publication.successful
    assert publication.publication_id
    assert publication.report_id
    assert publication.bundle_id
    assert publication.experiment_id
    assert publication.markdown_content
    assert publication.latex_content
    assert publication.section_count > 0

    assert publication.report_id == (
        report.report_id
    )

    assert publication.bundle_id == (
        report.bundle_id
    )

    assert publication.experiment_id == (
        report.experiment_id
    )

    assert "# " in (
        publication.markdown_content
    )

    assert "\\documentclass" in (
        publication.latex_content
    )

    assert not publication.errors


def test_publication_export() -> None:
    report = build_report()

    generator = PublicationGenerator()

    publication = generator.generate(
        report
    )

    assert publication.successful

    with TemporaryDirectory() as temporary:
        output_directory = (
            Path(temporary)
            / "generated_publication"
        )

        exporter = PublicationExporter()

        export_result = exporter.export(
            publication=publication,
            output_directory=output_directory,
        )

        print_mapping(
            "PUBLICATION EXPORT RESULT",
            export_result.to_dict(),
        )

        assert export_result.successful
        assert export_result.publication_id == (
            publication.publication_id
        )

        markdown_path = Path(
            export_result.markdown_path
        )

        latex_path = Path(
            export_result.latex_path
        )

        manifest_path = Path(
            export_result.manifest_path
        )

        data_path = Path(
            export_result.data_path
        )

        assert markdown_path.exists()
        assert latex_path.exists()
        assert manifest_path.exists()
        assert data_path.exists()

        assert markdown_path.is_file()
        assert latex_path.is_file()
        assert manifest_path.is_file()
        assert data_path.is_file()

        assert markdown_path.read_text(
            encoding="utf-8"
        ) == publication.markdown_content

        assert latex_path.read_text(
            encoding="utf-8"
        ) == publication.latex_content

        assert not export_result.errors


def test_invalid_report() -> None:
    generator = PublicationGenerator()

    publication = generator.generate(
        None
    )

    assert not publication.successful
    assert publication.errors
    assert not publication.markdown_content
    assert not publication.latex_content


def run_tests() -> None:
    test_publication_generation()
    test_publication_export()
    test_invalid_report()

    print()
    print(
        "Publication Generator Framework "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()