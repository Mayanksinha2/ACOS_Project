from __future__ import annotations

from typing import Any

from ..presentation import percent
from ..xai_explanations import DynamicExplanationEngine


AGENT_LABELS = {
    "PricingAgent": "💰 Pricing Agent",
    "InventoryAgent": "📦 Inventory Agent",
    "MarketingAgent": "📣 Marketing Agent",
}


def _safe_fraction(value: Any) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    if number > 1.0:
        number = number / 100.0
    return max(0.0, min(1.0, number))


def _display_operation(value: Any) -> str:
    return str(value or "N/A").replace("_", " ").title()


def render_agent_cards(
    st: Any,
    proposals: list[dict],
    payload: dict | None = None,
) -> None:
    if not proposals:
        st.info("No agent proposals were produced.")
        return

    explanations = (
        DynamicExplanationEngine().explain_all(payload or {})
        if payload
        else {}
    )

    st.markdown(
        '<div class="acos-section-title">Agent recommendations</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(min(3, len(proposals)))

    for index, proposal in enumerate(proposals):
        agent = str(proposal.get("agent", "Agent"))
        operation = _display_operation(proposal.get("operation"))
        action_type = _display_operation(proposal.get("action_type"))
        value = proposal.get("value", 0)
        unit = str(proposal.get("unit", "") or "")
        confidence = _safe_fraction(proposal.get("confidence"))
        risk = _safe_fraction(proposal.get("risk"))
        explanation = explanations.get(agent)

        with columns[index % len(columns)]:
            with st.container(border=True):
                st.subheader(AGENT_LABELS.get(agent, agent))
                st.markdown(f"### {operation}")

                left, right = st.columns(2)
                with left:
                    st.caption("Action type")
                    st.write(action_type)
                with right:
                    st.caption("Recommended value")
                    st.write(f"{value} {unit}".strip())

                st.divider()
                st.write("**Confidence**")
                st.progress(
                    confidence,
                    text=f"{percent(confidence):.0f}%",
                )
                st.write("**Risk**")
                st.progress(
                    risk,
                    text=f"{percent(risk):.0f}%",
                )

                st.divider()

                if explanation:
                    st.write("**Conclusion**")
                    st.write(explanation.conclusion)

                    with st.expander("Observed business facts", expanded=True):
                        for item in explanation.observations:
                            st.write("•", item)

                    with st.expander("Reasoning chain", expanded=True):
                        for item in explanation.reasoning:
                            st.write("•", item)

                    with st.expander("Metric-backed evidence", expanded=True):
                        for item in explanation.evidence:
                            st.write("•", item)
                else:
                    st.write("**Why this agent recommended it**")
                    st.write(
                        proposal.get("rationale")
                        or "No rationale was supplied."
                    )
