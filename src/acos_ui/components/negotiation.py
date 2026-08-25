from __future__ import annotations
from typing import Any

from .mocra_visual import render_mocra
from .resolution_visual import render_negotiation_flow


def render_negotiation(st: Any, payload: dict) -> None:
    render_negotiation_flow(st, payload)
    st.divider()
    render_mocra(st, payload)
