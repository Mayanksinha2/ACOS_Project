from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _pct(value: Any) -> float:
    number = _num(value)
    return number * 100.0 if abs(number) <= 1.0 else number


def _money(value: Any) -> str:
    return f"₹{_num(value):,.2f}"


@dataclass(frozen=True, slots=True)
class AgentExplanation:
    agent: str
    observations: tuple[str, ...]
    reasoning: tuple[str, ...]
    evidence: tuple[str, ...]
    conclusion: str


class DynamicExplanationEngine:
    """
    UI-level explainability layer grounded in the actual scenario values.

    It does not alter the agent decision. It interprets the completed ACOS
    payload and produces metric-backed observations, reasoning, and evidence.
    """

    def explain_all(
        self,
        payload: dict[str, Any],
    ) -> dict[str, AgentExplanation]:
        return {
            "PricingAgent": self._pricing(payload),
            "InventoryAgent": self._inventory(payload),
            "MarketingAgent": self._marketing(payload),
        }

    def _scenario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload.get("scenario") or {}

    def _calculated(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload.get("calculated_metrics") or {}

    def _proposal(
        self,
        payload: dict[str, Any],
        agent: str,
    ) -> dict[str, Any]:
        for item in payload.get("proposals") or []:
            if str(item.get("agent")) == agent:
                return item
        return {}

    def _pricing(self, payload: dict[str, Any]) -> AgentExplanation:
        s = self._scenario(payload)
        c = self._calculated(payload)
        p = self._proposal(payload, "PricingAgent")

        price = _num(s.get("current_price"))
        factor = _num(s.get("competitor_price_factor"), 1.0)
        competitor_price = price * factor
        demand = _num(c.get("adjusted_demand", s.get("demand")))
        conversion = _pct(
            c.get("conversion_rate", s.get("conversion_rate"))
        )
        profit = _num(s.get("profit"))
        revenue = _num(s.get("revenue"))
        margin_rate = (
            profit / revenue * 100.0
            if revenue > 0
            else 0.0
        )
        operation = str(p.get("operation") or "MAINTAIN")
        value = abs(_num(p.get("value")))

        observations = (
            f"Current selling price is {_money(price)}.",
            f"Estimated competitor price is {_money(competitor_price)} "
            f"(factor {factor:.2f}).",
            f"Adjusted demand is {demand:.1f}/100.",
            f"Current conversion rate is {conversion:.2f}%.",
            f"Observed profit margin is approximately {margin_rate:.1f}%.",
        )

        reasoning = []
        if factor < 0.95:
            reasoning.append(
                "Competitors appear materially cheaper, creating price pressure."
            )
        elif factor > 1.05:
            reasoning.append(
                "Competitors appear more expensive, so ACOS has some pricing headroom."
            )
        else:
            reasoning.append(
                "Competitor pricing is close to the current price, so market pressure is limited."
            )

        if conversion < 4.0:
            reasoning.append(
                "Conversion is weak, so any price increase could further reduce purchases."
            )
        elif conversion > 7.0:
            reasoning.append(
                "Conversion is strong, which may support maintaining or cautiously increasing price."
            )
        else:
            reasoning.append(
                "Conversion is moderate and does not justify an aggressive price move."
            )

        if margin_rate < 10.0:
            reasoning.append(
                "Profit margin is already thin, so a discount should be applied cautiously."
            )
        else:
            reasoning.append(
                "Current margin provides some room for controlled price adjustment."
            )

        evidence = [
            f"Price gap versus estimated competitor level: "
            f"{_money(competitor_price - price)}.",
            f"Adjusted demand score used by ACOS: {demand:.1f}/100.",
            f"Conversion observed from the scenario: {conversion:.2f}%.",
            f"Profit-to-revenue ratio: {margin_rate:.1f}%.",
        ]

        if operation == "DECREASE":
            conclusion = (
                f"Pricing Agent recommends decreasing price by {value:.2f}% "
                "to improve competitiveness and conversion."
            )
        elif operation == "INCREASE":
            conclusion = (
                f"Pricing Agent recommends increasing price by {value:.2f}% "
                "to improve unit margin while market conditions remain supportive."
            )
        else:
            conclusion = (
                "Pricing Agent recommends maintaining the current price because "
                "the available signals do not justify a direct price change."
            )

        return AgentExplanation(
            agent="PricingAgent",
            observations=observations,
            reasoning=tuple(reasoning),
            evidence=tuple(evidence),
            conclusion=conclusion,
        )

    def _inventory(self, payload: dict[str, Any]) -> AgentExplanation:
        s = self._scenario(payload)
        c = self._calculated(payload)
        p = self._proposal(payload, "InventoryAgent")

        inventory = _num(s.get("inventory"))
        demand = _num(c.get("adjusted_demand", s.get("demand")))
        sales = _num(s.get("sales"))
        operation = str(p.get("operation") or "MAINTAIN_STOCK")
        value = _num(p.get("value"))

        demand_units = max(1.0, demand)
        coverage_ratio = inventory / demand_units
        inventory_to_sales = (
            inventory / sales
            if sales > 0
            else 0.0
        )

        observations = (
            f"Current inventory is {inventory:.0f} units.",
            f"Adjusted demand score is {demand:.1f}/100.",
            f"Observed sales volume is {sales:.0f} units.",
            f"Inventory-to-demand ratio is {coverage_ratio:.2f}.",
            f"Inventory-to-sales ratio is {inventory_to_sales:.2f}.",
        )

        reasoning = []
        if inventory < max(10.0, demand * 0.25):
            reasoning.append(
                "Available stock is low relative to demand, creating a potential stock-out risk."
            )
        elif inventory > demand * 2.0:
            reasoning.append(
                "Inventory is substantially above demand, increasing holding-cost and overstock risk."
            )
        else:
            reasoning.append(
                "Inventory is broadly aligned with the current demand level."
            )

        if sales > inventory and inventory > 0:
            reasoning.append(
                "Recent sales exceed available stock, so replenishment should be considered."
            )
        elif sales > 0 and inventory_to_sales > 2.0:
            reasoning.append(
                "Stock coverage is high relative to observed sales, so additional procurement is unnecessary."
            )
        else:
            reasoning.append(
                "No immediate evidence suggests a severe shortage or clearance requirement."
            )

        evidence = (
            f"Inventory available: {inventory:.0f} units.",
            f"Adjusted demand reference: {demand:.1f}.",
            f"Current sales reference: {sales:.0f} units.",
            f"Coverage ratio used for interpretation: {coverage_ratio:.2f}.",
        )

        if "INCREASE" in operation:
            conclusion = (
                f"Inventory Agent recommends increasing stock by {value:.0f} units "
                "to reduce shortage risk."
            )
        elif "CLEAR" in operation or "DECREASE" in operation:
            conclusion = (
                f"Inventory Agent recommends reducing or clearing {abs(value):.0f} units "
                "to lower excess-stock exposure."
            )
        else:
            conclusion = (
                "Inventory Agent recommends maintaining stock because inventory "
                "and demand are currently within an acceptable range."
            )

        return AgentExplanation(
            agent="InventoryAgent",
            observations=observations,
            reasoning=tuple(reasoning),
            evidence=evidence,
            conclusion=conclusion,
        )

    def _marketing(self, payload: dict[str, Any]) -> AgentExplanation:
        s = self._scenario(payload)
        c = self._calculated(payload)
        p = self._proposal(payload, "MarketingAgent")

        visitors = _num(s.get("visitors"))
        sales = _num(s.get("sales"))
        conversion = _pct(
            c.get("conversion_rate", s.get("conversion_rate"))
        )
        ad_cost = _num(s.get("advertising_cost"))
        budget = _num(s.get("marketing_budget"))
        season = str(s.get("season") or "NORMAL")
        cost_per_sale = (
            ad_cost / sales
            if sales > 0
            else 0.0
        )
        operation = str(p.get("operation") or "NO_CHANGE")
        value = abs(_num(p.get("value")))

        observations = (
            f"Visitors: {visitors:,.0f}.",
            f"Sales: {sales:,.0f}.",
            f"Conversion rate: {conversion:.2f}%.",
            f"Advertising cost: {_money(ad_cost)}.",
            f"Marketing budget: {_money(budget)}.",
            f"Seasonal context: {season}.",
        )

        reasoning = []
        if visitors >= 1000 and conversion < 4.0:
            reasoning.append(
                "Traffic is meaningful, but too few visitors are purchasing, indicating conversion friction."
            )
        elif visitors < 500:
            reasoning.append(
                "Traffic volume is limited, so visibility and reach may be the primary issue."
            )
        else:
            reasoning.append(
                "Traffic and conversion are within a moderate range."
            )

        if sales > 0:
            reasoning.append(
                f"Advertising cost per sale is approximately {_money(cost_per_sale)}."
            )

        if season in {"SALE", "FESTIVAL"}:
            reasoning.append(
                f"The {season.lower()} period increases the potential value of promotional action."
            )
        else:
            reasoning.append(
                "There is no strong seasonal trigger requiring aggressive promotion."
            )

        evidence = (
            f"Measured traffic: {visitors:,.0f} visitors.",
            f"Measured purchases: {sales:,.0f} sales.",
            f"Calculated conversion: {conversion:.2f}%.",
            f"Advertising cost per sale: {_money(cost_per_sale)}.",
            f"Available marketing budget: {_money(budget)}.",
        )

        if operation == "DECREASE":
            conclusion = (
                f"Marketing Agent recommends a {value:.2f}% price decrease "
                "to reduce purchase hesitation and improve conversion."
            )
        elif "INCREASE_PROMOTION" in operation:
            conclusion = (
                f"Marketing Agent recommends increasing promotion by {value:.2f}% "
                "to improve reach and conversion."
            )
        elif "DECREASE_PROMOTION" in operation:
            conclusion = (
                f"Marketing Agent recommends reducing promotion by {value:.2f}% "
                "because current spend is not producing sufficient return."
            )
        else:
            conclusion = (
                "Marketing Agent recommends maintaining the current marketing approach "
                "because no stronger action is justified."
            )

        return AgentExplanation(
            agent="MarketingAgent",
            observations=observations,
            reasoning=tuple(reasoning),
            evidence=evidence,
            conclusion=conclusion,
        )
