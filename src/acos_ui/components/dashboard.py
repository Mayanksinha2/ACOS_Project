from __future__ import annotations
from typing import Any

from .executive import render_executive_header


def render_summary(st: Any, payload: dict) -> None:
    render_executive_header(st, payload)
