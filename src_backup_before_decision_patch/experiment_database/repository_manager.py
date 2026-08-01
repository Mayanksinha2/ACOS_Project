from __future__ import annotations

from dataclasses import dataclass

from .ablation_repository import (
    AblationRepository,
)
from .artifact_repository import (
    ArtifactRepository,
)
from .database import ExperimentDatabase
from .evaluation_repository import (
    EvaluationRepository,
)
from .experiment_repository import (
    ExperimentRepository,
)
from .publication_repository import (
    PublicationRepository,
)
from .report_repository import (
    ReportRepository,
)
from .run_repository import RunRepository


@dataclass(slots=True)
class RepositoryManager:
    database: ExperimentDatabase
    experiments: ExperimentRepository
    runs: RunRepository
    artifacts: ArtifactRepository
    reports: ReportRepository
    publications: PublicationRepository
    evaluations: EvaluationRepository
    ablations: AblationRepository

    @classmethod
    def create(
        cls,
        database: ExperimentDatabase,
    ) -> "RepositoryManager":
        database.initialize()

        return cls(
            database=database,
            experiments=ExperimentRepository(
                database
            ),
            runs=RunRepository(database),
            artifacts=ArtifactRepository(
                database
            ),
            reports=ReportRepository(
                database
            ),
            publications=PublicationRepository(
                database
            ),
            evaluations=EvaluationRepository(
                database
            ),
            ablations=AblationRepository(
                database
            ),
        )
