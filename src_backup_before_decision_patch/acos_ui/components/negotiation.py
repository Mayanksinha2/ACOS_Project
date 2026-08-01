from __future__ import annotations
from typing import Any


def render_negotiation(st: Any, payload: dict) -> None:
    left, middle, right = st.columns(3)
    with left:
        st.subheader("Conflict detection")
        conflicts = payload.get("conflicts") or []
        if conflicts:
            st.json(conflicts, expanded=False)
        else:
            st.info("No conflicts detected.")
    with middle:
        st.subheader("Negotiation")
        if payload.get("negotiation_required"):
            st.json(payload.get("negotiation_result"), expanded=False)
        else:
            st.info("Negotiation was not required.")
    with right:
        st.subheader("MOCRA resolution")
        mocra = payload.get("mocra_result")
        if mocra is not None:
            st.json(mocra, expanded=False)
        else:
            st.info("No MOCRA result available.")
