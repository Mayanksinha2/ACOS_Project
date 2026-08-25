from __future__ import annotations
from typing import Any

from .executive import render_business_plan


def render_decision(st: Any, payload: dict) -> None:
    if not payload.get("final_decision"):
        st.warning("No final decision is available.")
        return

    render_business_plan(st, payload)

    with st.expander("Technical final-decision object", expanded=False):
        st.json(payload.get("final_decision"), expanded=False)
