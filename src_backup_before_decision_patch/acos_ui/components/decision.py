from __future__ import annotations
from typing import Any


def render_decision(st: Any, payload: dict) -> None:
    final_decision = payload.get("final_decision")
    if final_decision is None:
        st.warning("No final decision is available.")
        return
    st.success("ACOS produced a final decision.")
    st.json(final_decision, expanded=True)
