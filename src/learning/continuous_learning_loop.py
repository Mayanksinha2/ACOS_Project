from typing import Optional

from knowledge.knowledge_base import (
    KnowledgeBase
)
from knowledge.knowledge_integrator import (
    KnowledgeIntegrator
)
from learning.experience_memory import (
    ExperienceMemory
)
from learning.self_optimization_engine import (
    SelfOptimizationEngine
)
from models.experience import Experience
from models.system_optimization_report import (
    SystemOptimizationReport
)


class ContinuousLearningLoop:
    """
    Coordinates the complete ACOS feedback cycle.

    Experience
        ↓
    Experience Memory
        ↓
    Learning Engine
        ↓
    SCOE
        ↓
    Persistent Knowledge Base
        ↓
    Knowledge-guided future decisions
    """

    def __init__(
        self,
        experience_memory: ExperienceMemory,
        self_optimization_engine: (
            SelfOptimizationEngine
        ),
        knowledge_base: KnowledgeBase,
        optimization_interval: int = 5
    ):
        if optimization_interval < 1:
            raise ValueError(
                "optimization_interval must be "
                "at least 1."
            )

        self.experience_memory = (
            experience_memory
        )

        self.self_optimization_engine = (
            self_optimization_engine
        )

        self.knowledge_base = (
            knowledge_base
        )

        self.knowledge_integrator = (
            KnowledgeIntegrator(
                knowledge_base
            )
        )

        self.optimization_interval = (
            optimization_interval
        )

        self.experiences_since_refresh = 0

        self.last_report: Optional[
            SystemOptimizationReport
        ] = None

    def process_experience(
        self,
        experience: Experience,
        force_refresh: bool = False
    ) -> Optional[SystemOptimizationReport]:
        """
        Store one new experience and automatically
        refresh system knowledge when required.
        """

        if not isinstance(
            experience,
            Experience
        ):
            raise TypeError(
                "experience must be an Experience."
            )

        self.experience_memory.add(
            experience
        )

        self.experiences_since_refresh += 1

        refresh_required = (
            force_refresh
            or self.experiences_since_refresh
            >= self.optimization_interval
        )

        if not refresh_required:
            return None

        return self.refresh_knowledge()

    def refresh_knowledge(
        self
    ) -> SystemOptimizationReport:
        """
        Run SCOE and persist all discovered knowledge.
        """

        report = (
            self.self_optimization_engine
            .analyze_system()
        )

        self.knowledge_integrator.integrate_report(
            report
        )

        self.last_report = report
        self.experiences_since_refresh = 0

        return report

    def process_many(
        self,
        experiences: list[Experience],
        refresh_at_end: bool = True
    ) -> Optional[SystemOptimizationReport]:
        """
        Process multiple experiences efficiently.
        """

        latest_report = None

        for experience in experiences:
            generated_report = (
                self.process_experience(
                    experience
                )
            )

            if generated_report is not None:
                latest_report = (
                    generated_report
                )

        if (
            refresh_at_end
            and self.experiences_since_refresh > 0
        ):
            latest_report = (
                self.refresh_knowledge()
            )

        return latest_report

    def system_summary(self) -> dict:
        """
        Return feedback-loop status.
        """

        return {
            "experience_count": len(
                self.experience_memory
            ),
            "knowledge_count": len(
                self.knowledge_base
            ),
            "experiences_since_refresh": (
                self.experiences_since_refresh
            ),
            "optimization_interval": (
                self.optimization_interval
            ),
            "last_system_health": (
                self.last_report.system_health_score
                if self.last_report
                else None
            ),
            "last_system_status": (
                self.last_report
                .system_health_status
                if self.last_report
                else None
            )
        }