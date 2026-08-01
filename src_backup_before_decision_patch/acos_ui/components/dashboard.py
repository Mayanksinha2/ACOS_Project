from __future__ import annotations
from typing import Any


def render_summary(st: Any, payload: dict) -> None:
    columns = st.columns(5)
    columns[0].metric("Status", payload.get("status", "UNKNOWN"))
    columns[1].metric("Agent proposals", len(payload.get("proposals", [])))
    columns[2].metric("Conflicts", len(payload.get("conflicts", [])))
    columns[3].metric("Negotiation", "Required" if payload.get("negotiation_required") else "Not required")
    columns[4].metric("Successful", "Yes" if payload.get("successful") else "No")
    st.caption(f"Run ID: {payload.get('run_id', '-')}")
