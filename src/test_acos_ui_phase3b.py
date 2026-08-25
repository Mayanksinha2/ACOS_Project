from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from acos_ui.learning_store import PersistentLearningStore
from acos_ui.outcome_evaluator import UIOutcomeEvaluator
from acos_ui.outcome_models import OutcomeMetrics


def sample_payload() -> dict:
    return {
        "run_id": "RUN-3B-001",
        "status": "COMPLETED",
        "successful": True,
        "scenario": {
            "product_id": "PROD-3B-001",
            "current_price": 999.0,
            "revenue": 42980.0,
            "profit": 7500.0,
        },
        "calculated_metrics": {
            "conversion_rate": 0.0375,
        },
        "negotiation_result": {
            "target": "PROD-3B-001",
            "agreement_reached": True,
            "final_operation": "DECREASE",
            "final_value": 7.91,
            "participant_agents": [
                "PricingAgent",
                "MarketingAgent",
            ],
            "rounds_completed": 1,
        },
        "mocra_result": {
            "winning_score": 0.763,
            "winning_decision": {
                "agent_id": "MarketingAgent",
            },
            "ranking": [],
        },
        "final_decision": {
            "decision_type": "NEGOTIATED",
            "result": {
                "target": "PROD-3B-001",
                "agreement_reached": True,
                "final_operation": "DECREASE",
                "final_value": 7.91,
                "participant_agents": [
                    "PricingAgent",
                    "MarketingAgent",
                ],
                "rounds_completed": 1,
            },
            "coordinated_actions": [],
        },
    }


def run_tests() -> None:
    before = OutcomeMetrics(
        revenue=42980.0,
        profit=7500.0,
        conversion_rate=0.0375,
        inventory_health=0.70,
        customer_satisfaction=0.70,
    )
    after = OutcomeMetrics(
        revenue=48500.0,
        profit=8250.0,
        conversion_rate=0.046,
        inventory_health=0.74,
        customer_satisfaction=0.78,
    )

    evaluation = UIOutcomeEvaluator().evaluate(
        payload=sample_payload(),
        before=before,
        after=after,
        notes="Seven-day observation window.",
    )

    assert evaluation.classification == "SUCCESS"
    assert evaluation.reward > 0
    assert evaluation.winning_agent == "MarketingAgent"
    assert len(evaluation.metric_changes) == 5

    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "learning.db"
        store = PersistentLearningStore(path)
        store.save(evaluation)

        assert store.exists_for_run("RUN-3B-001")

        loaded = store.latest()
        assert loaded is not None
        assert loaded.evaluation_id == evaluation.evaluation_id
        assert loaded.before.revenue == 42980.0
        assert loaded.after.conversion_rate == 0.046

        summary = store.summary()
        assert summary["total"] == 1
        assert summary["successes"] == 1
        assert summary["average_reward"] > 0
        assert summary["best_agent"] == "MarketingAgent"

        agent_stats = store.agent_statistics()
        assert len(agent_stats) == 1
        assert agent_stats[0]["agent"] == "MarketingAgent"
        assert 0 <= agent_stats[0]["reliability"] <= 1

        operation_stats = store.operation_statistics()
        assert operation_stats[0]["operation"] == "DECREASE"

    print("ACOS UI Phase 3B tests passed.")


if __name__ == "__main__":
    run_tests()
