from __future__ import annotations

from typing import Any

import pandas as pd

from ..learning_knowledge_sync import LearningKnowledgeSynchronizer
from ..learning_store import PersistentLearningStore


def render_learning_dashboard(
    st: Any,
    store: PersistentLearningStore,
) -> None:
    st.title("ACOS learning dashboard")
    st.caption(
        "Persistent outcome feedback and evidence-supported learning."
    )

    summary = store.summary()
    evaluations = store.list_evaluations()

    metrics = st.columns(6)
    metrics[0].metric("Experiences", summary["total"])
    metrics[1].metric("Successful", summary["successes"])
    metrics[2].metric("Failed", summary["failures"])
    metrics[3].metric("Neutral", summary["neutral"])
    metrics[4].metric(
        "Average reward",
        f'{summary["average_reward"]:.3f}',
    )
    metrics[5].metric(
        "Best supported agent",
        summary["best_agent"],
        (
            f'{summary["best_agent_success_rate"] * 100:.0f}% success'
            if summary["best_agent"] != "Insufficient evidence"
            else None
        ),
    )

    if not evaluations:
        st.info(
            "No real outcomes have been stored yet. Run a scenario, "
            "apply the recommendation, then open Evaluate outcome."
        )
        return

    if all(abs(item.reward) < 1e-12 for item in evaluations):
        st.warning(
            "All stored outcomes are neutral because their before and after "
            "metrics are identical. These records do not yet provide evidence "
            "that one agent or operation performs better."
        )

    reward_rows = [
        {
            "Evaluation": item.evaluation_id[:8],
            "Reward": item.reward,
        }
        for item in reversed(evaluations[:30])
    ]
    st.subheader("Reward trend")
    st.line_chart(
        pd.DataFrame(reward_rows).set_index("Evaluation"),
        height=260,
        use_container_width=True,
    )

    agent_stats = store.agent_statistics()
    st.subheader("Agent evidence and provisional reliability")
    st.caption(
        "Reliability is provisional until an agent has at least five "
        "evaluated outcomes. Fewer observations are shown as insufficient."
    )

    if agent_stats:
        display_rows = []
        chart_rows = []
        for row in agent_stats:
            sufficiently_supported = row["decision_count"] >= 5
            display_rows.append(
                {
                    "Agent": row["agent"],
                    "Evaluated outcomes": row["decision_count"],
                    "Average reward": round(
                        row["average_reward"],
                        3,
                    ),
                    "Success rate": (
                        f'{row["success_rate"] * 100:.1f}%'
                    ),
                    "Failure rate": (
                        f'{row["failure_rate"] * 100:.1f}%'
                    ),
                    "Reliability status": (
                        f'{row["reliability"] * 100:.1f}% provisional'
                        if sufficiently_supported
                        else "Insufficient evidence"
                    ),
                }
            )
            if sufficiently_supported:
                chart_rows.append(
                    {
                        "Agent": row["agent"],
                        "Provisional reliability": row["reliability"],
                        "Average reward": row["average_reward"],
                    }
                )

        if chart_rows:
            st.bar_chart(
                pd.DataFrame(chart_rows).set_index("Agent"),
                horizontal=True,
                height=280,
                use_container_width=True,
            )
        st.dataframe(
            display_rows,
            use_container_width=True,
            hide_index=True,
        )

    operation_stats = store.operation_statistics()
    st.subheader("Operation performance")
    st.dataframe(
        [
            {
                "Operation": row["operation"],
                "Evaluated outcomes": row["decision_count"],
                "Average reward": round(
                    row["average_reward"],
                    3,
                ),
                "Success rate": (
                    f'{row["success_rate"] * 100:.1f}%'
                ),
                "Learning status": (
                    "Eligible for knowledge synchronization"
                    if (
                        row["decision_count"] >= 3
                        and abs(row["average_reward"]) >= 0.05
                    )
                    else "More non-trivial evidence required"
                ),
            }
            for row in operation_stats
        ],
        use_container_width=True,
        hide_index=True,
    )

    synchronizer = LearningKnowledgeSynchronizer(store)
    sync_status = synchronizer.status()
    st.info(
        "Future MOCRA adjustment activates after at least "
        f"{sync_status['minimum_experiences']} supported outcomes with "
        f"|average reward| ≥ {sync_status['minimum_absolute_reward']:.2f}."
    )

    st.subheader("Recent learning experiences")
    st.dataframe(
        [
            {
                "Time": item.evaluated_at,
                "Product": item.product_id,
                "Agent": item.winning_agent,
                "Action": (
                    f"{item.primary_operation} "
                    f"{item.primary_value:g} "
                    f"{item.primary_unit}"
                ),
                "Reward": item.reward,
                "Outcome": item.classification,
                "Notes": item.notes,
            }
            for item in evaluations[:50]
        ],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Persistent storage information"):
        st.code(str(store.database_path))
        st.caption(
            "Outcome feedback survives application and computer restarts."
        )
