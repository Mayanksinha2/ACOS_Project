from __future__ import annotations

import json

import streamlit as st

from .application_adapter import ACOSUIAdapter, ScenarioInput
from .components.dashboard import render_summary
from .components.decision import render_decision
from .components.history import render_history
from .components.negotiation import render_negotiation
from .components.proposals import render_proposals
from .session_state import HISTORY_KEY, LATEST_KEY, initialize_session, save_run


def _scenario_form() -> ScenarioInput | None:
    with st.form("acos_scenario_form"):
        st.subheader("Commerce scenario")
        basic, market, performance = st.tabs(["Product", "Market", "Performance"])
        with basic:
            c1, c2, c3 = st.columns(3)
            product_id = c1.text_input("Product ID", "PROD-DEMO-001")
            current_price = c2.number_input("Current price (₹)", min_value=0.0, value=799.0, step=10.0)
            unit_cost = c3.number_input("Unit cost (₹)", min_value=0.0, value=420.0, step=10.0)
            inventory = c1.number_input("Inventory", min_value=0, value=25, step=1)
            marketing_budget = c2.number_input("Marketing budget (₹)", min_value=0.0, value=25000.0, step=500.0)
        with market:
            c1, c2, c3 = st.columns(3)
            demand = c1.slider("Base demand score", 0.0, 100.0, 80.0, 1.0)
            season = c2.selectbox("Season", ["NORMAL", "FESTIVAL", "SALE", "OFF_SEASON"])
            demand_multiplier = c3.number_input("Demand multiplier", min_value=0.1, value=1.2, step=0.1)
            competitor_price_factor = c1.number_input("Competitor price factor", min_value=0.1, value=1.0, step=0.05)
            advertising_cost = c2.number_input("Advertising cost (₹)", min_value=0.0, value=1000.0, step=100.0)
            c3.caption("Adjusted demand is calculated as base demand × multiplier (capped at 100).")
        with performance:
            c1, c2, c3 = st.columns(3)
            visitors = c1.number_input("Visitors", min_value=0, value=500, step=10)
            sales = c2.number_input("Sales", min_value=0, value=20, step=1)
            c3.caption("Conversion rate is calculated automatically from sales ÷ visitors.")
            revenue = c1.number_input("Revenue (₹)", min_value=0.0, value=15980.0, step=100.0)
            profit = c2.number_input("Profit (₹)", value=6500.0, step=100.0)

        submitted = st.form_submit_button("Run ACOS", type="primary", use_container_width=True)
        if not submitted:
            return None

        conversion_rate = (int(sales) / int(visitors)) if int(visitors) > 0 else 0.0
        return ScenarioInput(
            product_id=product_id,
            inventory=int(inventory),
            demand=float(demand),
            conversion_rate=conversion_rate,
            advertising_cost=float(advertising_cost),
            visitors=int(visitors),
            sales=int(sales),
            revenue=float(revenue),
            profit=float(profit),
            season=season,
            demand_multiplier=float(demand_multiplier),
            competitor_price_factor=float(competitor_price_factor),
            current_price=float(current_price),
            unit_cost=float(unit_cost),
            marketing_budget=float(marketing_budget),
        )


def main() -> None:
    st.set_page_config(page_title="ACOS Demonstration Platform", page_icon="⚙️", layout="wide")
    initialize_session(st)
    st.title("ACOS Autonomous Commerce Optimization")
    st.caption("Interactive research demonstration: agents → conflict analysis → negotiation when required → MOCRA → coordinated final plan")

    with st.sidebar:
        st.header("System")
        st.success("Core ACOS pipeline connected")
        st.write("This interface calls the existing `ACOSApplicationService`; it does not duplicate agent logic.")
        if st.button("Clear session history", use_container_width=True):
            st.session_state[HISTORY_KEY] = []
            st.session_state[LATEST_KEY] = None
            st.rerun()

    scenario = _scenario_form()
    if scenario is not None:
        try:
            with st.spinner("Agents are analyzing the scenario..."):
                payload = ACOSUIAdapter().run_payload(scenario)
            save_run(st, payload)
            if payload.get("successful"):
                st.toast("ACOS run completed", icon="✅")
            else:
                st.error("ACOS completed with errors. Review the diagnostics below.")
        except Exception as error:
            st.exception(error)

    payload = st.session_state.get(LATEST_KEY)
    if payload:
        st.divider()
        render_summary(st, payload)

        warnings = payload.get("input_warnings", [])
        for warning in warnings:
            st.warning(warning)

        calculated = payload.get("calculated_metrics", {})
        if calculated:
            c1, c2, c3 = st.columns(3)
            c1.metric("Calculated conversion", f"{calculated.get('conversion_rate', 0) * 100:.2f}%")
            c2.metric("Adjusted demand", f"{calculated.get('adjusted_demand', 0):.1f}/100")
            c3.metric("Average selling price", f"₹{calculated.get('average_selling_price', 0):,.2f}")

        overview, agents, resolution, decision, data, history = st.tabs([
            "Overview", "Agent proposals", "Conflict & negotiation", "Final decision", "Raw result", "Session history"
        ])
        with overview:
            st.subheader("Run summary")
            st.json(payload.get("summary", {}), expanded=True)
            if payload.get("errors"):
                st.error("\n".join(payload["errors"]))
        with agents:
            render_proposals(st, payload.get("proposals", []))
        with resolution:
            render_negotiation(st, payload)
        with decision:
            render_decision(st, payload)
        with data:
            st.download_button(
                "Download complete result as JSON",
                data=json.dumps(payload, indent=2, ensure_ascii=False),
                file_name=f"acos_run_{payload.get('run_id', 'result')}.json",
                mime="application/json",
            )
            st.json(payload.get("raw"), expanded=False)
        with history:
            render_history(st, st.session_state[HISTORY_KEY])
    else:
        st.info("Configure a scenario and click **Run ACOS** to see the complete decision pipeline.")


if __name__ == "__main__":
    main()
