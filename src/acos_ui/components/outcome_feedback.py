from __future__ import annotations

from typing import Any

import pandas as pd

from ..learning_bridge import ExistingLearningBridge
from ..learning_store import PersistentLearningStore
from ..learning_knowledge_sync import LearningKnowledgeSynchronizer
from ..outcome_evaluator import UIOutcomeEvaluator
from ..outcome_models import OutcomeMetrics
from ..presentation import build_final_plan, money


def _baseline_metrics(
    payload: dict,
) -> OutcomeMetrics:
    scenario = payload.get("scenario") or {}
    calculated = payload.get("calculated_metrics") or {}

    conversion = calculated.get(
        "conversion_rate",
        scenario.get("conversion_rate", 0.0),
    )

    return OutcomeMetrics(
        revenue=float(scenario.get("revenue") or 0.0),
        profit=float(scenario.get("profit") or 0.0),
        conversion_rate=float(conversion or 0.0),
        inventory_health=0.70,
        customer_satisfaction=0.70,
    )


def render_outcome_feedback(
    st: Any,
    payload: dict | None,
    store: PersistentLearningStore,
) -> None:
    st.title("Evaluate real business outcome")
    st.caption(
        "After applying an ACOS recommendation, enter the actual business "
        "performance. ACOS will calculate reward and store the experience."
    )

    if not payload:
        st.info(
            "Run an ACOS scenario before recording an outcome."
        )
        return

    run_id = str(payload.get("run_id") or "")
    if store.exists_for_run(run_id):
        st.warning(
            "This run already has an outcome evaluation. "
            "Open the Learning Dashboard to review it."
        )
        return

    plan = build_final_plan(payload)
    baseline = _baseline_metrics(payload)

    st.subheader("Decision being evaluated")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Product", plan.product_id)
    c2.metric("Winner", plan.winning_agent)
    c3.metric(
        "Price action",
        plan.price_operation.title(),
        f"{plan.price_change_percent:.2f}%",
    )
    c4.metric(
        "Recommended price",
        (
            money(plan.rounded_price)
            if plan.rounded_price is not None
            else "N/A"
        ),
    )

    st.divider()

    with st.form("acos_outcome_feedback"):
        before_tab, after_tab = st.tabs(
            ["Before decision", "After decision"]
        )

        with before_tab:
            b1, b2, b3 = st.columns(3)
            before_revenue = b1.number_input(
                "Revenue before (₹)",
                value=float(baseline.revenue),
                step=100.0,
            )
            before_profit = b2.number_input(
                "Profit before (₹)",
                value=float(baseline.profit),
                step=100.0,
            )
            before_conversion = b3.number_input(
                "Conversion before (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(baseline.conversion_rate * 100.0),
                step=0.1,
            )
            before_inventory = b1.slider(
                "Inventory health before",
                0.0,
                100.0,
                float(baseline.inventory_health * 100.0),
                1.0,
            )
            before_satisfaction = b2.slider(
                "Customer satisfaction before",
                0.0,
                100.0,
                float(baseline.customer_satisfaction * 100.0),
                1.0,
            )

        with after_tab:
            a1, a2, a3 = st.columns(3)
            after_revenue = a1.number_input(
                "Revenue after (₹)",
                value=float(baseline.revenue),
                step=100.0,
            )
            after_profit = a2.number_input(
                "Profit after (₹)",
                value=float(baseline.profit),
                step=100.0,
            )
            after_conversion = a3.number_input(
                "Conversion after (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(baseline.conversion_rate * 100.0),
                step=0.1,
            )
            after_inventory = a1.slider(
                "Inventory health after",
                0.0,
                100.0,
                float(baseline.inventory_health * 100.0),
                1.0,
            )
            after_satisfaction = a2.slider(
                "Customer satisfaction after",
                0.0,
                100.0,
                float(baseline.customer_satisfaction * 100.0),
                1.0,
            )

        unchanged_confirmation = st.checkbox(
            "I confirm that there was genuinely no measurable change.",
            help=(
                "Required only when every after-value is identical to the "
                "before-value. This prevents accidental neutral experiences."
            ),
        )

        notes = st.text_area(
            "Outcome notes",
            placeholder=(
                "Example: Price was changed on 1 August and performance "
                "was measured for the next seven days."
            ),
        )

        submitted = st.form_submit_button(
            "Evaluate and store outcome",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        st.info(
            "Reward weights: Profit 35%, Conversion 25%, Revenue 20%, "
            "Inventory health 10%, Customer satisfaction 10%."
        )
        return

    before = OutcomeMetrics(
        revenue=float(before_revenue),
        profit=float(before_profit),
        conversion_rate=float(before_conversion) / 100.0,
        inventory_health=float(before_inventory) / 100.0,
        customer_satisfaction=float(before_satisfaction) / 100.0,
    )
    after = OutcomeMetrics(
        revenue=float(after_revenue),
        profit=float(after_profit),
        conversion_rate=float(after_conversion) / 100.0,
        inventory_health=float(after_inventory) / 100.0,
        customer_satisfaction=float(after_satisfaction) / 100.0,
    )

    unchanged = all(
        abs(after_value - before_value) < 1e-12
        for before_value, after_value in (
            (before.revenue, after.revenue),
            (before.profit, after.profit),
            (before.conversion_rate, after.conversion_rate),
            (before.inventory_health, after.inventory_health),
            (before.customer_satisfaction, after.customer_satisfaction),
        )
    )

    if unchanged and not unchanged_confirmation:
        st.error(
            "Every after-metric is identical to the before-metric. "
            "Enter the real result or confirm that there was genuinely "
            "no measurable change."
        )
        return

    try:
        evaluation = UIOutcomeEvaluator().evaluate(
            payload=payload,
            before=before,
            after=after,
            notes=notes,
        )
        store.save(evaluation)
        learned_entries = LearningKnowledgeSynchronizer(
            store
        ).synchronize()
    except Exception as error:
        st.exception(error)
        return

    if evaluation.classification == "SUCCESS":
        st.success(
            f"Outcome stored as SUCCESS with reward {evaluation.reward:.3f}."
        )
    elif evaluation.classification == "FAILURE":
        st.error(
            f"Outcome stored as FAILURE with reward {evaluation.reward:.3f}."
        )
    else:
        st.info(
            f"Outcome stored as NEUTRAL with reward {evaluation.reward:.3f}."
        )

    rows = [
        {
            "Metric": item.metric,
            "Before": item.before,
            "After": item.after,
            "Change": f"{item.relative_change * 100:+.2f}%",
            "Weight": f"{item.weight * 100:.0f}%",
            "Reward contribution": round(item.contribution, 4),
        }
        for item in evaluation.metric_changes
    ]
    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    if learned_entries:
        st.success(
            f"{len(learned_entries)} learned knowledge entries were "
            "synchronized. Future MOCRA scores can now be adjusted by "
            "the observed outcome history."
        )
    else:
        st.caption(
            "Learning knowledge is synchronized after at least three "
            "non-trivial outcomes support an agent or operation pattern."
        )

    bridge = ExistingLearningBridge()
    availability = bridge.availability()
    available_count = sum(availability.values())

    with st.expander("Learning-engine integration status"):
        st.write(
            f"{available_count} of {len(availability)} existing research "
            "learning modules were importable."
        )
        for module, available in availability.items():
            st.write(
                ("✓" if available else "○"),
                module,
            )
        st.caption(
            "Phase 3B stores a stable feedback payload without guessing "
            "undocumented learning-engine APIs. This prevents breaking the "
            "working research architecture."
        )
