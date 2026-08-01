from __future__ import annotations
from typing import Any


def render_negotiation(st: Any, payload: dict) -> None:
    left, middle, right = st.columns(3)
    comparisons = payload.get("conflicts") or []
    actual_conflicts = [
        item for item in comparisons
        if item.get("conflict_type") in {"SOFT_CONFLICT", "HARD_CONFLICT"}
    ]

    with left:
        st.subheader("Conflict detection")
        if actual_conflicts:
            st.json(actual_conflicts, expanded=False)
            st.caption(f"{len(actual_conflicts)} actual conflict(s) detected. Supporting and no-conflict comparisons are hidden here.")
        else:
            st.info("No operational conflicts detected.")

    with middle:
        st.subheader("Negotiation")
        if payload.get("negotiation_required"):
            negotiation = payload.get("negotiation_result")
            if negotiation:
                st.json(negotiation, expanded=False)
            else:
                st.warning("A conflict was detected, but no compatible proposals were available for negotiation.")
        else:
            st.info("Negotiation was not required.")

    with right:
        st.subheader("MOCRA resolution")
        mocra = payload.get("mocra_result")
        if mocra is not None:
            st.json(mocra, expanded=False)
        else:
            st.info("No MOCRA result available.")
