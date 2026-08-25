from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .presentation import mocra_ranking, percent


@dataclass(frozen=True, slots=True)
class AgentProfile:
    agent_id: str
    display_name: str
    icon: str
    role: str
    objective: str
    responsibility: str
    latest_operation: str
    latest_value: str
    confidence: float
    risk: float
    mocra_rank: int | None
    mocra_score: float | None
    latest_rationale: str
    status: str


STATIC_AGENT_PROFILES = {
    "PricingAgent": {
        "display_name": "Pricing Agent",
        "icon": "💰",
        "role": "Commercial pricing specialist",
        "objective": "Maximize business utility while protecting price competitiveness.",
        "responsibility": (
            "Evaluates current price, demand, competitors, profitability, "
            "and commercial conditions before proposing a price action."
        ),
    },
    "InventoryAgent": {
        "display_name": "Inventory Agent",
        "icon": "📦",
        "role": "Inventory health specialist",
        "objective": "Keep stock aligned with demand while avoiding shortages and overstock.",
        "responsibility": (
            "Evaluates inventory levels and demand pressure before proposing "
            "stock maintenance, replenishment, or clearance."
        ),
    },
    "MarketingAgent": {
        "display_name": "Marketing Agent",
        "icon": "📣",
        "role": "Conversion and promotion specialist",
        "objective": "Increase customer conversion and promotional effectiveness.",
        "responsibility": (
            "Evaluates conversion, traffic, campaign conditions, and advertising "
            "cost before proposing promotional or price-support actions."
        ),
    },
}


def build_agent_profiles(payload: dict[str, Any]) -> list[AgentProfile]:
    proposals = {
        str(item.get("agent")): item
        for item in payload.get("proposals") or []
    }
    rankings = {
        row["agent"]: row
        for row in mocra_ranking(payload)
    }

    profiles: list[AgentProfile] = []

    for agent_id, static in STATIC_AGENT_PROFILES.items():
        proposal = proposals.get(agent_id, {})
        ranking = rankings.get(agent_id)

        operation = str(proposal.get("operation") or "No decision")
        value = proposal.get("value", 0)
        unit = proposal.get("unit") or ""
        value_text = (
            f"{value:g} {unit}"
            if isinstance(value, (int, float))
            else f"{value} {unit}"
        ).strip()

        profiles.append(
            AgentProfile(
                agent_id=agent_id,
                display_name=static["display_name"],
                icon=static["icon"],
                role=static["role"],
                objective=static["objective"],
                responsibility=static["responsibility"],
                latest_operation=operation,
                latest_value=value_text or "N/A",
                confidence=percent(proposal.get("confidence")),
                risk=percent(proposal.get("risk")),
                mocra_rank=ranking["rank"] if ranking else None,
                mocra_score=ranking["score"] if ranking else None,
                latest_rationale=str(
                    proposal.get("rationale")
                    or "Run a scenario to view the latest reasoning."
                ),
                status=(
                    "Primary recommendation"
                    if ranking and ranking["rank"] == 1
                    else (
                        "Supporting / alternative"
                        if ranking
                        else "Waiting for run"
                    )
                ),
            )
        )

    return profiles
