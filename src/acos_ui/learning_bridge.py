from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .outcome_models import OutcomeEvaluation


class ExistingLearningBridge:
    """
    Safe compatibility bridge for the existing research learning package.

    The current Phase 3B does not assume undocumented constructor or method
    signatures. It reports whether the learning package is importable and
    exposes a stable payload that can be connected once the exact API is
    intentionally mapped.
    """

    MODULE_NAMES = (
        "learning.outcome_evaluator",
        "learning.experience_memory",
        "learning.learning_engine",
        "learning.adaptive_weight_optimizer",
        "learning.self_optimization_engine",
        "learning.continuous_learning_loop",
        "knowledge.knowledge_base",
        "knowledge.knowledge_integrator",
    )

    def availability(self) -> dict[str, bool]:
        result: dict[str, bool] = {}
        for module_name in self.MODULE_NAMES:
            try:
                __import__(module_name)
                result[module_name] = True
            except Exception:
                result[module_name] = False
        return result

    def feedback_payload(
        self,
        evaluation: OutcomeEvaluation,
    ) -> dict[str, Any]:
        return {
            "evaluation_id": evaluation.evaluation_id,
            "run_id": evaluation.run_id,
            "winning_agent": evaluation.winning_agent,
            "operation": evaluation.primary_operation,
            "reward": evaluation.reward,
            "classification": evaluation.classification,
            "before": asdict(evaluation.before),
            "after": asdict(evaluation.after),
            "metric_changes": [
                asdict(item)
                for item in evaluation.metric_changes
            ],
            "evaluated_at": evaluation.evaluated_at,
        }
