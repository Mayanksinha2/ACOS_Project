from pathlib import Path
from tempfile import TemporaryDirectory

from benchmarking.benchmark_engine import (
    BenchmarkEngine,
)
from experiments.experiment_runner import (
    ExperimentRunner,
)
from research_bundle.bundle_exporter import (
    BundleExporter,
)
from research_bundle.bundle_validator import (
    BundleValidator,
)
from research_bundle.research_bundle_builder import (
    ResearchBundleBuilder,
)
from simulator.scenario_generator import (
    ScenarioGenerator,
)
from statistics_engine.statistical_evaluation_engine import (
    StatisticalEvaluationEngine,
)
from visualization_engine.visualization_engine import (
    VisualizationEngine,
)


def build_research_bundle(
    output_directory: str,
):
    generator = ScenarioGenerator(
        random_seed=2026
    )

    experiment = ExperimentRunner(
        scenario_generator=generator
    ).run_random_experiment(
        scenario_count=20,
        customer_count=100,
        experiment_name=(
            "ACOS Research Bundle Test"
        ),
    )

    benchmark_result = BenchmarkEngine(
        random_seed=2026
    ).benchmark_experiment(
        experiment
    )

    statistical_result = (
        StatisticalEvaluationEngine()
        .evaluate(
            benchmark_result
        )
    )

    visualization_result = (
        VisualizationEngine(
            output_root=(
                f"{output_directory}/"
                "visualizations"
            ),
            dpi=120,
        ).generate_all(
            benchmark_result=(
                benchmark_result
            ),
            statistical_result=(
                statistical_result
            ),
        )
    )
    

    bundle = ResearchBundleBuilder(
        project_version="1.0.0",
        framework_version="1.0.0",
        researcher_name="ACOS Researcher",
        institution_name=(
            "M.Tech Research Project"
        ),
    ).build(
        experiment=experiment,
        benchmark_result=benchmark_result,
        statistical_result=(
            statistical_result
        ),
        visualization_result=(
            visualization_result
        ),
        random_seed=2026,
        additional_metadata={
            "research_domain": (
                "Autonomous E-commerce "
                "Optimization"
            ),
            "decision_method": "MOCRA",
            "negotiation_enabled": True,
        },
    )

    return bundle


def print_bundle_result(
    bundle,
) -> None:
    print(
        "\nACOS RESEARCH BUNDLE"
    )

    print("=" * 90)

    for key, value in (
        bundle.summary().items()
    ):
        print(f"{key:<32}: {value}")

    validation = bundle.validate()

    print(
        "\nVALIDATION"
    )

    print("-" * 90)

    for key, value in (
        validation.to_dict().items()
    ):
        print(f"{key:<32}: {value}")


def test_bundle_builder() -> None:
    with TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        print_bundle_result(bundle)

        assert bundle is not None
        assert bundle.metadata.bundle_id
        assert bundle.metadata.experiment_id
        assert (
            bundle.metadata.experiment_name
            == "ACOS Research Bundle Test"
        )

        assert bundle.experiment is not None

        assert (
            bundle.benchmark_result
            is not None
        )

        assert (
            bundle.statistical_result
            is not None
        )

        assert (
            bundle.visualization_result
            is not None
        )

        assert (
            bundle.analytics_result
            is None
        )

        assert (
            bundle.explainability_result
            is None
        )


def test_bundle_validation() -> None:
    with TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        validation = BundleValidator().validate(
            bundle
        )

        assert validation.valid
        assert validation.error_count == 0

        assert validation.warning_count == 2

        assert (
            "Analytics result is not included."
            in validation.warnings
        )

        assert (
            "Explainability result is not "
            "included."
            in validation.warnings
        )


def test_bundle_export() -> None:
    with TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        exporter = BundleExporter(
            output_root=(
                f"{directory}/bundles"
            )
        )

        export_result = exporter.export(
            bundle=bundle,
            bundle_name=(
                "acos_test_bundle"
            ),
            include_pickle=True,
            create_archive=True,
        )

        print(
            "\nEXPORT RESULT"
        )

        print("-" * 90)

        for key, value in (
            export_result.items()
        ):
            print(f"{key:<32}: {value}")

        assert export_result[
            "successful"
        ]

        output_directory = Path(
            export_result[
                "output_directory"
            ]
        )

        assert output_directory.exists()

        expected_files = {
            "bundle.json",
            "summary.json",
            "validation.json",
            "bundle.pkl",
        }

        actual_files = {
            file_path.name
            for file_path
            in output_directory.iterdir()
            if file_path.is_file()
        }

        assert expected_files.issubset(
            actual_files
        )

        assert Path(
            export_result["archive_path"]
        ).exists()

        loaded_json = exporter.load_json(
            export_result["json_path"]
        )

        assert (
            loaded_json["metadata"][
                "bundle_id"
            ]
            == bundle.metadata.bundle_id
        )

        loaded_bundle = exporter.load_pickle(
            export_result["pickle_path"]
        )

        assert (
            loaded_bundle.metadata.bundle_id
            == bundle.metadata.bundle_id
        )

        assert (
            loaded_bundle.validate().valid
        )


def test_invalid_bundle() -> None:
    with TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        bundle.statistical_result = None

        validation = bundle.validate()

        assert not validation.valid

        assert validation.error_count >= 1

        assert any(
            "statistical_result"
            in error
            for error in validation.errors
        )


def test_summary_serialization() -> None:
    with TemporaryDirectory() as directory:
        bundle = build_research_bundle(
            directory
        )

        summary = bundle.summary()

        assert summary["valid"]
        assert summary["bundle_id"]
        assert (
            summary["experiment_name"]
            == "ACOS Research Bundle Test"
        )

        serialized = bundle.to_dict(
            include_full_results=False
        )

        assert "metadata" in serialized
        assert "summary" in serialized

        assert (
            "benchmark_result"
            not in serialized
        )


def run_tests() -> None:
    test_bundle_builder()
    test_bundle_validation()
    test_bundle_export()
    test_invalid_bundle()
    test_summary_serialization()

    print(
        "\nResearch Bundle Framework "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()