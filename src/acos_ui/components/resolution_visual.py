from __future__ import annotations

from typing import Any

from ..presentation import (
    actual_conflicts,
    build_final_plan,
    negotiation_object,
    proposal_by_agent,
)


def _proposal_text(proposal: dict | None) -> str:
    if not proposal:
        return "No proposal"
    operation = str(proposal.get("operation") or "N/A").replace("_", " ").title()
    value = proposal.get("value", 0)
    unit = proposal.get("unit") or ""
    return f"{operation}<br><strong>{value} {unit}</strong>"


def render_negotiation_flow(st: Any, payload: dict) -> None:
    plan = build_final_plan(payload)
    negotiation = negotiation_object(payload)
    pricing = proposal_by_agent(payload.get("proposals"), "PricingAgent")
    marketing = proposal_by_agent(payload.get("proposals"), "MarketingAgent")
    conflicts = actual_conflicts(payload.get("conflicts"))

    st.markdown('<div class="acos-section-title">Conflict and negotiation</div>', unsafe_allow_html=True)

    left, arrow1, center, arrow2, right = st.columns([3, 1, 3, 1, 3])
    with left:
        st.markdown(
            f"""
            <div class="acos-flow-node">
              <strong>Pricing Agent</strong><br>
              {_proposal_text(pricing)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with arrow1:
        st.markdown('<div class="acos-arrow">→</div>', unsafe_allow_html=True)
    with center:
        st.markdown(
            f"""
            <div class="acos-flow-node">
              <strong>{"Conflict detected" if conflicts else "Proposal coordination"}</strong><br>
              {len(conflicts)} actual conflict(s)<br>
              <span class="acos-muted">Negotiation round {plan.rounds_completed}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with arrow2:
        st.markdown('<div class="acos-arrow">→</div>', unsafe_allow_html=True)
    with right:
        st.markdown(
            f"""
            <div class="acos-flow-node">
              <strong>Negotiated result</strong><br>
              {plan.price_operation.title()}<br>
              <strong>{plan.price_change_percent:.2f}%</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agreement reached", "Yes" if plan.agreement_reached else "No")
    c2.metric("Rounds", plan.rounds_completed)
    c3.metric("Participants", len(plan.participants))
    c4.metric("Actual conflicts", len(conflicts))

    if plan.participants:
        st.caption("Participants: " + ", ".join(plan.participants))

    explanations = negotiation.get("explanation") or []
    if explanations:
        with st.expander("How the negotiated value was calculated", expanded=True):
            for item in explanations:
                st.write("•", item)

    if marketing and marketing.get("action_type") != "PRICE_CHANGE":
        st.info(
            "The Marketing Agent did not provide a price-domain proposal in this run, "
            "so it was not included in price negotiation."
        )
