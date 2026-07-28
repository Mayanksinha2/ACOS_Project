from dataclasses import dataclass, field
from typing import Dict

from learning.adaptive_weight_optimizer import (
    AdaptiveWeightOptimizer
)
from learning.experience_memory import ExperienceMemory
from learning.learning_engine import LearningEngine
from models.execution_result import ExecutionResult
from models.experience import Experience
from models.outcome_metrics import OutcomeMetrics
from negotiation.score_calculator import ScoreCalculator


@dataclass
class TestProposal:
    source_agent: str
    confidence: float
    risk: float
    priority: float
    metadata: Dict = field(
        default_factory=dict
    )


def create_experience(
    experience_id: str,
    agent_name: str,
    reward: float,
    status: str
) -> Experience:

    execution_result = ExecutionResult(
        target="PRODUCT-001",
        action_type="PRICE_CHANGE",
        operation="MAINTAIN",
        success=True,
        previous_state={
            "selling_price": 799
        },
        updated_state={
            "selling_price": 799
        },
        message="Executed.",
        source="TEST"
    )

    outcome_metrics = OutcomeMetrics(
        decision_id=f"DECISION-{experience_id}",
        target="PRODUCT-001",
        revenue_change_percentage=0.0,
        profit_change_percentage=0.0,
        conversion_change_percentage=0.0,
        inventory_health_change=0.0,
        customer_satisfaction_change=0.0,
        overall_reward=reward,
        outcome_status=status,
        metric_scores={}
    )

    return Experience(
        experience_id=experience_id,
        decision_id=f"DECISION-{experience_id}",
        target="PRODUCT-001",
        source_agent=agent_name,
        decision_type="MOCRA",
        action_type="PRICE_CHANGE",
        operation="MAINTAIN",
        execution_result=execution_result,
        outcome_metrics=outcome_metrics
    )


def build_learning_engine() -> LearningEngine:
    memory = ExperienceMemory()

    memory.add_many([
        create_experience(
            "P-001",
            "PricingAgent",
            0.80,
            "SUCCESS"
        ),
        create_experience(
            "P-002",
            "PricingAgent",
            0.70,
            "SUCCESS"
        ),
        create_experience(
            "P-003",
            "PricingAgent",
            0.60,
            "SUCCESS"
        ),
        create_experience(
            "P-004",
            "PricingAgent",
            0.75,
            "SUCCESS"
        ),
        create_experience(
            "P-005",
            "PricingAgent",
            0.65,
            "SUCCESS"
        ),
        create_experience(
            "I-001",
            "InventoryAgent",
            -0.80,
            "FAILURE"
        ),
        create_experience(
            "I-002",
            "InventoryAgent",
            -0.60,
            "FAILURE"
        ),
        create_experience(
            "I-003",
            "InventoryAgent",
            -0.50,
            "FAILURE"
        ),
        create_experience(
            "I-004",
            "InventoryAgent",
            -0.40,
            "FAILURE"
        ),
        create_experience(
            "I-005",
            "InventoryAgent",
            -0.30,
            "FAILURE"
        )
    ])

    return LearningEngine(
        memory=memory
    )


def test_confidence_adjustment():
    learning_engine = build_learning_engine()

    optimizer = AdaptiveWeightOptimizer(
        learning_engine=learning_engine,
        minimum_experiences=3
    )

    pricing_proposal = TestProposal(
        source_agent="PricingAgent",
        confidence=0.80,
        risk=0.20,
        priority=0.80
    )

    inventory_proposal = TestProposal(
        source_agent="InventoryAgent",
        confidence=0.80,
        risk=0.20,
        priority=0.80
    )

    pricing_score = optimizer.optimize_proposal(
        pricing_proposal
    )

    inventory_score = optimizer.optimize_proposal(
        inventory_proposal
    )

    print("\nConfidence Adjustment Test")
    print("--------------------------")
    print(
        "Pricing Original:",
        pricing_score.original_confidence
    )
    print(
        "Pricing Modifier:",
        pricing_score.confidence_modifier
    )
    print(
        "Pricing Adjusted:",
        pricing_score.adjusted_confidence
    )
    print(
        "Inventory Original:",
        inventory_score.original_confidence
    )
    print(
        "Inventory Modifier:",
        inventory_score.confidence_modifier
    )
    print(
        "Inventory Adjusted:",
        inventory_score.adjusted_confidence
    )

    assert pricing_score.learning_applied is True
    assert inventory_score.learning_applied is True

    assert (
        pricing_score.adjusted_confidence
        > pricing_score.original_confidence
    )

    assert (
        inventory_score.adjusted_confidence
        < inventory_score.original_confidence
    )


def test_insufficient_experience():
    learning_engine = build_learning_engine()

    optimizer = AdaptiveWeightOptimizer(
        learning_engine=learning_engine,
        minimum_experiences=3
    )

    marketing_proposal = TestProposal(
        source_agent="MarketingAgent",
        confidence=0.75,
        risk=0.25,
        priority=0.70
    )

    result = optimizer.optimize_proposal(
        marketing_proposal
    )

    print("\nInsufficient Experience Test")
    print("----------------------------")
    print(result.to_dict())

    assert result.learning_applied is False
    assert result.confidence_modifier == 1.0
    assert result.adjusted_confidence == 0.75


def test_metadata_attachment():
    learning_engine = build_learning_engine()

    optimizer = AdaptiveWeightOptimizer(
        learning_engine=learning_engine
    )

    proposal = TestProposal(
        source_agent="PricingAgent",
        confidence=0.80,
        risk=0.20,
        priority=0.80
    )

    updated_proposal = optimizer.apply_to_proposal(
        proposal
    )

    print("\nMetadata Attachment Test")
    print("------------------------")
    print(updated_proposal.metadata)

    assert "adaptive_learning" in (
        updated_proposal.metadata
    )

    assert (
        updated_proposal.metadata[
            "adaptive_learning"
        ]["learning_applied"]
        is True
    )


def test_mocra_score_changes():
    learning_engine = build_learning_engine()

    optimizer = AdaptiveWeightOptimizer(
        learning_engine=learning_engine
    )

    pricing_proposal = TestProposal(
        source_agent="PricingAgent",
        confidence=0.80,
        risk=0.20,
        priority=0.80
    )

    inventory_proposal = TestProposal(
        source_agent="InventoryAgent",
        confidence=0.80,
        risk=0.20,
        priority=0.80
    )

    normal_calculator = ScoreCalculator()

    adaptive_calculator = ScoreCalculator(
        adaptive_optimizer=optimizer
    )

    normal_pricing_details = (
    normal_calculator.calculate(
        pricing_proposal
    )
)

    normal_inventory_details = (
         normal_calculator.calculate(
        inventory_proposal
        )
    )

    adaptive_pricing_details = (
        adaptive_calculator.calculate(
        pricing_proposal
        )
    )

    adaptive_inventory_details = (
        adaptive_calculator.calculate(
        inventory_proposal
        )
    )

    normal_pricing_score = (
        normal_pricing_details["final_score"]
    )

    normal_inventory_score = (
        normal_inventory_details["final_score"]
    )

    adaptive_pricing_score = (
        adaptive_pricing_details["final_score"]
    )

    adaptive_inventory_score = (
        adaptive_inventory_details["final_score"]
    )

    print("\nMOCRA Adaptive Score Test")
    print("-------------------------")
    print(
        "Normal Pricing:",
        normal_pricing_score
    )
    print(
        "Normal Inventory:",
        normal_inventory_score
    )
    print(
        "Adaptive Pricing:",
        adaptive_pricing_score
    )
    print(
        "Adaptive Inventory:",
        adaptive_inventory_score
    )

    assert (
        normal_pricing_score
        == normal_inventory_score
    )

    assert (
        adaptive_pricing_score
        > adaptive_inventory_score
    )

    assert (
        adaptive_pricing_score
        > normal_pricing_score
    )

    assert (
        adaptive_inventory_score
        < normal_inventory_score
    )


if __name__ == "__main__":
    test_confidence_adjustment()
    test_insufficient_experience()
    test_metadata_attachment()
    test_mocra_score_changes()

    print(
        "\nAdaptive Weight Optimizer tests passed."
    )