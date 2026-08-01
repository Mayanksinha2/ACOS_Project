from learning.experience_memory import ExperienceMemory
from learning.learning_engine import LearningEngine
from models.execution_result import ExecutionResult
from models.experience import Experience
from models.outcome_metrics import OutcomeMetrics


def create_experience(
    experience_id: str,
    agent_name: str,
    reward: float,
    status: str,
    operation: str
) -> Experience:

    decision_id = (
        f"DECISION-{experience_id}"
    )

    execution_result = ExecutionResult(
        target="PRODUCT-001",
        action_type="PRICE_CHANGE",
        operation=operation,
        success=True,
        previous_state={
            "selling_price": 799
        },
        updated_state={
            "selling_price": 759
        },
        message="Executed successfully.",
        source="TEST"
    )

    outcome_metrics = OutcomeMetrics(
        decision_id=decision_id,
        target="PRODUCT-001",
        revenue_change_percentage=5.0,
        profit_change_percentage=5.0,
        conversion_change_percentage=5.0,
        inventory_health_change=0.05,
        customer_satisfaction_change=0.05,
        overall_reward=reward,
        outcome_status=status,
        metric_scores={}
    )

    return Experience(
        experience_id=experience_id,
        decision_id=decision_id,
        target="PRODUCT-001",
        source_agent=agent_name,
        decision_type="MOCRA",
        action_type="PRICE_CHANGE",
        operation=operation,
        execution_result=execution_result,
        outcome_metrics=outcome_metrics
    )


def build_memory() -> ExperienceMemory:
    memory = ExperienceMemory()

    experiences = [
        create_experience(
            "EXP-001",
            "PricingAgent",
            0.80,
            "SUCCESS",
            "DECREASE"
        ),
        create_experience(
            "EXP-002",
            "PricingAgent",
            0.70,
            "SUCCESS",
            "DECREASE"
        ),
        create_experience(
            "EXP-003",
            "PricingAgent",
            0.60,
            "SUCCESS",
            "MAINTAIN"
        ),
        create_experience(
            "EXP-004",
            "PricingAgent",
            0.50,
            "SUCCESS",
            "MAINTAIN"
        ),
        create_experience(
            "EXP-005",
            "PricingAgent",
            0.40,
            "NEUTRAL",
            "INCREASE"
        ),
        create_experience(
            "EXP-006",
            "InventoryAgent",
            -0.60,
            "FAILURE",
            "INCREASE"
        ),
        create_experience(
            "EXP-007",
            "InventoryAgent",
            -0.40,
            "FAILURE",
            "INCREASE"
        ),
        create_experience(
            "EXP-008",
            "InventoryAgent",
            0.10,
            "NEUTRAL",
            "MAINTAIN"
        ),
        create_experience(
            "EXP-009",
            "MarketingAgent",
            0.30,
            "SUCCESS",
            "DECREASE"
        ),
        create_experience(
            "EXP-010",
            "MarketingAgent",
            0.25,
            "SUCCESS",
            "DECREASE"
        )
    ]

    memory.add_many(
        experiences
    )

    return memory


def test_agent_analysis():
    memory = build_memory()

    engine = LearningEngine(
        memory=memory
    )

    performance = engine.analyze_agent(
        "PricingAgent"
    )

    print("\nAgent Analysis Test")
    print("-------------------")
    print("Agent:", performance.agent_name)
    print(
        "Experience Count:",
        performance.experience_count
    )
    print(
        "Average Reward:",
        performance.average_reward
    )
    print(
        "Success Rate:",
        performance.success_rate
    )
    print(
        "Reward Stability:",
        performance.reward_stability
    )
    print(
        "Reliability Score:",
        performance.reliability_score
    )
    print(
        "Confidence Modifier:",
        performance.confidence_modifier
    )
    print(
        "Operation Performance:",
        performance.operation_performance
    )

    assert performance.experience_count == 5
    assert performance.success_count == 4
    assert performance.neutral_count == 1
    assert performance.average_reward == 0.6
    assert performance.success_rate == 0.8
    assert performance.reliability_score > 0.7
    assert performance.confidence_modifier > 1.0
    assert performance.is_reliable() is True


def test_agent_ranking():
    memory = build_memory()

    engine = LearningEngine(
        memory=memory
    )

    ranking = engine.rank_agents()

    print("\nAgent Ranking Test")
    print("------------------")

    for position, performance in enumerate(
        ranking,
        start=1
    ):
        print(
            position,
            performance.agent_name,
            performance.reliability_score
        )

    assert ranking[0].agent_name == "PricingAgent"
    assert (
        ranking[-1].agent_name
        == "InventoryAgent"
    )


def test_confidence_modifiers():
    memory = build_memory()

    engine = LearningEngine(
        memory=memory
    )

    pricing_modifier = (
        engine.get_confidence_modifier(
            "PricingAgent"
        )
    )

    inventory_modifier = (
        engine.get_confidence_modifier(
            "InventoryAgent"
        )
    )

    print("\nConfidence Modifier Test")
    print("------------------------")
    print(
        "Pricing Modifier:",
        pricing_modifier
    )
    print(
        "Inventory Modifier:",
        inventory_modifier
    )

    assert pricing_modifier > 1.0
    assert inventory_modifier < 1.0


def test_unknown_agent():
    memory = build_memory()

    engine = LearningEngine(
        memory=memory
    )

    performance = engine.analyze_agent(
        "UnknownAgent"
    )

    print("\nUnknown Agent Test")
    print("------------------")
    print(
        performance.to_dict()
    )

    assert performance.experience_count == 0
    assert performance.reliability_score == 0.0
    assert performance.confidence_modifier == 1.0


def test_invalid_weights():
    memory = build_memory()

    try:
        LearningEngine(
            memory=memory,
            weights={
                "average_reward": 0.50,
                "success_rate": 0.30,
                "stability": 0.10,
                "experience": 0.05
            }
        )

    except ValueError as error:
        print("\nInvalid Weight Test")
        print("-------------------")
        print("Expected Error:", error)
        return

    raise AssertionError(
        "Invalid weights should raise ValueError."
    )


if __name__ == "__main__":
    test_agent_analysis()
    test_agent_ranking()
    test_confidence_modifiers()
    test_unknown_agent()
    test_invalid_weights()

    print("\nLearning Engine tests passed.")