from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from application.business_state_builder import BusinessStateBuilder
from reasoning.inventory_reasoner import InventoryReasoner
from reasoning.marketing_reasoner import MarketingReasoner
from reasoning.proposal_generator import ProposalGenerator
from reasoning.rule_reasoner import RuleReasoner
from negotiation.score_calculator import ScoreCalculator

from acos_ui.learning_knowledge_sync import (
    LearningKnowledgeSynchronizer,
)
from acos_ui.learning_store import PersistentLearningStore
from acos_ui.outcome_evaluator import UIOutcomeEvaluator
from acos_ui.outcome_models import OutcomeMetrics


def make_state(
    *,
    conversion: float,
    inventory: int = 45,
    demand: float = 48.0,
):
    visitors = 5000
    sales = round(visitors * conversion)
    return BusinessStateBuilder.build_from_manual_input(
        product_id="PROD-CORRECTNESS",
        inventory=inventory,
        demand=demand,
        conversion_rate=conversion,
        advertising_cost=5000.0,
        visitors=visitors,
        sales=sales,
        revenue=90000.0,
        profit=15000.0,
        season="SALE",
        demand_multiplier=1.1,
        competitor_price_factor=0.90,
        additional_metrics={
            "current_price": 999.0,
            "unit_cost": 420.0,
            "marketing_budget": 60000.0,
        },
    )


def marketing_decision(conversion: float):
    reasoner = MarketingReasoner()
    reasoner.analyze(make_state(conversion=conversion))
    return ProposalGenerator.generate(
        "MarketingAgent",
        reasoner,
        goal="Increase Customer Conversion",
    )


def run_tests() -> None:
    mild = marketing_decision(0.039)
    severe = marketing_decision(0.010)

    assert mild.business_action.operation == "DECREASE"
    assert severe.business_action.operation == "DECREASE"
    assert severe.business_action.value > mild.business_action.value
    assert severe.confidence > mild.confidence
    assert severe.risk > mild.risk

    mild_score = ScoreCalculator().calculate(mild)["final_score"]
    severe_score = ScoreCalculator().calculate(severe)["final_score"]
    assert mild_score != severe_score

    assert any(
        "Conversion is" in item
        for item in severe.evidence
    )
    assert not any(
        "Generated using" in item
        for item in severe.evidence
    )

    pricing = RuleReasoner()
    pricing.analyze(
        make_state(
            conversion=0.04,
            inventory=15,
            demand=80.0,
        )
    )
    pricing_decision = ProposalGenerator.generate(
        "PricingAgent",
        pricing,
    )
    assert pricing_decision.business_action.operation == "INCREASE"
    assert pricing_decision.context["dynamic_scoring"] is True

    inventory = InventoryReasoner()
    inventory.analyze(
        make_state(
            conversion=0.04,
            inventory=300,
            demand=25.0,
        )
    )
    inventory_decision = ProposalGenerator.generate(
        "InventoryAgent",
        inventory,
    )
    assert inventory_decision.business_action.operation == "CLEAR_STOCK"
    assert inventory_decision.business_action.value >= 10

    payload = {
        "run_id": "RUN-LEARN-001",
        "status": "COMPLETED",
        "successful": True,
        "scenario": {
            "product_id": "PROD-CORRECTNESS",
            "current_price": 999.0,
        },
        "negotiation_result": {
            "target": "PROD-CORRECTNESS",
            "agreement_reached": True,
            "final_operation": "DECREASE",
            "final_value": 10.0,
            "participant_agents": [
                "PricingAgent",
                "MarketingAgent",
            ],
            "rounds_completed": 1,
        },
        "mocra_result": {
            "winning_score": 0.8,
            "winning_decision": {
                "agent_id": "MarketingAgent",
            },
            "ranking": [],
        },
        "final_decision": {
            "decision_type": "NEGOTIATED",
            "result": {
                "target": "PROD-CORRECTNESS",
                "agreement_reached": True,
                "final_operation": "DECREASE",
                "final_value": 10.0,
                "participant_agents": [
                    "PricingAgent",
                    "MarketingAgent",
                ],
                "rounds_completed": 1,
            },
            "coordinated_actions": [],
        },
    }

    before = OutcomeMetrics(
        revenue=100000.0,
        profit=20000.0,
        conversion_rate=0.02,
        inventory_health=0.70,
        customer_satisfaction=0.70,
    )
    after = OutcomeMetrics(
        revenue=115000.0,
        profit=22000.0,
        conversion_rate=0.03,
        inventory_health=0.74,
        customer_satisfaction=0.75,
    )

    with TemporaryDirectory() as temporary:
        database = Path(temporary) / "learning.db"
        knowledge = Path(temporary) / "knowledge.json"
        store = PersistentLearningStore(database)

        from knowledge.knowledge_base import KnowledgeBase

        for index in range(3):
            current = dict(payload)
            current["run_id"] = f"RUN-LEARN-{index}"
            evaluation = UIOutcomeEvaluator().evaluate(
                current,
                before,
                after,
                notes="Positive observed outcome.",
            )
            store.save(evaluation)

        synchronizer = LearningKnowledgeSynchronizer(
            store,
            knowledge_base=KnowledgeBase(
                storage_path=str(knowledge),
                auto_load=True,
                auto_save=True,
            ),
        )
        entries = synchronizer.synchronize()

        assert entries
        assert any(
            item.knowledge_type == "AGENT_WEIGHT_INCREASE"
            for item in entries
        )
        assert any(
            item.knowledge_type == "OPERATION_PREFERENCE"
            for item in entries
        )

        summary = store.summary()
        assert summary["best_agent"] == "MarketingAgent"

    print("Decision Intelligence Correctness tests passed.")


if __name__ == "__main__":
    run_tests()
