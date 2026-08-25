from __future__ import annotations

from typing import Any

import pandas as pd

from ..presentation import mocra_ranking


def render_mocra(st: Any, payload: dict) -> None:
    rows = mocra_ranking(payload)
    st.markdown('<div class="acos-section-title">MOCRA decision ranking</div>', unsafe_allow_html=True)

    if not rows:
        st.info("No MOCRA ranking is available.")
        return

    chart = pd.DataFrame(
        {
            "Agent": [row["agent"] for row in rows],
            "MOCRA score": [row["score"] for row in rows],
        }
    ).set_index("Agent")

    st.bar_chart(
        chart,
        horizontal=True,
        height=260,
        use_container_width=True,
    )

    table_rows = []
    for row in rows:
        table_rows.append(
            {
                "Rank": row["rank"],
                "Role": (
                    "Primary recommendation"
                    if row["rank"] == 1
                    else "Supporting / alternative"
                ),
                "Agent": row["agent"],
                "Operation": row["operation"],
                "MOCRA score": round(row["score"], 3),
                "Confidence": f'{row["confidence"]:.0f}%',
                "Risk": f'{row["risk"]:.0f}%',
            }
        )
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    mocra = payload.get("mocra_result") or {}
    explanation = mocra.get("explanation") or []
    if explanation:
        with st.expander("Why the winner ranked first", expanded=True):
            for line in explanation:
                st.write("•", line)
