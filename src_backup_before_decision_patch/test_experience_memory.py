from learning.experience_memory import ExperienceMemory
from models.execution_result import ExecutionResult
from models.experience import Experience
from models.outcome_metrics import OutcomeMetrics


def create_execution_result(
    source: str,
    operation: str
) -> ExecutionResult:
    return ExecutionResult(
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
        message="Action executed successfully.",
        source=source
    )


def create_outcome(
    decision_id: str,
    reward: float,
    status: str
) -> OutcomeMetrics:
    return OutcomeMetrics(
        decision_id=decision_id,
        target="PRODUCT-001",
        revenue_change_percentage=10.0,
        profit_change_percentage=8.0,
        conversion_change_percentage=6.0,
        inventory_health_change=0.10,
        customer_satisfaction_change=0.05,
        overall_reward=reward,
        outcome_status=status,
        metric_scores={
            "revenue": 0.50,
            "profit": 0.40,
            "conversion": 0.30,
            "inventory_health": 0.10,
            "customer_satisfaction": 0.05
        }
    )


def create_experience(
    experience_id: str,
    decision_id: str,
    source_agent: str,
    reward: float,
    status: str,
    operation: str
) -> Experience:
    return Experience(
        experience_id=experience_id,
        decision_id=decision_id,
        target="PRODUCT-001",
        source_agent=source_agent,
        decision_type="NEGOTIATED",
        action_type="PRICE_CHANGE",
        operation=operation,
        execution_result=create_execution_result(
            source="NEGOTIATION",
            operation=operation
        ),
        outcome_metrics=create_outcome(
            decision_id=decision_id,
            reward=reward,
            status=status
        ),
        context={
            "season": "FESTIVE",
            "market_demand": "HIGH"
        }
    )


def test_add_and_retrieve():
    memory = ExperienceMemory()

    experience = create_experience(
        experience_id="EXP-001",
        decision_id="DECISION-001",
        source_agent="PricingAgent",
        reward=0.63,
        status="SUCCESS",
        operation="DECREASE"
    )

    memory.add(experience)

    stored = memory.get_by_id(
        "EXP-001"
    )

    print("\nAdd and Retrieve Test")
    print("---------------------")
    print("Stored Experience:", stored.experience_id)
    print("Stored Agent:", stored.source_agent)
    print("Stored Reward:", stored.reward)

    assert len(memory) == 1
    assert stored is not None
    assert stored.experience_id == "EXP-001"
    assert stored.reward == 0.63


def test_agent_statistics():
    memory = ExperienceMemory()

    experiences = [
        create_experience(
            "EXP-001",
            "DECISION-001",
            "PricingAgent",
            0.60,
            "SUCCESS",
            "DECREASE"
        ),
        create_experience(
            "EXP-002",
            "DECISION-002",
            "PricingAgent",
            -0.40,
            "FAILURE",
            "INCREASE"
        ),
        create_experience(
            "EXP-003",
            "DECISION-003",
            "InventoryAgent",
            0.80,
            "SUCCESS",
            "MAINTAIN"
        ),
        create_experience(
            "EXP-004",
            "DECISION-004",
            "PricingAgent",
            0.10,
            "NEUTRAL",
            "MAINTAIN"
        )
    ]

    memory.add_many(experiences)

    pricing_experiences = memory.get_by_agent(
        "PricingAgent"
    )

    pricing_average_reward = memory.average_reward(
        "PricingAgent"
    )

    pricing_success_rate = memory.success_rate(
        "PricingAgent"
    )

    pricing_failure_rate = memory.failure_rate(
        "PricingAgent"
    )

    print("\nAgent Statistics Test")
    print("---------------------")
    print(
        "Pricing Experiences:",
        len(pricing_experiences)
    )
    print(
        "Pricing Average Reward:",
        pricing_average_reward
    )
    print(
        "Pricing Success Rate:",
        pricing_success_rate
    )
    print(
        "Pricing Failure Rate:",
        pricing_failure_rate
    )

    assert len(pricing_experiences) == 3
    assert pricing_average_reward == 0.1
    assert pricing_success_rate == 0.3333
    assert pricing_failure_rate == 0.3333


def test_agent_summary():
    memory = ExperienceMemory()

    memory.add_many([
        create_experience(
            "EXP-101",
            "DECISION-101",
            "PricingAgent",
            0.70,
            "SUCCESS",
            "DECREASE"
        ),
        create_experience(
            "EXP-102",
            "DECISION-102",
            "PricingAgent",
            0.30,
            "SUCCESS",
            "MAINTAIN"
        ),
        create_experience(
            "EXP-103",
            "DECISION-103",
            "InventoryAgent",
            -0.50,
            "FAILURE",
            "INCREASE"
        )
    ])

    summary = memory.agent_summary()

    print("\nAgent Summary Test")
    print("------------------")
    print(summary)

    assert summary["PricingAgent"][
        "experience_count"
    ] == 2

    assert summary["PricingAgent"][
        "average_reward"
    ] == 0.5

    assert summary["PricingAgent"][
        "success_rate"
    ] == 1.0

    assert summary["InventoryAgent"][
        "failure_count"
    ] == 1


def test_duplicate_rejection():
    memory = ExperienceMemory()

    experience = create_experience(
        "EXP-200",
        "DECISION-200",
        "MarketingAgent",
        0.25,
        "SUCCESS",
        "DECREASE"
    )

    memory.add(experience)

    try:
        memory.add(experience)

    except ValueError as error:
        print("\nDuplicate Rejection Test")
        print("------------------------")
        print("Expected Error:", error)
        return

    raise AssertionError(
        "Duplicate experience should raise ValueError."
    )


def test_recent_and_clear():
    memory = ExperienceMemory()

    for index in range(5):
        memory.add(
            create_experience(
                experience_id=f"EXP-{index}",
                decision_id=f"DECISION-{index}",
                source_agent="PricingAgent",
                reward=0.10 * index,
                status="NEUTRAL",
                operation="MAINTAIN"
            )
        )

    recent = memory.get_recent(
        limit=2
    )

    print("\nRecent Experience Test")
    print("----------------------")
    print([
        experience.experience_id
        for experience in recent
    ])

    assert len(recent) == 2
    assert recent[0].experience_id == "EXP-3"
    assert recent[1].experience_id == "EXP-4"

    memory.clear()

    assert len(memory) == 0
    assert memory.get_all() == []


if __name__ == "__main__":
    test_add_and_retrieve()
    test_agent_statistics()
    test_agent_summary()
    test_duplicate_rejection()
    test_recent_and_clear()

    print("\nExperience Memory tests passed.")