from __future__ import annotations

import json

import streamlit as st

from .application_adapter import ACOSUIAdapter, ScenarioInput
from .components.agent_profiles_view import render_agent_profiles
from .components.architecture import render_architecture
from .components.dashboard import render_summary
from .components.decision import render_decision
from .components.experience_detail import render_experience_detail
from .components.history import render_history
from .components.landing import render_landing
from .components.learning_dashboard import render_learning_dashboard
from .components.negotiation import render_negotiation
from .components.outcome_feedback import render_outcome_feedback
from .components.proposals import render_proposals
from .components.scenario_summary import render_scenario_summary
from .components.styles import apply_styles
from .learning_store import PersistentLearningStore
from .presets import PRESET_DESCRIPTIONS, get_preset, preset_names
from .session_state import (
    HISTORY_KEY,
    LATEST_KEY,
    initialize_session,
    save_run,
)


PAGE_KEY = "acos_navigation"
NEXT_PAGE_KEY = "acos_next_navigation"
PRESET_KEY = "acos_selected_preset"


def _initialize_navigation() -> None:
    if PAGE_KEY not in st.session_state:
        st.session_state[PAGE_KEY] = "Overview"
    if NEXT_PAGE_KEY not in st.session_state:
        st.session_state[NEXT_PAGE_KEY] = None
    if PRESET_KEY not in st.session_state:
        st.session_state[PRESET_KEY] = "Custom scenario"


def _apply_pending_navigation() -> None:
    next_page = st.session_state.get(NEXT_PAGE_KEY)
    if next_page:
        st.session_state[PAGE_KEY] = next_page
        st.session_state[NEXT_PAGE_KEY] = None


def _scenario_form() -> ScenarioInput | None:
    selected_preset = st.selectbox(
        "Scenario preset",
        options=preset_names(),
        key=PRESET_KEY,
        help=(
            "Load a prepared business condition, then edit any "
            "value before running ACOS."
        ),
    )
    preset = get_preset(selected_preset)
    st.caption(PRESET_DESCRIPTIONS[selected_preset])

    with st.form("acos_scenario_form"):
        st.subheader("Build a commerce scenario")
        st.caption(
            "Preset values are editable. Conversion is calculated "
            "automatically from visitors and sales."
        )

        basic, market, performance = st.tabs(
            ["Product", "Market", "Performance"]
        )

        with basic:
            c1, c2, c3 = st.columns(3)
            product_id = c1.text_input(
                "Product ID",
                preset.product_id,
            )
            current_price = c2.number_input(
                "Current price (₹)",
                min_value=0.0,
                value=float(preset.current_price),
                step=10.0,
            )
            unit_cost = c3.number_input(
                "Unit cost (₹)",
                min_value=0.0,
                value=float(preset.unit_cost),
                step=10.0,
            )
            inventory = c1.number_input(
                "Inventory",
                min_value=0,
                value=int(preset.inventory),
                step=1,
            )
            marketing_budget = c2.number_input(
                "Marketing budget (₹)",
                min_value=0.0,
                value=float(preset.marketing_budget),
                step=500.0,
            )

        with market:
            c1, c2, c3 = st.columns(3)
            demand = c1.slider(
                "Base demand score",
                0.0,
                100.0,
                float(preset.demand),
                1.0,
            )
            seasons = [
                "NORMAL",
                "FESTIVAL",
                "SALE",
                "OFF_SEASON",
            ]
            season = c2.selectbox(
                "Season",
                seasons,
                index=(
                    seasons.index(preset.season)
                    if preset.season in seasons
                    else 0
                ),
            )
            demand_multiplier = c3.number_input(
                "Demand multiplier",
                min_value=0.1,
                value=float(preset.demand_multiplier),
                step=0.1,
            )
            competitor_price_factor = c1.number_input(
                "Competitor price factor",
                min_value=0.1,
                value=float(
                    preset.competitor_price_factor
                ),
                step=0.05,
            )
            advertising_cost = c2.number_input(
                "Advertising cost (₹)",
                min_value=0.0,
                value=float(preset.advertising_cost),
                step=100.0,
            )
            c3.info(
                "Adjusted demand = base demand × demand multiplier, "
                "capped at 100."
            )

        with performance:
            c1, c2, c3 = st.columns(3)
            visitors = c1.number_input(
                "Visitors",
                min_value=0,
                value=int(preset.visitors),
                step=10,
            )
            sales = c2.number_input(
                "Sales",
                min_value=0,
                value=int(preset.sales),
                step=1,
            )
            conversion_preview = (
                float(sales) / float(visitors) * 100.0
                if visitors
                else 0.0
            )
            c3.metric(
                "Calculated conversion",
                f"{conversion_preview:.2f}%",
            )
            revenue = c1.number_input(
                "Revenue (₹)",
                min_value=0.0,
                value=float(preset.revenue),
                step=100.0,
            )
            profit = c2.number_input(
                "Profit (₹)",
                value=float(preset.profit),
                step=100.0,
            )

        submitted = st.form_submit_button(
            "Run ACOS",
            type="primary",
            use_container_width=True,
        )
        if not submitted:
            return None

        conversion_rate = (
            int(sales) / int(visitors)
            if int(visitors) > 0
            else 0.0
        )

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
            demand_multiplier=float(
                demand_multiplier
            ),
            competitor_price_factor=float(
                competitor_price_factor
            ),
            current_price=float(current_price),
            unit_cost=float(unit_cost),
            marketing_budget=float(marketing_budget),
        )


def _sidebar_navigation(
    store: PersistentLearningStore,
) -> None:
    with st.sidebar:
        st.header("ACOS")
        st.success("Core decision engine online")

        st.radio(
            "Navigate",
            options=[
                "Overview",
                "Run scenario",
                "Latest decision",
                "Evaluate outcome",
                "Learning dashboard",
                "Experience explorer",
                "Architecture",
                "Agent profiles",
                "Research details",
                "Run history",
            ],
            key=PAGE_KEY,
        )

        st.divider()
        summary = store.summary()
        st.metric(
            "Persistent experiences",
            summary["total"],
        )
        st.metric(
            "Average learned reward",
            f'{summary["average_reward"]:.3f}',
        )
        st.caption(
            "Phase 3B stores real outcomes in a persistent SQLite "
            "learning database."
        )

        if st.button(
            "Clear session history",
            use_container_width=True,
        ):
            st.session_state[HISTORY_KEY] = []
            st.session_state[LATEST_KEY] = None
            st.rerun()


def _run_scenario_page() -> None:
    st.title("Run an ACOS scenario")
    scenario = _scenario_form()

    if scenario is not None:
        try:
            with st.spinner(
                "Agents are analysing, negotiating and "
                "ranking proposals..."
            ):
                payload = ACOSUIAdapter().run_payload(
                    scenario
                )
            save_run(st, payload)

            if payload.get("successful"):
                st.toast(
                    "ACOS decision completed",
                    icon="✅",
                )
                st.session_state[
                    NEXT_PAGE_KEY
                ] = "Latest decision"
                st.rerun()
            else:
                st.error(
                    "ACOS completed with errors. "
                    "Review diagnostics."
                )
        except Exception as error:
            st.exception(error)


def _latest_decision_page(
    payload: dict | None,
) -> None:
    st.title("Latest autonomous decision")

    if not payload:
        st.info(
            "No completed decision is available. "
            "Open **Run scenario** and execute ACOS."
        )
        return

    render_summary(st, payload)

    decision_tab, agents_tab, resolution_tab, scenario_tab = st.tabs(
        [
            "Executive decision",
            "Agent recommendations",
            "Negotiation & MOCRA",
            "Scenario health",
        ]
    )

    with decision_tab:
        render_decision(st, payload)
    with agents_tab:
        render_proposals(
            st,
            payload.get("proposals") or [],
            payload=payload,
        )
    with resolution_tab:
        render_negotiation(st, payload)
    with scenario_tab:
        render_scenario_summary(st, payload)

    if st.button(
        "Record the real outcome of this decision",
        type="primary",
        use_container_width=True,
    ):
        st.session_state[
            NEXT_PAGE_KEY
        ] = "Evaluate outcome"
        st.rerun()


def _research_page(
    payload: dict | None,
) -> None:
    st.title("Research details")
    st.caption(
        "This page exposes the complete technical result "
        "for researchers and developers."
    )

    if not payload:
        st.info(
            "Run a scenario before viewing research details."
        )
        return

    st.download_button(
        "Download complete result as JSON",
        data=json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        file_name=(
            f"acos_run_{payload.get('run_id', 'result')}.json"
        ),
        mime="application/json",
    )

    with st.expander(
        "Run summary JSON",
        expanded=True,
    ):
        st.json(
            payload.get("summary") or {},
            expanded=False,
        )
    with st.expander("Complete raw result"):
        st.json(
            payload.get("raw"),
            expanded=False,
        )

    if payload.get("errors"):
        st.error("\n".join(payload["errors"]))


def main() -> None:
    st.set_page_config(
        page_title="ACOS Autonomous Commerce",
        page_icon="⚙️",
        layout="wide",
    )
    apply_styles(st)
    initialize_session(st)
    _initialize_navigation()
    _apply_pending_navigation()

    try:
        store = PersistentLearningStore()
    except Exception as error:
        st.error(
            "Persistent learning storage could not be initialized."
        )
        st.exception(error)
        return

    _sidebar_navigation(store)

    payload = st.session_state.get(LATEST_KEY)
    history = st.session_state[HISTORY_KEY]
    page = st.session_state[PAGE_KEY]

    if page == "Overview":
        render_landing(st, payload, history)
    elif page == "Run scenario":
        _run_scenario_page()
    elif page == "Latest decision":
        _latest_decision_page(payload)
    elif page == "Evaluate outcome":
        render_outcome_feedback(
            st,
            payload,
            store,
        )
    elif page == "Learning dashboard":
        render_learning_dashboard(
            st,
            store,
        )
    elif page == "Experience explorer":
        render_experience_detail(
            st,
            store,
        )
    elif page == "Architecture":
        render_architecture(st, payload)
    elif page == "Agent profiles":
        st.title("ACOS specialist agents")
        render_agent_profiles(st, payload, store=store)
    elif page == "Research details":
        _research_page(payload)
    elif page == "Run history":
        st.title("Session run history")
        render_history(st, history)


if __name__ == "__main__":
    main()
