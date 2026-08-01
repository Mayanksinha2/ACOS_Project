from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from publication_generator import (
    PublicationExporter,
    PublicationGenerator,
)
from report_generator import (
    ReportExporter,
    ResearchReportGenerator,
)
from test_research_bundle import (
    build_research_bundle,
)

from .experiment_request import ExperimentRequest
from .utils import first_non_empty, get_value


@dataclass(slots=True)
class ACOSExperimentExecutionResult:
    """
    Normalized execution result returned by the real
    ACOS experiment adapter.

    The ExperimentRunner converts this object into the
    standard ExperimentResult used by ExperimentManager.
    """

    successful: bool = False

    reward: float | None = None
    decision: Any = None

    conflict_detected: bool = False
    negotiation_required: bool = False

    bundle_path: str = ""
    report_path: str = ""
    publication_path: str = ""
    output_directory: str = ""

    bundle: Any = None
    report: Any = None
    publication: Any = None

    warnings: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )


def execute_acos_experiment(
    request: ExperimentRequest,
    run_index: int,
    random_seed: int | None,
) -> ACOSExperimentExecutionResult:
    """
    Execute one real ACOS research experiment.

    Current pipeline:

        build_research_bundle()
                ↓
        ResearchReportGenerator
                ↓
        ReportExporter
                ↓
        PublicationGenerator
                ↓
        PublicationExporter

    Every run receives an isolated output directory.
    """

    result = ACOSExperimentExecutionResult()

    try:
        run_directory = _build_run_directory(
            request=request,
            run_index=run_index,
        )

        result.output_directory = str(
            run_directory
        )

        bundle_directory = (
            run_directory
            / "research_bundle"
        )

        report_directory = (
            run_directory
            / "research_report"
        )

        publication_directory = (
            run_directory
            / "publication"
        )

        # -------------------------------------------------
        # 1. Execute the real ACOS research pipeline
        # -------------------------------------------------

        bundle = build_research_bundle(
            bundle_directory
        )

        if bundle is None:
            result.errors.append(
                "build_research_bundle() returned None."
            )
            return result

        result.bundle = bundle
        result.bundle_path = str(
            bundle_directory
        )

        result.warnings.extend(
            _extract_warnings(bundle)
        )

        result.errors.extend(
            _extract_errors(bundle)
        )

        # -------------------------------------------------
        # 2. Extract experiment-level research values
        # -------------------------------------------------

        experiment = get_value(
            bundle,
            "experiment",
            None,
        )

        benchmark_result = get_value(
            bundle,
            "benchmark_result",
            None,
        )

        result.reward = _extract_reward(
            experiment=experiment,
            benchmark_result=benchmark_result,
        )

        result.decision = _extract_decision(
            experiment
        )

        result.conflict_detected = (
            _extract_conflict_detected(
                experiment
            )
        )

        result.negotiation_required = (
            _extract_negotiation_required(
                experiment
            )
        )

        # -------------------------------------------------
        # 3. Generate the research report
        # -------------------------------------------------

        report = None

        if (
            request.config.save_report
            or request.config.save_publication
        ):
            report_generator = (
                ResearchReportGenerator()
            )

            report = report_generator.generate(
                bundle
            )

            result.report = report

            result.warnings.extend(
                _extract_warnings(report)
            )

            result.errors.extend(
                _extract_errors(report)
            )

            report_successful = bool(
                get_value(
                    report,
                    "successful",
                    False,
                )
            )

            if not report_successful:
                result.errors.append(
                    "Research report generation failed."
                )

            elif request.config.save_report:
                # -----------------------------------------
                # Export the generated report
                # -----------------------------------------

                report_exporter = (
                    ReportExporter()
                )

                report_export_result = (
                    report_exporter.export(
                        report,
                        report_directory,
                    )
                )

                result.warnings.extend(
                    _extract_warnings(
                        report_export_result
                    )
                )

                result.errors.extend(
                    _extract_errors(
                        report_export_result
                    )
                )

                report_export_successful = bool(
                    get_value(
                        report_export_result,
                        "successful",
                        False,
                    )
                )

                if report_export_successful:
                    result.report_path = str(
                        first_non_empty(
                            get_value(
                                report_export_result,
                                "markdown_path",
                                None,
                            ),
                            report_directory,
                        )
                    )

                else:
                    result.errors.append(
                        "Research report export failed."
                    )

        # -------------------------------------------------
        # 4. Generate and export the publication
        # -------------------------------------------------

        if request.config.save_publication:
            if report is None:
                result.errors.append(
                    "Publication generation requires "
                    "a research report."
                )

            elif not bool(
                get_value(
                    report,
                    "successful",
                    False,
                )
            ):
                result.errors.append(
                    "Publication generation skipped "
                    "because research report generation "
                    "was unsuccessful."
                )

            else:
                publication_generator = (
                    PublicationGenerator()
                )

                publication = (
                    publication_generator.generate(
                        report
                    )
                )

                result.publication = publication

                result.warnings.extend(
                    _extract_warnings(
                        publication
                    )
                )

                result.errors.extend(
                    _extract_errors(
                        publication
                    )
                )

                publication_successful = bool(
                    get_value(
                        publication,
                        "successful",
                        False,
                    )
                )

                if not publication_successful:
                    result.errors.append(
                        "Publication generation failed."
                    )

                else:
                    publication_exporter = (
                        PublicationExporter()
                    )

                    publication_export_result = (
                        publication_exporter.export(
                            publication,
                            publication_directory,
                        )
                    )

                    result.warnings.extend(
                        _extract_warnings(
                            publication_export_result
                        )
                    )

                    result.errors.extend(
                        _extract_errors(
                            publication_export_result
                        )
                    )

                    publication_export_successful = bool(
                        get_value(
                            publication_export_result,
                            "successful",
                            False,
                        )
                    )

                    if publication_export_successful:
                        result.publication_path = str(
                            first_non_empty(
                                get_value(
                                    publication_export_result,
                                    "markdown_path",
                                    None,
                                ),
                                publication_directory,
                            )
                        )

                    else:
                        result.errors.append(
                            "Publication export failed."
                        )

        # -------------------------------------------------
        # 5. Final normalization
        # -------------------------------------------------

        result.warnings = _remove_duplicates(
            result.warnings
        )

        result.errors = _remove_duplicates(
            result.errors
        )

        result.successful = not result.errors

        return result

    except Exception as error:
        result.successful = False

        result.errors.append(
            f"{type(error).__name__}: {error}"
        )

        result.errors = _remove_duplicates(
            result.errors
        )

        return result


def _build_run_directory(
    request: ExperimentRequest,
    run_index: int,
) -> Path:
    """
    Create an isolated directory for every experiment run.

    Directory format:

        <root>/
            <experiment_id>/
                run_001/
                run_002/
                ...
    """

    if request.output_directory:
        root_directory = Path(
            request.output_directory
        )
    else:
        root_directory = Path(
            "experiment_outputs"
        )

    run_directory = (
        root_directory
        / request.experiment_id
        / f"run_{run_index:03d}"
    )

    run_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return run_directory


def _extract_reward(
    experiment: Any,
    benchmark_result: Any,
) -> float | None:
    """
    Extract the reward from the available experiment
    or benchmark result structures.
    """

    scenario_results = get_value(
        experiment,
        "scenario_results",
        [],
    )

    rewards: list[float] = []

    if scenario_results:
        for scenario_result in scenario_results:
            run_result = get_value(
                scenario_result,
                "run_result",
                None,
            )

            outcome_result = get_value(
                run_result,
                "outcome_result",
                None,
            )

            evaluation_result = get_value(
                run_result,
                "evaluation_result",
                None,
            )

            scenario_reward = first_non_empty(
                get_value(
                    scenario_result,
                    "reward",
                    None,
                ),
                get_value(
                    run_result,
                    "reward",
                    None,
                ),
                get_value(
                    run_result,
                    "final_reward",
                    None,
                ),
                get_value(
                    outcome_result,
                    "reward",
                    None,
                ),
                get_value(
                    evaluation_result,
                    "reward",
                    None,
                ),
            )

            if scenario_reward is not None:
                try:
                    rewards.append(
                        float(scenario_reward)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

    if rewards:
        return sum(rewards) / len(rewards)

    experiment_outcome = get_value(
        experiment,
        "outcome",
        None,
    )

    experiment_outcome_result = get_value(
        experiment,
        "outcome_result",
        None,
    )

    value = first_non_empty(
        get_value(
            experiment,
            "reward",
            None,
        ),
        get_value(
            experiment,
            "final_reward",
            None,
        ),
        get_value(
            experiment,
            "average_reward",
            None,
        ),
        get_value(
            experiment_outcome,
            "reward",
            None,
        ),
        get_value(
            experiment_outcome_result,
            "reward",
            None,
        ),
        get_value(
            benchmark_result,
            "reward",
            None,
        ),
        get_value(
            benchmark_result,
            "average_reward",
            None,
        ),
        get_value(
            benchmark_result,
            "mean_reward",
            None,
        ),
    )

    if value is None:
        return None

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def _extract_decision(
    experiment: Any,
) -> Any:
    """
    Extract the final decision from an experiment.

    Supports both direct experiment fields and nested
    scenario-run result structures.
    """

    scenario_results = get_value(
        experiment,
        "scenario_results",
        [],
    )

    if scenario_results:
        first_scenario = scenario_results[0]

        run_result = get_value(
            first_scenario,
            "run_result",
            None,
        )

        execution_result = get_value(
            run_result,
            "execution_result",
            None,
        )

        decision_result = get_value(
            run_result,
            "decision_result",
            None,
        )

        negotiation_result = get_value(
            run_result,
            "negotiation_result",
            None,
        )

        selected_decision = first_non_empty(
            get_value(
                run_result,
                "final_decision",
                None,
            ),
            get_value(
                run_result,
                "selected_decision",
                None,
            ),
            get_value(
                execution_result,
                "decision",
                None,
            ),
            get_value(
                decision_result,
                "decision",
                None,
            ),
            get_value(
                negotiation_result,
                "final_operation",
                None,
            ),
            decision_result,
        )

        if selected_decision is not None:
            return selected_decision

    execution_result = get_value(
        experiment,
        "execution_result",
        None,
    )

    decision_result = get_value(
        experiment,
        "decision_result",
        None,
    )

    return first_non_empty(
        get_value(
            experiment,
            "final_decision",
            None,
        ),
        get_value(
            experiment,
            "decision",
            None,
        ),
        get_value(
            experiment,
            "selected_decision",
            None,
        ),
        get_value(
            execution_result,
            "decision",
            None,
        ),
        get_value(
            decision_result,
            "decision",
            None,
        ),
        decision_result,
    )


def _extract_conflict_detected(
    experiment: Any,
) -> bool:
    """
    Return True when at least one real conflict exists.
    """

    scenario_results = get_value(
        experiment,
        "scenario_results",
        [],
    )

    if scenario_results:
        for scenario_result in scenario_results:
            run_result = get_value(
                scenario_result,
                "run_result",
                None,
            )

            conflicts = get_value(
                run_result,
                "conflicts",
                [],
            )

            if conflicts:
                for conflict in conflicts:
                    conflict_type = str(
                        get_value(
                            conflict,
                            "conflict_type",
                            "",
                        )
                    ).upper()

                    requires_negotiation = bool(
                        get_value(
                            conflict,
                            "requires_negotiation",
                            False,
                        )
                    )

                    if (
                        requires_negotiation
                        or conflict_type
                        not in {
                            "",
                            "SUPPORTING",
                            "NO_CONFLICT",
                        }
                    ):
                        return True

            direct_conflict = first_non_empty(
                get_value(
                    run_result,
                    "conflict_detected",
                    None,
                ),
                get_value(
                    run_result,
                    "has_conflict",
                    None,
                ),
            )

            if bool(direct_conflict):
                return True

    conflict_result = get_value(
        experiment,
        "conflict_result",
        None,
    )

    value = first_non_empty(
        get_value(
            experiment,
            "conflict_detected",
            None,
        ),
        get_value(
            experiment,
            "has_conflict",
            None,
        ),
        get_value(
            conflict_result,
            "conflict_detected",
            None,
        ),
        get_value(
            conflict_result,
            "has_conflict",
            None,
        ),
        False,
    )

    return bool(value)


def _extract_negotiation_required(
    experiment: Any,
) -> bool:
    """
    Return True when negotiation was required or executed.
    """

    scenario_results = get_value(
        experiment,
        "scenario_results",
        [],
    )

    if scenario_results:
        for scenario_result in scenario_results:
            run_result = get_value(
                scenario_result,
                "run_result",
                None,
            )

            negotiation_result = get_value(
                run_result,
                "negotiation_result",
                None,
            )

            if negotiation_result is not None:
                agreement_reached = get_value(
                    negotiation_result,
                    "agreement_reached",
                    None,
                )

                final_operation = get_value(
                    negotiation_result,
                    "final_operation",
                    None,
                )

                negotiation_required = get_value(
                    negotiation_result,
                    "negotiation_required",
                    None,
                )

                negotiated = get_value(
                    negotiation_result,
                    "negotiated",
                    None,
                )

                if any(
                    [
                        bool(agreement_reached),
                        bool(final_operation),
                        bool(negotiation_required),
                        bool(negotiated),
                    ]
                ):
                    return True

            conflicts = get_value(
                run_result,
                "conflicts",
                [],
            )

            for conflict in conflicts or []:
                if bool(
                    get_value(
                        conflict,
                        "requires_negotiation",
                        False,
                    )
                ):
                    return True

    negotiation_result = get_value(
        experiment,
        "negotiation_result",
        None,
    )

    value = first_non_empty(
        get_value(
            experiment,
            "negotiation_required",
            None,
        ),
        get_value(
            experiment,
            "negotiated",
            None,
        ),
        get_value(
            negotiation_result,
            "negotiation_required",
            None,
        ),
        get_value(
            negotiation_result,
            "negotiated",
            None,
        ),
        get_value(
            negotiation_result,
            "agreement_reached",
            None,
        ),
        False,
    )

    return bool(value)


def _extract_warnings(
    source: Any,
) -> list[str]:
    """
    Extract warnings safely from any framework result.
    """

    warnings = get_value(
        source,
        "warnings",
        [],
    )

    if not warnings:
        return []

    if isinstance(
        warnings,
        str,
    ):
        return [warnings]

    return [
        str(warning)
        for warning in warnings
        if warning
    ]


def _extract_errors(
    source: Any,
) -> list[str]:
    """
    Extract errors safely from any framework result.
    """

    errors = get_value(
        source,
        "errors",
        [],
    )

    if not errors:
        return []

    if isinstance(
        errors,
        str,
    ):
        return [errors]

    return [
        str(error)
        for error in errors
        if error
    ]


def _remove_duplicates(
    values: list[str],
) -> list[str]:
    """
    Preserve order while removing duplicate messages.
    """

    unique_values: list[str] = []

    for value in values:
        normalized_value = str(
            value
        ).strip()

        if (
            normalized_value
            and normalized_value
            not in unique_values
        ):
            unique_values.append(
                normalized_value
            )

    return unique_values