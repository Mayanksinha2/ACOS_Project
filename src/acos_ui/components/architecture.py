from __future__ import annotations

from typing import Any


STAGES = [
    (
        "1",
        "Business scenario",
        "Product, market, performance and financial inputs.",
        "Input layer",
    ),
    (
        "2",
        "Business State Builder",
        "Normalizes raw inputs into the shared commerce state.",
        "Application layer",
    ),
    (
        "3",
        "Specialist agents",
        "Pricing, Inventory and Marketing independently propose actions.",
        "Multi-agent layer",
    ),
    (
        "4",
        "Conflict Detector",
        "Identifies compatible, supporting, soft-conflict and hard-conflict proposals.",
        "Coordination layer",
    ),
    (
        "5",
        "Adaptive Negotiation",
        "Relevant agents balance competing objectives and reach a compromise.",
        "Negotiation layer",
    ),
    (
        "6",
        "MOCRA",
        "Ranks alternatives using confidence, risk, priority and learned modifiers.",
        "Decision layer",
    ),
    (
        "7",
        "Final coordinated plan",
        "Preserves compatible price, inventory and marketing actions.",
        "Execution layer",
    ),
    (
        "8",
        "Outcome and learning",
        "Evaluates results and feeds experience into future decisions.",
        "Learning layer",
    ),
]


def render_architecture(st: Any, payload: dict | None = None) -> None:
    st.subheader("ACOS system architecture")
    st.caption(
        "This view explains how a business scenario becomes an autonomous, "
        "coordinated commerce decision."
    )

    status_map = {
        "Business scenario": bool(payload),
        "Business State Builder": bool(payload and payload.get("business_state")),
        "Specialist agents": bool(payload and payload.get("proposals")),
        "Conflict Detector": bool(payload and payload.get("conflicts") is not None),
        "Adaptive Negotiation": bool(payload and payload.get("negotiation_result")),
        "MOCRA": bool(payload and payload.get("mocra_result")),
        "Final coordinated plan": bool(payload and payload.get("final_decision")),
        "Outcome and learning": False,
    }

    for index, (number, title, description, layer) in enumerate(STAGES):
        active = status_map.get(title, False)
        status = "Completed in latest run" if active else (
            "Ready for Phase 3B" if title == "Outcome and learning" else "Ready"
        )

        left, body, right = st.columns([1, 6, 2])
        with left:
            st.markdown(
                f"""
                <div class="acos-architecture-number">{number}</div>
                """,
                unsafe_allow_html=True,
            )
        with body:
            st.markdown(f"#### {title}")
            st.write(description)
            st.caption(layer)
        with right:
            if active:
                st.success(status)
            elif title == "Outcome and learning":
                st.info(status)
            else:
                st.caption(status)

        if index < len(STAGES) - 1:
            st.markdown(
                '<div class="acos-architecture-arrow">↓</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Specialist agent collaboration")

    pricing, inventory, marketing = st.columns(3)
    pricing.info(
        "**💰 Pricing Agent**\n\n"
        "Protects margin, pricing position and business utility."
    )
    inventory.info(
        "**📦 Inventory Agent**\n\n"
        "Balances stock availability, overstock and demand pressure."
    )
    marketing.info(
        "**📣 Marketing Agent**\n\n"
        "Improves conversion, campaign performance and customer response."
    )

    st.markdown(
        """
        These agents do not simply vote. Their proposals are checked for domain
        compatibility, conflict, influence and business impact before ACOS selects
        or negotiates the final coordinated plan.
        """
    )
