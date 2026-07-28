from learning.outcome_evaluator import OutcomeEvaluator


def test_successful_outcome():
    evaluator = OutcomeEvaluator()

    before_metrics = {
        "revenue": 10000,
        "profit": 2500,
        "conversion_rate": 2.0,
        "inventory_health": 0.60,
        "customer_satisfaction": 0.70
    }

    after_metrics = {
        "revenue": 11200,
        "profit": 3000,
        "conversion_rate": 2.3,
        "inventory_health": 0.75,
        "customer_satisfaction": 0.78
    }

    result = evaluator.evaluate(
        decision_id="DECISION-001",
        target="PRODUCT-001",
        before_metrics=before_metrics,
        after_metrics=after_metrics
    )

    print("\nSuccessful Outcome Test")
    print("-----------------------")
    print("Decision ID:", result.decision_id)
    print("Target:", result.target)
    print(
        "Revenue Change:",
        result.revenue_change_percentage
    )
    print(
        "Profit Change:",
        result.profit_change_percentage
    )
    print(
        "Conversion Change:",
        result.conversion_change_percentage
    )
    print(
        "Inventory Health Change:",
        result.inventory_health_change
    )
    print(
        "Customer Satisfaction Change:",
        result.customer_satisfaction_change
    )
    print("Metric Scores:", result.metric_scores)
    print("Overall Reward:", result.overall_reward)
    print("Outcome Status:", result.outcome_status)

    assert result.decision_id == "DECISION-001"
    assert result.target == "PRODUCT-001"
    assert result.revenue_change_percentage == 12.0
    assert result.profit_change_percentage == 20.0
    assert result.conversion_change_percentage == 15.0
    assert result.overall_reward > 0
    assert result.outcome_status == "SUCCESS"
    assert result.is_successful() is True


def test_failed_outcome():
    evaluator = OutcomeEvaluator()

    before_metrics = {
        "revenue": 10000,
        "profit": 2500,
        "conversion_rate": 2.0,
        "inventory_health": 0.75,
        "customer_satisfaction": 0.80
    }

    after_metrics = {
        "revenue": 8000,
        "profit": 1800,
        "conversion_rate": 1.5,
        "inventory_health": 0.50,
        "customer_satisfaction": 0.60
    }

    result = evaluator.evaluate(
        decision_id="DECISION-002",
        target="PRODUCT-001",
        before_metrics=before_metrics,
        after_metrics=after_metrics
    )

    print("\nFailed Outcome Test")
    print("-------------------")
    print("Overall Reward:", result.overall_reward)
    print("Outcome Status:", result.outcome_status)

    assert result.overall_reward < 0
    assert result.outcome_status == "FAILURE"
    assert result.is_failure() is True


def test_neutral_outcome():
    evaluator = OutcomeEvaluator()

    before_metrics = {
        "revenue": 10000,
        "profit": 2500,
        "conversion_rate": 2.0,
        "inventory_health": 0.70,
        "customer_satisfaction": 0.75
    }

    after_metrics = {
        "revenue": 10100,
        "profit": 2525,
        "conversion_rate": 2.01,
        "inventory_health": 0.70,
        "customer_satisfaction": 0.75
    }

    result = evaluator.evaluate(
        decision_id="DECISION-003",
        target="PRODUCT-001",
        before_metrics=before_metrics,
        after_metrics=after_metrics
    )

    print("\nNeutral Outcome Test")
    print("--------------------")
    print("Overall Reward:", result.overall_reward)
    print("Outcome Status:", result.outcome_status)

    assert result.outcome_status == "NEUTRAL"


def test_invalid_weights():
    try:
        OutcomeEvaluator(
            weights={
                "revenue": 0.30,
                "profit": 0.30,
                "conversion": 0.20,
                "inventory_health": 0.10,
                "customer_satisfaction": 0.05
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
    test_successful_outcome()
    test_failed_outcome()
    test_neutral_outcome()
    test_invalid_weights()

    print("\nOutcome Evaluator tests passed.")