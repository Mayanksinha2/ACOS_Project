from __future__ import annotations

from typing import Any

from ..agent_profiles import build_agent_profiles
from ..learning_store import PersistentLearningStore


def render_agent_profiles(
    st: Any,
    payload: dict | None,
    store: PersistentLearningStore | None = None,
) -> None:
    st.subheader("Agent profiles")
    st.caption(
        "Each specialist agent has a separate role, objective, "
        "latest recommendation and observed outcome history."
    )

    profiles = build_agent_profiles(payload or {})
    selected = st.radio(
        "Select an agent",
        options=[profile.agent_id for profile in profiles],
        format_func=lambda value: next(
            (
                f"{profile.icon} {profile.display_name}"
                for profile in profiles
                if profile.agent_id == value
            ),
            value,
        ),
        horizontal=True,
    )
    profile = next(
        item for item in profiles if item.agent_id == selected
    )

    st.markdown(
        f"""
        <div class="acos-profile-hero">
          <div class="acos-profile-icon">{profile.icon}</div>
          <div>
            <h2>{profile.display_name}</h2>
            <div class="acos-muted">{profile.role}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    objective, responsibility = st.columns(2)
    with objective:
        st.markdown("#### Objective")
        st.write(profile.objective)
    with responsibility:
        st.markdown("#### Responsibility")
        st.write(profile.responsibility)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Latest recommendation",
        profile.latest_operation.replace("_", " ").title(),
        profile.latest_value,
    )
    c2.metric("Confidence", f"{profile.confidence:.0f}%")
    c3.metric("Risk", f"{profile.risk:.0f}%")
    c4.metric(
        "MOCRA",
        (
            f"Rank {profile.mocra_rank}"
            if profile.mocra_rank is not None
            else "No ranking"
        ),
        (
            f"Score {profile.mocra_score:.3f}"
            if profile.mocra_score is not None
            else None
        ),
    )

    left, right = st.columns(2)
    with left:
        st.write("**Confidence**")
        st.progress(
            min(max(profile.confidence / 100.0, 0.0), 1.0),
            text=f"{profile.confidence:.0f}%",
        )
    with right:
        st.write("**Risk**")
        st.progress(
            min(max(profile.risk / 100.0, 0.0), 1.0),
            text=f"{profile.risk:.0f}%",
        )

    st.markdown("#### Latest reasoning")
    st.write(profile.latest_rationale)

    if profile.status == "Primary recommendation":
        st.success(profile.status)
    elif profile.status == "Supporting / alternative":
        st.info(profile.status)
    else:
        st.caption(profile.status)

    st.markdown("#### Observed performance history")
    if store is None:
        st.info("Persistent learning store is unavailable.")
        return

    stats = next(
        (
            row
            for row in store.agent_statistics()
            if row["agent"] == profile.agent_id
        ),
        None,
    )

    if not stats:
        st.info(
            "No evaluated real-world outcomes have been recorded for "
            "this agent yet."
        )
        return

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Evaluated outcomes", stats["decision_count"])
    p2.metric("Average reward", f'{stats["average_reward"]:.3f}')
    p3.metric("Success rate", f'{stats["success_rate"] * 100:.1f}%')
    p4.metric(
        "Reliability",
        (
            f'{stats["reliability"] * 100:.1f}% provisional'
            if stats["decision_count"] >= 5
            else "Insufficient evidence"
        ),
    )

    if stats["decision_count"] < 5:
        st.warning(
            "At least five evaluated outcomes are required before "
            "reliability should be interpreted as meaningful."
        )
