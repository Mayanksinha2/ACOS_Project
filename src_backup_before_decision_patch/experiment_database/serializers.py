from __future__ import annotations

from sqlite3 import Row

from .models import (
    AblationResultRecord,
    AggregatedEvaluationRecord,
    ArtifactRecord,
    ExperimentRecord,
    PublicationRecord,
    ReportRecord,
    RunRecord,
)
from .utils import (
    int_to_bool,
    json_loads,
)


def experiment_from_row(
    row: Row,
) -> ExperimentRecord:
    return ExperimentRecord(
        experiment_id=row["experiment_id"],
        name=row["name"],
        status=row["status"],
        description=row["description"] or "",
        metadata=json_loads(
            row["metadata_json"],
            {},
        ),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def run_from_row(
    row: Row,
) -> RunRecord:
    return RunRecord(
        run_id=row["run_id"],
        experiment_id=row["experiment_id"],
        variant_name=row["variant_name"],
        repetition_index=row["repetition_index"],
        random_seed=row["random_seed"],
        status=row["status"],
        successful=int_to_bool(
            row["successful"]
        ),
        reward=row["reward"],
        duration_seconds=row[
            "duration_seconds"
        ],
        conflict_detected=int_to_bool(
            row["conflict_detected"]
        ),
        negotiation_required=int_to_bool(
            row["negotiation_required"]
        ),
        metadata=json_loads(
            row["metadata_json"],
            {},
        ),
        warnings=json_loads(
            row["warnings_json"],
            [],
        ),
        errors=json_loads(
            row["errors_json"],
            [],
        ),
        created_at=row["created_at"],
    )


def artifact_from_row(
    row: Row,
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=row["artifact_id"],
        experiment_id=row["experiment_id"],
        run_id=row["run_id"],
        artifact_type=row["artifact_type"],
        path=row["path"],
        metadata=json_loads(
            row["metadata_json"],
            {},
        ),
        created_at=row["created_at"],
    )


def report_from_row(
    row: Row,
) -> ReportRecord:
    return ReportRecord(
        report_id=row["report_id"],
        experiment_id=row["experiment_id"],
        run_id=row["run_id"],
        markdown_path=row["markdown_path"],
        html_path=row["html_path"],
        manifest_path=row["manifest_path"],
        data_path=row["data_path"],
        metadata=json_loads(
            row["metadata_json"],
            {},
        ),
        created_at=row["created_at"],
    )


def publication_from_row(
    row: Row,
) -> PublicationRecord:
    return PublicationRecord(
        publication_id=row["publication_id"],
        experiment_id=row["experiment_id"],
        run_id=row["run_id"],
        markdown_path=row["markdown_path"],
        latex_path=row["latex_path"],
        manifest_path=row["manifest_path"],
        data_path=row["data_path"],
        metadata=json_loads(
            row["metadata_json"],
            {},
        ),
        created_at=row["created_at"],
    )


def evaluation_from_row(
    row: Row,
) -> AggregatedEvaluationRecord:
    return AggregatedEvaluationRecord(
        evaluation_id=row["evaluation_id"],
        experiment_id=row["experiment_id"],
        metrics=json_loads(
            row["metrics_json"],
            {},
        ),
        groups=json_loads(
            row["groups_json"],
            {},
        ),
        warnings=json_loads(
            row["warnings_json"],
            [],
        ),
        errors=json_loads(
            row["errors_json"],
            [],
        ),
        created_at=row["created_at"],
    )


def ablation_from_row(
    row: Row,
) -> AblationResultRecord:
    return AblationResultRecord(
        ablation_id=row["ablation_id"],
        experiment_id=row["experiment_id"],
        baseline_group=row["baseline_group"],
        primary_metric=row["primary_metric"],
        best_group=row["best_group"],
        worst_group=row["worst_group"],
        ranking=json_loads(
            row["ranking_json"],
            [],
        ),
        comparisons=json_loads(
            row["comparisons_json"],
            [],
        ),
        warnings=json_loads(
            row["warnings_json"],
            [],
        ),
        errors=json_loads(
            row["errors_json"],
            [],
        ),
        created_at=row["created_at"],
    )
