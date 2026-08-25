from __future__ import annotations

from typing import Any

from ..agent_profiles import build_agent_profiles


def render_landing(st: Any, payload: dict | None, history: list[dict]) -> None:
    st.markdown(
        """
        <div class="acos-landing-hero">
          <div class="acos-eyebrow">AUTONOMOUS COMMERCE OPERATING SYSTEM</div>
          <h1>Observe. Negotiate. Decide. Explain.</h1>
          <p>
            ACOS coordinates specialist commerce agents to produce transparent,
            multi-objective business decisions.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profiles = build_agent_profiles(payload or {})
    winner = next(
        (
            profile.display_name
            for profile in profiles
            if profile.status == "Primary recommendation"
        ),
        "No run yet",
    )

    conflicts = 0
    if payload:
        for item in payload.get("conflicts") or []:
            if str(item.get("conflict_type") or "").upper() in {
                "SOFT_CONFLICT",
                "HARD_CONFLICT",
            }:
                conflicts += 1

    metrics = st.columns(5)
    metrics[0].metric("Runs this session", len(history))
    metrics[1].metric(
        "Decision engine",
        "Online",
    )
    metrics[2].metric(
        "Latest status",
        payload.get("status", "Waiting") if payload else "Waiting",
    )
    metrics[3].metric("Latest conflicts", conflicts)
    metrics[4].metric("Latest winner", winner)

    st.subheader("System status")
    status_columns = st.columns(5)
    for column, label in zip(
        status_columns,
        [
            "✓ Agents online",
            "✓ Conflict detection online",
            "✓ Negotiation online",
            "✓ MOCRA online",
            "◌ Learning integration next",
        ],
    ):
        column.info(label)

    st.subheader("What you can do")
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        "**Run scenario**\n\n"
        "Choose a preset or enter your own commerce situation."
    )
    c2.markdown(
        "**Understand the decision**\n\n"
        "Review agents, conflict, negotiation and MOCRA ranking."
    )
    c3.markdown(
        "**Explore the architecture**\n\n"
        "See how every ACOS module contributes to the final plan."
    )
