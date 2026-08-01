import tempfile
from pathlib import Path

from knowledge.knowledge_base import (
    KnowledgeBase
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


def print_knowledge(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Print stored knowledge for inspection.
    """

    print("\nPersistent Knowledge Base")
    print("-------------------------")

    summary = knowledge_base.summary()

    print(
        "Total Entries:",
        summary["total_entries"]
    )

    print(
        "Active Entries:",
        summary["active_entries"]
    )

    print(
        "Inactive Entries:",
        summary["inactive_entries"]
    )

    print(
        "Average Confidence:",
        summary["average_confidence"]
    )

    print(
        "Storage Path:",
        summary["storage_path"]
    )

    print("\nKnowledge Type Counts")
    print("---------------------")

    for knowledge_type, count in (
        summary["type_counts"].items()
    ):
        print(
            knowledge_type,
            "->",
            count
        )

    print("\nStored Knowledge")
    print("----------------")

    for entry in knowledge_base.get_all():
        print(
            entry.priority,
            "->",
            entry.knowledge_type,
            "->",
            entry.target
        )

        print(
            "Statement:",
            entry.statement
        )

        print(
            "Confidence:",
            round(
                entry.confidence,
                4
            )
        )

        print(
            "Expected Benefit:",
            round(
                entry.expected_benefit,
                4
            )
        )

        print(
            "Occurrences:",
            entry.occurrence_count
        )

        print(
            "Active:",
            entry.is_active
        )

        print()


def build_scoe_report():
    """
    Generate a valid SCOE report.
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

    return scoe.analyze_system()


def test_report_integration(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Test conversion from SCOE report to knowledge.
    """

    report = build_scoe_report()

    integrator = KnowledgeIntegrator(
        knowledge_base
    )

    stored_entries = integrator.integrate_report(
        report
    )

    assert len(
        stored_entries
    ) > 0

    assert len(
        knowledge_base
    ) > 0

    assert any(
        entry.knowledge_type
        == "OPERATION_PREFERENCE"
        and entry.target
        == "INCREASE"
        for entry in knowledge_base.get_all()
    )

    assert any(
        entry.knowledge_type
        == "OPERATION_AVOIDANCE"
        and entry.target
        == "DECREASE"
        for entry in knowledge_base.get_all()
    )

    assert any(
        entry.knowledge_type
        == "AGENT_WEIGHT_INCREASE"
        and entry.target
        == "PricingAgent"
        for entry in knowledge_base.get_all()
    )

    assert any(
        entry.knowledge_type
        == "AGENT_WEIGHT_REDUCTION"
        and entry.target
        == "MarketingAgent"
        for entry in knowledge_base.get_all()
    )

    assert any(
        entry.knowledge_type
        == "SYSTEM_HEALTH"
        and entry.target
        == "ACOS"
        for entry in knowledge_base.get_all()
    )


def test_duplicate_reinforcement(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Reintegrating the same report should reinforce
    knowledge instead of creating duplicates.
    """

    original_count = len(
        knowledge_base
    )

    preferred_operation = (
        knowledge_base.get_by_unique_key(
            "OPERATION_PREFERENCE::INCREASE"
        )
    )

    assert preferred_operation is not None

    original_occurrence_count = (
        preferred_operation.occurrence_count
    )

    report = build_scoe_report()

    integrator = KnowledgeIntegrator(
        knowledge_base
    )

    integrator.integrate_report(
        report
    )

    assert len(
        knowledge_base
    ) == original_count

    reinforced_entry = (
        knowledge_base.get_by_unique_key(
            "OPERATION_PREFERENCE::INCREASE"
        )
    )

    assert reinforced_entry is not None

    assert (
        reinforced_entry.occurrence_count
        ==
        original_occurrence_count + 1
    )


def test_relevant_knowledge_retrieval(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Test context-aware knowledge retrieval.
    """

    pricing_knowledge = (
        knowledge_base.get_relevant_knowledge(
            agent_name="PricingAgent",
            operation="INCREASE",
            context={
                "season": "FESTIVAL",
                "demand_level": "HIGH",
                "inventory_level": "LOW"
            },
            minimum_confidence=0.50
        )
    )

    assert len(
        pricing_knowledge
    ) > 0

    assert any(
        entry.target
        in {
            "PricingAgent",
            "INCREASE",
            "SEASON=FESTIVAL",
            "DEMAND_LEVEL=HIGH",
            "INVENTORY_LEVEL=LOW"
        }
        for entry in pricing_knowledge
    )


def test_type_queries(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Test operation and agent-specific queries.
    """

    preferred_operations = (
        knowledge_base.get_preferred_operations()
    )

    avoided_operations = (
        knowledge_base.get_avoided_operations()
    )

    pricing_agent_knowledge = (
        knowledge_base.get_agent_knowledge(
            "PricingAgent"
        )
    )

    assert any(
        entry.target == "INCREASE"
        for entry in preferred_operations
    )

    assert any(
        entry.target == "DECREASE"
        for entry in avoided_operations
    )

    assert len(
        pricing_agent_knowledge
    ) > 0


def test_activation_control(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Test activating and deactivating knowledge.
    """

    entry = (
        knowledge_base.get_preferred_operations()[0]
    )

    result = knowledge_base.deactivate(
        entry.knowledge_id
    )

    assert result is True

    assert entry.is_active is False

    active_preferred_operations = (
        knowledge_base.get_preferred_operations()
    )

    assert all(
        active_entry.knowledge_id
        != entry.knowledge_id
        for active_entry
        in active_preferred_operations
    )

    result = knowledge_base.activate(
        entry.knowledge_id
    )

    assert result is True

    assert entry.is_active is True


def test_manual_knowledge(
    knowledge_base: KnowledgeBase
) -> None:
    """
    Test manually adding knowledge.
    """

    manual_entry = KnowledgeEntry(
        knowledge_type="BUSINESS_RULE",
        target="LOW_STOCK",
        statement=(
            "Avoid aggressive discounts when "
            "inventory is critically low."
        ),
        confidence=0.90,
        expected_benefit=0.30,
        priority="HIGH",
        evidence={
            "inventory_level": "LOW",
            "recommended_action": (
                "PROTECT_STOCK"
            )
        },
        source="RESEARCHER"
    )

    stored_entry = knowledge_base.add(
        manual_entry
    )

    assert stored_entry.target == "LOW_STOCK"

    assert (
        knowledge_base.get_by_id(
            stored_entry.knowledge_id
        )
        is not None
    )


def test_persistence(
    storage_path: str,
    original_knowledge_base: KnowledgeBase
) -> None:
    """
    Test saving and loading knowledge.
    """

    original_knowledge_base.save()

    assert Path(
        storage_path
    ).exists()

    restored_knowledge_base = KnowledgeBase(
        storage_path=storage_path,
        auto_load=True,
        auto_save=False
    )

    assert len(
        restored_knowledge_base
    ) == len(
        original_knowledge_base
    )

    assert any(
        entry.knowledge_type
        == "SYSTEM_HEALTH"
        for entry
        in restored_knowledge_base.get_all()
    )

    assert any(
        entry.target == "PricingAgent"
        for entry
        in restored_knowledge_base.get_all()
    )

    assert any(
        entry.target == "INCREASE"
        for entry
        in restored_knowledge_base.get_all()
    )


def run_tests() -> None:
    """
    Run the complete persistent Knowledge Base test.
    """

    with tempfile.TemporaryDirectory() as directory:
        storage_path = str(
            Path(directory)
            / "knowledge_base.json"
        )

        knowledge_base = KnowledgeBase(
            storage_path=storage_path,
            auto_load=True,
            auto_save=True
        )

        test_report_integration(
            knowledge_base
        )

        test_duplicate_reinforcement(
            knowledge_base
        )

        test_relevant_knowledge_retrieval(
            knowledge_base
        )

        test_type_queries(
            knowledge_base
        )

        test_activation_control(
            knowledge_base
        )

        test_manual_knowledge(
            knowledge_base
        )

        test_persistence(
            storage_path=storage_path,
            original_knowledge_base=(
                knowledge_base
            )
        )

        print_knowledge(
            knowledge_base
        )

        print(
            "\nPersistent Knowledge Base tests passed."
        )


if __name__ == "__main__":
    run_tests()