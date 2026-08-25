from __future__ import annotations

from typing import Any

from ..presentation import (
    actual_conflicts,
    build_final_plan,
    money,
)


def render_executive_header(st: Any, payload: dict) -> None:
    plan = build_final_plan(payload)
    status = payload.get("status", "UNKNOWN")
    run_id = payload.get("run_id", "-")

    st.markdown(
        f"""
        <div class="acos-hero">
          <div class="acos-muted">ACOS executive decision • {status}</div>
          <h2>{plan.business_summary}</h2>
          <div class="acos-muted">
            Product: {plan.product_id} &nbsp;•&nbsp;
            Resolution: {plan.resolution_method} &nbsp;•&nbsp;
            Run ID: {run_id}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    conflicts = actual_conflicts(payload.get("conflicts"))
    columns = st.columns(6)
    columns[0].metric("Status", status)
    columns[1].metric("Agents", len(payload.get("proposals") or []))
    columns[2].metric("Actual conflicts", len(conflicts))
    columns[3].metric(
        "Agreement",
        "Reached" if plan.agreement_reached else "Not reached",
    )
    columns[4].metric("Winning agent", plan.winning_agent)
    columns[5].metric(
        "MOCRA score",
        f"{plan.winning_score:.3f}" if plan.winning_score is not None else "N/A",
    )


def render_business_plan(st: Any, payload: dict) -> None:
    plan = build_final_plan(payload)

    st.markdown('<div class="acos-section-title">Final coordinated business plan</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="acos-plan">
          <strong>Primary recommendation</strong><br>
          {plan.business_summary}
        </div>
        """,
        unsafe_allow_html=True,
    )

    price, inventory, marketing = st.columns(3)

    with price:
        st.subheader("Price")
        if plan.current_price is not None:
            st.metric(
                "Recommended selling price",
                money(plan.rounded_price),
                delta=(
                    f"-{plan.price_change_percent:.2f}%"
                    if plan.price_operation == "DECREASE"
                    else (
                        f"+{plan.price_change_percent:.2f}%"
                        if plan.price_operation == "INCREASE"
                        else "0%"
                    )
                ),
                delta_color="inverse" if plan.price_operation == "DECREASE" else "normal",
            )
            st.caption(
                f"Exact calculated value: {money(plan.recommended_price)} • "
                f"Current price: {money(plan.current_price)}"
            )
        else:
            st.metric(
                "Price action",
                plan.price_operation,
                f"{plan.price_change_percent:.2f}%",
            )

    with inventory:
        st.subheader("Inventory")
        st.metric(
            "Recommended action",
            plan.inventory_operation.replace("_", " ").title(),
            f"{plan.inventory_value:g} {plan.inventory_unit}",
        )
        st.caption("Inventory remains a coordinated supporting action.")

    with marketing:
        st.subheader("Marketing")
        marketing_label = (
            "Marketing-supported price action"
            if plan.marketing_operation.upper() in {
                "DECREASE", "INCREASE", "MAINTAIN"
            }
            else "Recommended marketing action"
        )
        st.metric(
            marketing_label,
            plan.marketing_operation.replace("_", " ").title(),
            f"{plan.marketing_value:g} {plan.marketing_unit}",
        )
        st.caption("The Marketing Agent's action remains visible in the plan.")

    impact, tradeoffs = st.columns(2)
    with impact:
        st.success("Expected positive impact")
        for item in plan.positive_impact:
            st.write("✓", item)
    with tradeoffs:
        st.warning("Trade-offs to monitor")
        for item in plan.trade_offs or ("No major trade-off was identified.",):
            st.write("•", item)
