from __future__ import annotations

from typing import Any

from ..learning_store import PersistentLearningStore


def render_experience_detail(
    st: Any,
    store: PersistentLearningStore,
) -> None:
    st.title("Learning experience explorer")
    evaluations = store.list_evaluations()

    if not evaluations:
        st.info("No persistent learning experiences are available.")
        return

    options = {
        (
            f"{item.evaluated_at} • {item.product_id} • "
            f"{item.classification} • {item.reward:.3f}"
        ): item
        for item in evaluations
    }

    selected_label = st.selectbox(
        "Select an experience",
        list(options),
    )
    evaluation = options[selected_label]

    metrics = st.columns(5)
    metrics[0].metric("Outcome", evaluation.classification)
    metrics[1].metric("Reward", f"{evaluation.reward:.3f}")
    metrics[2].metric("Winning agent", evaluation.winning_agent)
    metrics[3].metric("Decision", evaluation.primary_operation)
    metrics[4].metric("Product", evaluation.product_id)

    st.subheader("Metric-level explanation")
    st.dataframe(
        [
            {
                "Metric": item.metric,
                "Before": item.before,
                "After": item.after,
                "Relative change": (
                    f"{item.relative_change * 100:+.2f}%"
                ),
                "Weight": f"{item.weight * 100:.0f}%",
                "Contribution": round(
                    item.contribution,
                    4,
                ),
            }
            for item in evaluation.metric_changes
        ],
        use_container_width=True,
        hide_index=True,
    )

    if evaluation.notes:
        st.info(evaluation.notes)

    with st.expander("Stored run snapshot"):
        st.json(
            evaluation.run_snapshot,
            expanded=False,
        )

    confirm = st.checkbox(
        "I understand this permanently deletes the selected experience."
    )
    if st.button(
        "Delete selected experience",
        disabled=not confirm,
    ):
        store.delete(evaluation.evaluation_id)
        st.success("Experience deleted.")
        st.rerun()
