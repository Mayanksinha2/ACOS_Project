from __future__ import annotations
from typing import Any


def render_proposals(st: Any, proposals: list[dict]) -> None:
    if not proposals:
        st.info("No agent proposals were produced.")
        return

    columns = st.columns(len(proposals))
    for column, proposal in zip(columns, proposals):
        with column:
            st.subheader(proposal.get("agent", "Agent"))
            st.metric("Operation", proposal.get("operation") or "N/A")
            st.progress(max(0.0, min(1.0, proposal.get("confidence", 0.0))), text=f"Confidence {proposal.get('confidence', 0.0):.0%}")
            st.progress(max(0.0, min(1.0, proposal.get("risk", 0.0))), text=f"Risk {proposal.get('risk', 0.0):.0%}")
            action_value = proposal.get("value")
            if action_value is not None:
                st.write("**Value:**", action_value, proposal.get("unit") or "")
            rationale = proposal.get("rationale")
            if rationale:
                st.write("**Rationale:**", rationale)
            evidence = proposal.get("evidence") or []
            if evidence:
                with st.expander("Evidence"):
                    for item in evidence:
                        st.write("•", item)
