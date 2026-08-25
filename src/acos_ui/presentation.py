from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class FinalPlan:
    product_id: str
    resolution_method: str
    price_operation: str
    price_change_percent: float
    current_price: float | None
    recommended_price: float | None
    rounded_price: float | None
    inventory_operation: str
    inventory_value: float
    inventory_unit: str
    marketing_operation: str
    marketing_value: float
    marketing_unit: str
    agreement_reached: bool
    rounds_completed: int
    participants: tuple[str, ...]
    winning_agent: str
    winning_score: float | None
    business_summary: str
    positive_impact: tuple[str, ...]
    trade_offs: tuple[str, ...]


def as_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def percent(value: Any) -> float:
    number = as_number(value)
    return number * 100.0 if abs(number) <= 1.0 else number


def money(value: Any) -> str:
    return f"₹{as_number(value):,.2f}"


def practical_price(value: float | None) -> float | None:
    if value is None:
        return None
    # Business-friendly price ending. The recommendation remains approximate,
    # while the exact negotiated value is still available in technical details.
    if value <= 0:
        return 0.0
    rounded = round(value / 10.0) * 10.0
    return max(0.0, rounded)


def actual_conflicts(conflicts: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in conflicts or []:
        conflict_type = str(
            item.get("conflict_type")
            or item.get("type")
            or ""
        ).upper()
        if conflict_type in {"SOFT_CONFLICT", "HARD_CONFLICT"}:
            result.append(item)
    return result


def proposal_by_agent(
    proposals: Iterable[dict[str, Any]] | None,
    agent_name: str,
) -> dict[str, Any] | None:
    target = agent_name.lower()
    for proposal in proposals or []:
        name = str(
            proposal.get("agent")
            or proposal.get("agent_id")
            or ""
        ).lower()
        if name == target:
            return proposal
    return None


def action_from_coordinated_item(item: dict[str, Any]) -> dict[str, Any]:
    action = item.get("business_action")
    return action if isinstance(action, dict) else {}


def coordinated_action(
    final_decision: dict[str, Any] | None,
    *,
    agent_name: str | None = None,
    action_type: str | None = None,
) -> dict[str, Any] | None:
    for item in (final_decision or {}).get("coordinated_actions") or []:
        if agent_name and str(item.get("agent_id", "")).lower() != agent_name.lower():
            continue
        action = action_from_coordinated_item(item)
        if action_type and str(action.get("action_type", "")).upper() != action_type.upper():
            continue
        return {"proposal": item, "action": action}
    return None


def negotiation_object(payload: dict[str, Any]) -> dict[str, Any]:
    final_decision = payload.get("final_decision") or {}
    result = final_decision.get("result")
    if isinstance(result, dict) and result.get("negotiation_id"):
        return result
    negotiation = payload.get("negotiation_result")
    return negotiation if isinstance(negotiation, dict) else {}


def mocra_ranking(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mocra = payload.get("mocra_result") or {}
    ranking = mocra.get("ranking") or []
    rows: list[dict[str, Any]] = []

    for index, item in enumerate(ranking, start=1):
        decision = item.get("decision") or {}
        action = decision.get("business_action") or {}
        details = item.get("score_details") or {}
        score = details.get("final_score")
        if score is None:
            score = item.get("score")

        rows.append(
            {
                "rank": index,
                "agent": decision.get("agent_id", "Unknown Agent"),
                "operation": action.get("operation", "N/A"),
                "action_type": action.get("action_type", "N/A"),
                "score": as_number(score),
                "confidence": percent(decision.get("confidence")),
                "risk": percent(decision.get("risk")),
                "priority": action.get("priority", ""),
            }
        )
    return rows


def _price_action(payload: dict[str, Any]) -> tuple[str, float]:
    negotiation = negotiation_object(payload)
    operation = str(negotiation.get("final_operation") or "").upper()
    value = abs(as_number(negotiation.get("final_value")))

    if operation:
        return operation, value

    final_decision = payload.get("final_decision") or {}
    price = coordinated_action(final_decision, action_type="PRICE_CHANGE")
    if price:
        action = price["action"]
        return str(action.get("operation", "MAINTAIN")).upper(), abs(
            as_number(action.get("value"))
        )

    return "MAINTAIN", 0.0


def _recommended_price(
    current_price: float | None,
    operation: str,
    change_percent: float,
) -> float | None:
    if current_price is None:
        return None

    factor = change_percent / 100.0
    if operation == "DECREASE":
        return max(0.0, current_price * (1.0 - factor))
    if operation == "INCREASE":
        return current_price * (1.0 + factor)
    return current_price


def _scenario_current_price(payload: dict[str, Any]) -> float | None:
    scenario = payload.get("scenario") or {}
    if "current_price" in scenario:
        return as_number(scenario.get("current_price"))

    calculated = payload.get("calculated_metrics") or {}
    if "current_price" in calculated:
        return as_number(calculated.get("current_price"))

    business_state = payload.get("business_state") or {}
    metrics = business_state.get("metrics") or business_state.get("additional_metrics") or {}
    for key in ("current_price", "price"):
        if key in metrics:
            return as_number(metrics[key])
    return None


def _domain_action(
    payload: dict[str, Any],
    *,
    agent_name: str,
    default_operation: str,
    default_unit: str,
) -> tuple[str, float, str]:
    final_decision = payload.get("final_decision") or {}
    result = coordinated_action(final_decision, agent_name=agent_name)

    if result:
        action = result["action"]
        return (
            str(action.get("operation") or default_operation),
            as_number(action.get("value")),
            str(action.get("unit") or default_unit),
        )

    proposal = proposal_by_agent(payload.get("proposals"), agent_name)
    if proposal:
        return (
            str(proposal.get("operation") or default_operation),
            as_number(proposal.get("value")),
            str(proposal.get("unit") or default_unit),
        )

    return default_operation, 0.0, default_unit


def _impact_text(
    operation: str,
    price_change: float,
    marketing_operation: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    positive: list[str] = []
    trade_offs: list[str] = []

    if operation == "DECREASE":
        positive.extend(
            [
                "Lower price may improve customer conversion.",
                "The discount may increase product traffic and sales volume.",
            ]
        )
        trade_offs.append("Unit margin may decrease unless sales volume rises.")
    elif operation == "INCREASE":
        positive.append("Higher selling price may improve unit margin.")
        trade_offs.append("Conversion may decline if customers are price-sensitive.")
    else:
        positive.append("Current price stability protects the existing market position.")

    if "INCREASE" in marketing_operation.upper():
        positive.append("Higher promotional visibility may support traffic growth.")
        trade_offs.append("Marketing spend will increase.")
    elif "DECREASE" in marketing_operation.upper():
        trade_offs.append("Reduced promotion may lower traffic.")

    if price_change == 0 and not positive:
        positive.append("No immediate commercial adjustment is required.")

    return tuple(positive), tuple(trade_offs)


def build_final_plan(payload: dict[str, Any]) -> FinalPlan:
    final_decision = payload.get("final_decision") or {}
    negotiation = negotiation_object(payload)
    mocra = payload.get("mocra_result") or {}
    winning = mocra.get("winning_decision") or {}

    operation, change = _price_action(payload)
    current_price = _scenario_current_price(payload)
    exact_price = _recommended_price(current_price, operation, change)

    inventory_operation, inventory_value, inventory_unit = _domain_action(
        payload,
        agent_name="InventoryAgent",
        default_operation="MAINTAIN_STOCK",
        default_unit="UNITS",
    )
    marketing_operation, marketing_value, marketing_unit = _domain_action(
        payload,
        agent_name="MarketingAgent",
        default_operation="NO_CHANGE",
        default_unit="PERCENT",
    )

    winning_agent = str(winning.get("agent_id") or "")
    if not winning_agent:
        ranking = mocra_ranking(payload)
        winning_agent = ranking[0]["agent"] if ranking else "N/A"

    winning_score = mocra.get("winning_score")
    if winning_score is None:
        ranking = mocra_ranking(payload)
        winning_score = ranking[0]["score"] if ranking else None

    product_id = str(
        negotiation.get("target")
        or (payload.get("scenario") or {}).get("product_id")
        or payload.get("run_id")
        or "Product"
    )

    if operation == "DECREASE":
        summary = (
            f"Reduce the price by {change:.2f}%"
            + (
                f", from {money(current_price)} to approximately "
                f"{money(practical_price(exact_price))}."
                if current_price is not None and exact_price is not None
                else "."
            )
        )
    elif operation == "INCREASE":
        summary = (
            f"Increase the price by {change:.2f}%"
            + (
                f", from {money(current_price)} to approximately "
                f"{money(practical_price(exact_price))}."
                if current_price is not None and exact_price is not None
                else "."
            )
        )
    else:
        summary = (
            f"Maintain the current price"
            + (f" at {money(current_price)}." if current_price is not None else ".")
        )

    positive, trade_offs = _impact_text(
        operation,
        change,
        marketing_operation,
    )

    return FinalPlan(
        product_id=product_id,
        resolution_method=str(final_decision.get("decision_type") or "UNKNOWN"),
        price_operation=operation,
        price_change_percent=change,
        current_price=current_price,
        recommended_price=exact_price,
        rounded_price=practical_price(exact_price),
        inventory_operation=inventory_operation,
        inventory_value=inventory_value,
        inventory_unit=inventory_unit,
        marketing_operation=marketing_operation,
        marketing_value=marketing_value,
        marketing_unit=marketing_unit,
        agreement_reached=bool(negotiation.get("agreement_reached", False)),
        rounds_completed=int(as_number(negotiation.get("rounds_completed"))),
        participants=tuple(negotiation.get("participant_agents") or ()),
        winning_agent=winning_agent or "N/A",
        winning_score=(
            as_number(winning_score) if winning_score is not None else None
        ),
        business_summary=summary,
        positive_impact=positive,
        trade_offs=trade_offs,
    )
