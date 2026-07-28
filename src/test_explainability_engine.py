from application.acos_application_service import (
    ACOSApplicationService,
)
from application.business_state_builder import (
    BusinessStateBuilder,
)
from explainability.explainability_engine import (
    ExplainabilityEngine,
)


def print_explanation(
    explanation,
) -> None:
    print("\nACOS DECISION EXPLANATION")
    print("=" * 75)

    print(
        "Explanation ID:",
        explanation.explanation_id,
    )

    print(
        "Run ID:",
        explanation.run_id,
    )

    print(
        "Status:",
        explanation.status,
    )

    print(
        "Product:",
        explanation.product_id,
    )

    print(
        "Negotiation required:",
        explanation.negotiation_required,
    )

    print(
        "Agreement reached:",
        explanation.agreement_reached,
    )

    print(
        "Selected agent:",
        explanation.selected_agent,
    )

    print(
        "Selected operation:",
        explanation.selected_operation,
    )

    print("\nAGENT PROPOSALS")
    print("-" * 75)

    for proposal in (
        explanation.proposal_explanations
    ):
        print(
            "\nAgent:",
            proposal.agent_id,
        )

        print(
            "Operation:",
            proposal.operation,
        )

        print(
            "Confidence:",
            proposal.confidence,
        )

        print(
            "Risk:",
            proposal.risk,
        )

        print(
            "MOCRA score:",
            proposal.score,
        )

        print(
            "Selected:",
            proposal.selected,
        )

        print(
            "Explanation:",
            proposal.explanation,
        )

    print("\nCONFLICTS")
    print("-" * 75)

    for line in explanation.conflict_summary:
        print("-", line)

    print("\nNEGOTIATION")
    print("-" * 75)

    for line in (
        explanation.negotiation_summary
    ):
        print("-", line)

    print("\nMOCRA")
    print("-" * 75)

    for line in explanation.mocra_summary:
        print("-", line)

    print("\nFINAL DECISION")
    print("-" * 75)

    print(
        explanation.final_decision_summary
    )

    print("\nCONFIDENCE SUMMARY")
    print("-" * 75)

    print(
        explanation.confidence_summary
    )

    print("\nRISK SUMMARY")
    print("-" * 75)

    print(
        explanation.risk_summary
    )

    print("\nBUSINESS INTERPRETATION")
    print("-" * 75)

    print(
        explanation.business_interpretation
    )


def test_complete_explanation() -> None:
    business_state = (
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="EXPLAIN-001",
            inventory=15,
            demand=85,
            conversion_rate=0.03,
            advertising_cost=1200,
            visitors=100,
            sales=3,
            revenue=2397,
            profit=1137,
            season="FESTIVAL",
        )
    )

    service = ACOSApplicationService()

    run_result = service.run(
        business_state
    )

    engine = ExplainabilityEngine()

    explanation = engine.explain(
        run_result
    )

    print_explanation(
        explanation
    )

    assert explanation.status == "COMPLETED"

    assert explanation.successful

    assert explanation.product_id == (
        "EXPLAIN-001"
    )

    assert len(
        explanation.proposal_explanations
    ) == 3

    assert explanation.selected_agent == (
        "InventoryAgent"
    )

    assert explanation.selected_operation == (
        "PROTECT_STOCK"
    )

    assert explanation.negotiation_required

    assert explanation.agreement_reached

    assert explanation.final_decision_summary

    selected_proposals = [
        proposal
        for proposal
        in explanation.proposal_explanations
        if proposal.selected
    ]

    assert len(selected_proposals) == 1

    assert (
        selected_proposals[0].agent_id
        == "InventoryAgent"
    )


def test_explanation_dictionary() -> None:
    business_state = (
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="EXPLAIN-002",
            inventory=100,
            demand=45,
            conversion_rate=0.07,
            advertising_cost=500,
        )
    )

    run_result = (
        ACOSApplicationService()
        .run(
            business_state
        )
    )

    explanation = (
        ExplainabilityEngine()
        .explain(
            run_result
        )
    )

    data = explanation.to_dict()

    assert isinstance(data, dict)

    assert data["run_id"] == (
        run_result.run_id
    )

    assert (
        len(
            data[
                "proposal_explanations"
            ]
        )
        == 3
    )

    assert (
        "business_interpretation"
        in data
    )


def test_multiple_explanations() -> None:
    service = ACOSApplicationService()

    states = [
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="MULTI-001",
            inventory=10,
            demand=90,
            conversion_rate=0.02,
            advertising_cost=1400,
        ),
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="MULTI-002",
            inventory=150,
            demand=30,
            conversion_rate=0.08,
            advertising_cost=400,
        ),
    ]

    run_results = [
        service.run(state)
        for state in states
    ]

    explanations = (
        ExplainabilityEngine()
        .explain_many(
            run_results
        )
    )

    assert len(explanations) == 2

    assert all(
        explanation.successful
        for explanation
        in explanations
    )

    assert {
        explanation.product_id
        for explanation
        in explanations
    } == {
        "MULTI-001",
        "MULTI-002",
    }


def run_tests() -> None:
    test_complete_explanation()
    test_explanation_dictionary()
    test_multiple_explanations()

    print(
        "\nExplainability Engine "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()