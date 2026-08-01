from __future__ import annotations
from typing import Any


def render_decision(st: Any, payload: dict) -> None:
    final_decision = payload.get("final_decision")
    if final_decision is None:
        st.warning("No final decision is available.")
        return

    st.success("ACOS produced a coordinated final plan.")
    decision_type = final_decision.get("decision_type", "UNKNOWN")
    st.metric("Resolution method", decision_type)

    actions = final_decision.get("coordinated_actions") or []
    if actions:
        st.subheader("Coordinated actions")
        columns = st.columns(min(3, len(actions)))
        for index, item in enumerate(actions):
            action = item.get("business_action") or {}
            with columns[index % len(columns)]:
                st.markdown(f"**{item.get('agent_id', 'Agent')}**")
                st.write(f"Operation: `{action.get('operation', '')}`")
                st.write(f"Domain: `{action.get('action_type', '')}`")
                value = action.get("value", 0)
                unit = action.get("unit", "")
                st.write(f"Value: **{value} {unit}**")
                rationale = action.get("rationale")
                if rationale:
                    st.caption(rationale)

    with st.expander("Technical final-decision object", expanded=False):
        st.json(final_decision, expanded=True)
