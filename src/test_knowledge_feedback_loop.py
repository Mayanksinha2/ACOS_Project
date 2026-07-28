import tempfile
from pathlib import Path
from types import SimpleNamespace

from knowledge.knowledge_advisor import (
    KnowledgeAdvisor
)
from knowledge.knowledge_base import (
    KnowledgeBase
)
from knowledge.knowledge_guided_score_calculator import (
    KnowledgeGuidedScoreCalculator
)
from knowledge.knowledge_integrator import (
    KnowledgeIntegrator
)
from learning.learning_engine import (
    LearningEngine
)
from learning.self_optimization_engine import (
    SelfOptimizationEngine
)
from models.knowledge_entry import (
    KnowledgeEntry
)
from test_self_optimization_engine import (
    build_experience_memory
)


class FakeBaseScoreCalculator:
    """
    Simulates the existing backward-compatible
    MOCRA ScoreCalculator.
    """

    def calculate(
        self,
        decision
    ) -> dict:
        return {
            "confidence_score": 0.80,
            "risk_score": 0.80,
            "priority_score": 0.80,
            "final_score": 0.80
        }

    def calculate_value(
        self,
        decision
    ) -> float:
        return self.calculate(
            decision
        )["final_score"]


def build_knowledge_base(
    storage_path: str
) -> KnowledgeBase:
    """
    Generate SCOE knowledge from historical experience.
    """

    memory = build_experience_memory()

    learning_engine = LearningEngine(
        memory
    )

    scoe = SelfOptimizationEngine(
        experience_memory=memory,
        learning_engine=learning_engine,
        strong_agent_threshold=0.70,
        weak_agent_threshold=0.45,
        strong_operation_threshold=0.40,
        weak_operation_threshold=-0.20,
        minimum_operation_experiences=2
    )

    report = scoe.analyze_system()

    knowledge_base = KnowledgeBase(
        storage_path=storage_path,
        auto_load=False,
        auto_save=True
    )

    integrator = KnowledgeIntegrator(
        knowledge_base
    )

    integrator.integrate_report(
        report
    )

    return knowledge_base


def create_decision(
    agent_name: str,
    operation: str
):
    """
    Create a lightweight decision compatible with
    the extraction logic.
    """

    action = SimpleNamespace(
        operation=operation,
        priority=8
    )

    return SimpleNamespace(
        agent_id=agent_name,
        business_action=action,
        metadata={
            "context": {
                "season": "FESTIVAL",
                "demand_level": "HIGH",
                "inventory_level": "LOW",
                "market_condition": (
                    "HIGH_DEMAND"
                )
            }
        }
    )


def test_positive_knowledge_adjustment(
    calculator: KnowledgeGuidedScoreCalculator
) -> None:
    """
    PricingAgent and INCREASE should receive
    positive knowledge influence.
    """

    decision = create_decision(
        agent_name="PricingAgent",
        operation="INCREASE"
    )

    score = calculator.calculate(
        decision
    )

    print("\nPositive Knowledge Adjustment")
    print("-----------------------------")

    print(
        "Agent:",
        decision.agent_id
    )

    print(
        "Operation:",
        decision.business_action.operation
    )

    print(
        "Base Score:",
        score["base_final_score"]
    )

    print(
        "Knowledge Modifier:",
        score["knowledge_modifier"]
    )

    print(
        "Final Score:",
        score["final_score"]
    )

    print(
        "Knowledge Applied:",
        score["knowledge_applied"]
    )

    assert score["knowledge_applied"] is True

    assert (
        score["knowledge_modifier"]
        > 1.0
    )

    assert (
        score["final_score"]
        > score["base_final_score"]
    )


def test_negative_knowledge_adjustment(
    calculator: KnowledgeGuidedScoreCalculator
) -> None:
    """
    MarketingAgent and DECREASE should receive
    a negative knowledge influence.
    """

    decision = create_decision(
        agent_name="MarketingAgent",
        operation="DECREASE"
    )

    score = calculator.calculate(
        decision
    )

    print("\nNegative Knowledge Adjustment")
    print("-----------------------------")

    print(
        "Agent:",
        decision.agent_id
    )

    print(
        "Operation:",
        decision.business_action.operation
    )

    print(
        "Base Score:",
        score["base_final_score"]
    )

    print(
        "Knowledge Modifier:",
        score["knowledge_modifier"]
    )

    print(
        "Final Score:",
        score["final_score"]
    )

    print(
        "Knowledge Applied:",
        score["knowledge_applied"]
    )

    assert score["knowledge_applied"] is True

    assert (
        score["knowledge_modifier"]
        < 1.0
    )

    assert (
        score["final_score"]
        < score["base_final_score"]
    )


def test_unknown_decision(
    calculator: KnowledgeGuidedScoreCalculator
) -> None:
    """
    An unknown agent and operation should preserve
    the original score.
    """

    decision = create_decision(
        agent_name="UnknownAgent",
        operation="UNKNOWN_OPERATION"
    )

    score = calculator.calculate(
        decision
    )

    print("\nUnknown Decision")
    print("----------------")

    print(
        "Base Score:",
        score["base_final_score"]
    )

    print(
        "Final Score:",
        score["final_score"]
    )

    print(
        "Knowledge Applied:",
        score["knowledge_applied"]
    )

    assert (
        score["knowledge_applied"]
        is False
    )

    assert (
        score["knowledge_modifier"]
        == 1.0
    )

    assert (
        score["final_score"]
        == score["base_final_score"]
    )


def test_manual_business_rule(
    knowledge_base: KnowledgeBase,
    calculator: KnowledgeGuidedScoreCalculator
) -> None:
    """
    Verify that manually stored rules also influence
    future decisions.
    """

    knowledge_base.add(
        KnowledgeEntry(
            knowledge_type="BUSINESS_RULE",
            target="INVENTORY_LEVEL=LOW",
            statement=(
                "Avoid aggressive discounts when "
                "inventory is low."
            ),
            confidence=0.95,
            expected_benefit=0.40,
            priority="CRITICAL",
            evidence={
                "recommendation": (
                    "AVOID_DISCOUNT"
                )
            },
            source="RESEARCHER"
        )
    )

    decision = create_decision(
        agent_name="MarketingAgent",
        operation="DECREASE"
    )

    score = calculator.calculate(
        decision
    )

    adjustment = score[
        "knowledge_adjustment"
    ]

    assert (
        adjustment["negative_influence"]
        > 0.0
    )

    assert any(
        "BUSINESS_RULE"
        in explanation
        for explanation
        in adjustment["explanations"]
    )


def test_persistence(
    storage_path: str,
    knowledge_base: KnowledgeBase
) -> None:
    """
    Verify the feedback knowledge remains available
    after application restart.
    """

    knowledge_base.save()

    restored = KnowledgeBase(
        storage_path=storage_path,
        auto_load=True,
        auto_save=False
    )

    assert len(
        restored
    ) == len(
        knowledge_base
    )

    advisor = KnowledgeAdvisor(
        restored
    )

    adjustment = advisor.advise(
        original_score=0.80,
        agent_name="PricingAgent",
        operation="INCREASE",
        context={
            "season": "FESTIVAL",
            "demand_level": "HIGH",
            "inventory_level": "LOW"
        }
    )

    assert adjustment.knowledge_applied is True

    assert adjustment.adjusted_score > 0.80


def run_tests() -> None:
    with tempfile.TemporaryDirectory() as directory:
        storage_path = str(
            Path(directory)
            / "knowledge_feedback.json"
        )

        knowledge_base = build_knowledge_base(
            storage_path
        )

        advisor = KnowledgeAdvisor(
            knowledge_base=knowledge_base,
            minimum_confidence=0.40,
            maximum_adjustment=0.30
        )

        base_calculator = (
            FakeBaseScoreCalculator()
        )

        calculator = (
            KnowledgeGuidedScoreCalculator(
                base_score_calculator=(
                    base_calculator
                ),
                knowledge_advisor=advisor
            )
        )

        test_positive_knowledge_adjustment(
            calculator
        )

        test_negative_knowledge_adjustment(
            calculator
        )

        test_unknown_decision(
            calculator
        )

        test_manual_business_rule(
            knowledge_base,
            calculator
        )

        test_persistence(
            storage_path,
            knowledge_base
        )

        print(
            "\nKnowledge Feedback Loop tests passed."
        )


if __name__ == "__main__":
    run_tests()