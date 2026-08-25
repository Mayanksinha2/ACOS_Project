from __future__ import annotations

from typing import Any

from .agent_cards import render_agent_cards


def render_proposals(
    st: Any,
    proposals: list[dict],
    payload: dict | None = None,
) -> None:
    render_agent_cards(
        st,
        proposals,
        payload=payload,
    )
