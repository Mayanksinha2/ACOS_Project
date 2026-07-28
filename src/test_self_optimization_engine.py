from learning.experience_memory import (
    ExperienceMemory
)
from learning.learning_engine import (
    LearningEngine
)
from learning.self_optimization_engine import (
    SelfOptimizationEngine
)
from models.experience import Experience
from models.outcome_metrics import OutcomeMetrics


def create_outcome(
    experience_id: str,
    reward: float,
    status: str,
    target: str = "SKU-101"
) -> OutcomeMetrics:
    """
    Create an OutcomeMetrics object compatible with
    the existing ACOS OutcomeMetrics dataclass.
    """

    decision_id = f"DEC-{experience_id}"

    return OutcomeMetrics(
        decision_id=decision_id,
        target=target,

        revenue_change_percentage=reward,
        profit_change_percentage=reward,
        conversion_change_percentage=reward,
        inventory_health_change=reward,
        customer_satisfaction_change=reward,

        overall_reward=reward,
        outcome_status=status,

        metric_scores={
            "revenue_score": reward,
            "profit_score": reward,
            "conversion_score": reward,
            "inventory_health_score": reward,
            "customer_satisfaction_score": reward
        }
    )


def create_experience(
    experience_id: str,
    agent_name: str,
    operation: str,
    reward: float,
    status: str,
    context: dict,
    target: str = "SKU-101"
) -> Experience:
    """
    Create an Experience object for SCOE testing.
    """

    decision_id = f"DEC-{experience_id}"

    outcome_metrics = create_outcome(
        experience_id=experience_id,
        reward=reward,
        status=status,
        target=target
    )

    return Experience(
        experience_id=experience_id,
        decision_id=decision_id,
        target=target,
        source_agent=agent_name,
        decision_type="AUTONOMOUS",
        action_type="COMMERCE_ACTION",
        operation=operation,

        execution_result={
            "success": status == "SUCCESS",
            "message": (
                f"{operation} execution completed "
                f"with outcome {status}."
            )
        },

        outcome_metrics=outcome_metrics,
        context=context
    )


def build_experience_memory() -> ExperienceMemory:
    """
    Build synthetic historical experiences for three agents.

    PricingAgent:
        Strong positive performance.

    InventoryAgent:
        Moderate positive performance.

    MarketingAgent:
        Consistently poor performance.
    """

    memory = ExperienceMemory()

    # -------------------------------------------------
    # PricingAgent experiences
    # -------------------------------------------------

    pricing_rewards = [
        0.80,
        0.75,
        0.70,
        0.85,
        0.65
    ]

    for index, reward in enumerate(
        pricing_rewards,
        start=1
    ):
        memory.add(
            create_experience(
                experience_id=f"P-{index}",
                agent_name="PricingAgent",
                operation="INCREASE",
                reward=reward,
                status="SUCCESS",
                context={
                    "season": "FESTIVAL",
                    "demand_level": "HIGH",
                    "inventory_level": "LOW",
                    "market_condition": "HIGH_DEMAND"
                }
            )
        )

    # -------------------------------------------------
    # InventoryAgent experiences
    # -------------------------------------------------

    inventory_data = [
        (0.40, "SUCCESS"),
        (0.30, "SUCCESS"),
        (0.15, "NEUTRAL"),
        (0.25, "SUCCESS"),
        (0.10, "NEUTRAL")
    ]

    for index, data in enumerate(
        inventory_data,
        start=1
    ):
        reward, status = data

        memory.add(
            create_experience(
                experience_id=f"I-{index}",
                agent_name="InventoryAgent",
                operation="PROTECT_STOCK",
                reward=reward,
                status=status,
                context={
                    "season": "FESTIVAL",
                    "demand_level": "HIGH",
                    "inventory_level": "LOW",
                    "market_condition": "STOCK_PRESSURE"
                }
            )
        )

    # -------------------------------------------------
    # MarketingAgent experiences
    # -------------------------------------------------

    marketing_rewards = [
        -0.60,
        -0.50,
        -0.45,
        -0.70,
        -0.55
    ]

    for index, reward in enumerate(
        marketing_rewards,
        start=1
    ):
        memory.add(
            create_experience(
                experience_id=f"M-{index}",
                agent_name="MarketingAgent",
                operation="DECREASE",
                reward=reward,
                status="FAILURE",
                context={
                    "season": "FESTIVAL",
                    "demand_level": "HIGH",
                    "inventory_level": "LOW",
                    "market_condition": "HIGH_DEMAND"
                }
            )
        )

    return memory


def print_report(report) -> None:
    """
    Print the complete SCOE analysis report.
    """

    print("\nSCOE System Report")
    print("------------------")

    print(
        "System Health:",
        report.system_health_score
    )

    print(
        "System Status:",
        report.system_health_status
    )

    print(
        "Recommendation Count:",
        report.recommendation_count
    )

    print("\nAgent Rankings")
    print("--------------")

    for agent in report.agent_rankings:
        print(
            agent["rank"],
            agent["agent_name"],
            "| Reliability:",
            agent["reliability_score"],
            "| Average Reward:",
            agent["average_reward"],
            "| Success Rate:",
            agent["success_rate"],
            "| Failure Rate:",
            agent["failure_rate"]
        )

    print("\nStrong Agents")
    print("-------------")

    if report.strong_agents:
        for agent_name in report.strong_agents:
            print(agent_name)
    else:
        print("None")

    print("\nWeak Agents")
    print("-----------")

    if report.weak_agents:
        for agent_name in report.weak_agents:
            print(agent_name)
    else:
        print("None")

    print("\nBest Operations")
    print("---------------")

    if report.best_operations:
        for operation in report.best_operations:
            print(
                operation["operation"],
                "| Average Reward:",
                operation["average_reward"],
                "| Success Rate:",
                operation["success_rate"],
                "| Experiences:",
                operation["experience_count"]
            )
    else:
        print("None")

    print("\nWeak Operations")
    print("---------------")

    if report.weak_operations:
        for operation in report.weak_operations:
            print(
                operation["operation"],
                "| Average Reward:",
                operation["average_reward"],
                "| Failure Rate:",
                operation["failure_rate"],
                "| Experiences:",
                operation["experience_count"]
            )
    else:
        print("None")

    print("\nBusiness Patterns")
    print("-----------------")

    if report.business_patterns:
        for pattern in report.business_patterns:
            print(
                pattern["pattern"],
                "| Average Reward:",
                pattern["average_reward"],
                "| Success Rate:",
                pattern["success_rate"],
                "| Failure Rate:",
                pattern["failure_rate"],
                "| Experiences:",
                pattern["experience_count"]
            )
    else:
        print("None")

    print("\nOptimization Recommendations")
    print("----------------------------")

    if report.recommendations:
        for recommendation in report.recommendations:
            print(
                recommendation.priority,
                "->",
                recommendation.recommendation_type,
                "->",
                recommendation.target
            )

            print(
                "Message:",
                recommendation.message
            )

            print(
                "Expected Benefit:",
                recommendation.expected_benefit
            )

            print(
                "Confidence:",
                recommendation.confidence
            )

            print(
                "Evidence:",
                recommendation.evidence
            )

            print()
    else:
        print("None")


def test_system_report(report) -> None:
    """
    Validate SCOE report structure.
    """

    assert len(
        report.agent_rankings
    ) == 3

    assert (
        0.0
        <= report.system_health_score
        <= 1.0
    )

    assert report.system_health_status in {
        "EXCELLENT",
        "GOOD",
        "STABLE",
        "WEAK",
        "CRITICAL"
    }

    assert report.recommendation_count > 0


def test_agent_rankings(report) -> None:
    """
    Validate learned agent rankings.
    """

    assert (
        report.agent_rankings[0]["agent_name"]
        == "PricingAgent"
    )

    assert (
        report.agent_rankings[-1]["agent_name"]
        == "MarketingAgent"
    )

    assert (
        report.agent_rankings[0][
            "reliability_score"
        ]
        >
        report.agent_rankings[-1][
            "reliability_score"
        ]
    )


def test_agent_classification(report) -> None:
    """
    Validate strong and weak agent classification.
    """

    assert (
        "PricingAgent"
        in report.strong_agents
    )

    assert (
        "MarketingAgent"
        in report.weak_agents
    )


def test_operation_analysis(report) -> None:
    """
    Validate operation-level optimization analysis.
    """

    assert any(
        operation["operation"] == "INCREASE"
        for operation in report.best_operations
    )

    assert any(
        operation["operation"] == "DECREASE"
        for operation in report.weak_operations
    )


def test_agent_recommendations(report) -> None:
    """
    Validate agent optimization recommendations.
    """

    assert any(
        recommendation.recommendation_type
        == "AGENT_WEIGHT_INCREASE"
        and recommendation.target
        == "PricingAgent"
        for recommendation in report.recommendations
    )

    assert any(
        recommendation.recommendation_type
        == "AGENT_WEIGHT_REDUCTION"
        and recommendation.target
        == "MarketingAgent"
        for recommendation in report.recommendations
    )


def test_operation_recommendations(report) -> None:
    """
    Validate operation optimization recommendations.
    """

    assert any(
        recommendation.recommendation_type
        == "OPERATION_PREFERENCE"
        and recommendation.target
        == "INCREASE"
        for recommendation in report.recommendations
    )

    assert any(
        recommendation.recommendation_type
        == "OPERATION_AVOIDANCE"
        and recommendation.target
        == "DECREASE"
        for recommendation in report.recommendations
    )


def test_report_serialization(report) -> None:
    """
    Validate report serialization.
    """

    report_data = report.to_dict()

    assert isinstance(
        report_data,
        dict
    )

    assert (
        "system_health_score"
        in report_data
    )

    assert (
        "agent_rankings"
        in report_data
    )

    assert (
        "recommendations"
        in report_data
    )

    assert isinstance(
        report_data["recommendations"],
        list
    )


def run_tests() -> None:
    """
    Run the complete Self-Commerce Optimization
    Engine test suite.
    """

    memory = build_experience_memory()

    assert len(memory) == 15

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

    print_report(
        report
    )

    test_system_report(
        report
    )

    test_agent_rankings(
        report
    )

    test_agent_classification(
        report
    )

    test_operation_analysis(
        report
    )

    test_agent_recommendations(
        report
    )

    test_operation_recommendations(
        report
    )

    test_report_serialization(
        report
    )

    print(
        "\nSelf-Optimization Engine tests passed."
    )


if __name__ == "__main__":
    run_tests()