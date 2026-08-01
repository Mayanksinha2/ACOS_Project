from __future__ import annotations
from typing import Any

HISTORY_KEY = "acos_run_history"
LATEST_KEY = "acos_latest_payload"


def initialize_session(st: Any) -> None:
    st.session_state.setdefault(HISTORY_KEY, [])
    st.session_state.setdefault(LATEST_KEY, None)


def save_run(st: Any, payload: dict) -> None:
    st.session_state[LATEST_KEY] = payload
    history = st.session_state[HISTORY_KEY]
    history.insert(0, payload)
    del history[25:]
