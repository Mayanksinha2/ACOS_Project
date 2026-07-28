from application.acos_application_service import (
    ACOSApplicationService,
)
from application.business_state_builder import (
    BusinessStateBuilder,
)


def display_proposals(result) -> None:
    print("\nAgent Proposals")
    print("-" * 70)

    for proposal in result.proposals:
        action = proposal.business_action

        print(
            f"{proposal.agent_id:<18}"
            f"{action.operation:<22}"
            f"Confidence: {proposal.confidence:.2f}  "
            f"Risk: {proposal.risk:.2f}"
        )


def test_complete_acos_run() -> None:
    state = (
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="PROD-ACOS-001",
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

    result = service.run(
        state
    )

    print("\nACOS RUN RESULT")
    print("=" * 70)

    print("Run ID:", result.run_id)
    print("Status:", result.status)
    print(
        "Negotiation required:",
        result.negotiation_required,
    )
    print(
        "Conflicts:",
        result.conflict_count,
    )

    display_proposals(
        result
    )

    print("\nMOCRA Result")
    print("-" * 70)
    print(result.mocra_result)

    print("\nFinal Decision")
    print("-" * 70)
    print(result.final_decision)

    print("\nSummary")
    print("-" * 70)
    print(result.summary())

    assert result.status == "COMPLETED"
    assert result.successful
    assert result.proposal_count == 3
    assert result.final_decision is not None

    operations = {
        proposal.agent_id:
        proposal.business_action.operation
        for proposal in result.proposals
    }

    assert (
        operations["PricingAgent"]
        == "INCREASE"
    )

    assert (
        operations["InventoryAgent"]
        == "PROTECT_STOCK"
    )

    assert (
        operations["MarketingAgent"]
        == "DECREASE"
    )


def test_proposals_only() -> None:
    state = (
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="PROD-PROPOSAL-001",
            inventory=80,
            demand=55,
            conversion_rate=0.07,
            advertising_cost=600,
        )
    )

    service = ACOSApplicationService()

    proposals = (
        service.generate_proposals_only(
            state
        )
    )

    assert len(proposals) == 3

    for proposal in proposals:
        assert (
            proposal.business_action.target
            == "PROD-PROPOSAL-001"
        )


def test_service_reuse() -> None:
    service = ACOSApplicationService()

    first_state = (
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="PROD-REUSE-001",
            inventory=15,
            demand=90,
            conversion_rate=0.03,
            advertising_cost=1000,
        )
    )

    second_state = (
        BusinessStateBuilder
        .build_from_manual_input(
            product_id="PROD-REUSE-002",
            inventory=150,
            demand=30,
            conversion_rate=0.08,
            advertising_cost=500,
        )
    )

    first_result = service.run(
        first_state
    )

    second_result = service.run(
        second_state
    )

    assert first_result.successful
    assert second_result.successful

    assert (
        first_result.run_id
        != second_result.run_id
    )

    assert all(
        proposal.business_action.target
        == "PROD-REUSE-002"
        for proposal
        in second_result.proposals
    )


def run_tests() -> None:
    test_complete_acos_run()
    test_proposals_only()
    test_service_reuse()

    print(
        "\nACOS Application Service "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()