from __future__ import annotations
from typing import Any


def render_history(st: Any, history: list[dict]) -> None:
    if not history:
        st.info("Run a scenario to create history in this browser session.")
        return
    rows = []
    for item in history:
        rows.append({
            "run_id": item.get("run_id"),
            "timestamp": item.get("timestamp"),
            "status": item.get("status"),
            "proposals": len(item.get("proposals", [])),
            "conflicts": len(item.get("conflicts", [])),
            "negotiation": item.get("negotiation_required", False),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
