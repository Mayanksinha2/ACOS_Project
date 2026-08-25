from __future__ import annotations

from typing import Any

from ..presentation import money


def render_scenario_summary(st: Any, payload: dict) -> None:
    scenario = payload.get("scenario") or {}
    calculated = payload.get("calculated_metrics") or {}

    st.markdown('<div class="acos-section-title">Scenario summary</div>', unsafe_allow_html=True)

    row1 = st.columns(6)
    row1[0].metric("Product", scenario.get("product_id", "N/A"))
    row1[1].metric("Current price", money(scenario.get("current_price")))
    row1[2].metric("Inventory", f'{scenario.get("inventory", 0)} units')
    row1[3].metric("Base demand", f'{scenario.get("demand", 0):.0f}/100')
    row1[4].metric("Adjusted demand", f'{calculated.get("adjusted_demand", 0):.1f}/100')
    row1[5].metric(
        "Conversion",
        f'{calculated.get("conversion_rate", 0) * 100:.2f}%',
    )

    row2 = st.columns(5)
    row2[0].metric("Visitors", scenario.get("visitors", 0))
    row2[1].metric("Sales", scenario.get("sales", 0))
    row2[2].metric("Revenue", money(scenario.get("revenue")))
    row2[3].metric("Profit", money(scenario.get("profit")))
    row2[4].metric("Season", scenario.get("season", "N/A"))

    warnings = payload.get("input_warnings") or []
    if warnings:
        with st.expander(f"Input quality warnings ({len(warnings)})", expanded=True):
            for warning in warnings:
                st.warning(warning)
    else:
        st.success("Scenario inputs passed consistency checks.")
