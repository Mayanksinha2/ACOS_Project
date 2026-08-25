from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from application.acos_application_service import ACOSApplicationService
from application.business_state_builder import BusinessStateBuilder

from .result_serializer import to_serializable


@dataclass(frozen=True, slots=True)
class ScenarioInput:
    product_id: str = "PROD-DEMO-001"
    inventory: int = 25
    demand: float = 80.0
    conversion_rate: float = 0.04
    advertising_cost: float = 1000.0
    visitors: int = 500
    sales: int = 20
    revenue: float = 15980.0
    profit: float = 6500.0
    season: str = "FESTIVAL"
    demand_multiplier: float = 1.2
    competitor_price_factor: float = 1.0
    current_price: float = 799.0
    unit_cost: float = 420.0
    marketing_budget: float = 25000.0

    @property
    def calculated_conversion_rate(self) -> float:
        return self.sales / self.visitors if self.visitors > 0 else 0.0

    @property
    def adjusted_demand(self) -> float:
        return min(100.0, max(0.0, self.demand * self.demand_multiplier))

    @property
    def average_selling_price(self) -> float:
        return self.revenue / self.sales if self.sales > 0 else 0.0

    def validate(self) -> None:
        if not self.product_id.strip():
            raise ValueError("Product ID is required.")
        if self.inventory < 0 or self.visitors < 0 or self.sales < 0:
            raise ValueError("Inventory, visitors, and sales cannot be negative.")
        if self.sales > self.visitors and self.visitors > 0:
            raise ValueError("Sales cannot exceed visitors.")
        if not 0 <= self.demand <= 100:
            raise ValueError("Demand must be between 0 and 100.")
        if not 0 <= self.conversion_rate <= 1:
            raise ValueError("Conversion rate must be between 0 and 1.")
        if self.demand_multiplier <= 0 or self.competitor_price_factor <= 0:
            raise ValueError("Demand and competitor factors must be positive.")
        if min(
            self.current_price,
            self.unit_cost,
            self.marketing_budget,
            self.advertising_cost,
            self.revenue,
        ) < 0:
            raise ValueError(
                "Price, cost, budget, advertising cost, and revenue cannot be negative."
            )

    def validation_warnings(self) -> list[str]:
        warnings: list[str] = []

        expected_conversion = self.calculated_conversion_rate
        if abs(self.conversion_rate - expected_conversion) > 0.0001:
            warnings.append(
                f"Conversion rate was corrected from {self.conversion_rate * 100:.2f}% "
                f"to {expected_conversion * 100:.2f}% using sales ÷ visitors."
            )

        if self.sales > 0 and self.current_price > 0:
            realized_price = self.average_selling_price
            difference = abs(realized_price - self.current_price) / self.current_price
            if difference > 0.05:
                warnings.append(
                    f"Average realized selling price is ₹{realized_price:,.2f}, which differs "
                    f"from current price ₹{self.current_price:,.2f} by more than 5%."
                )

        simple_profit = (
            self.revenue
            - (self.sales * self.unit_cost)
            - self.advertising_cost
        )
        if abs(simple_profit - self.profit) > max(
            100.0,
            abs(simple_profit) * 0.10,
        ):
            warnings.append(
                f"Entered profit ₹{self.profit:,.2f} differs from the simple calculated "
                f"profit ₹{simple_profit:,.2f}. Shipping, commission, returns, tax, or "
                "other operating expenses may explain the difference."
            )
        return warnings


class ACOSUIAdapter:
    """Stable UI boundary over the existing ACOS application service."""

    def __init__(
        self,
        service: ACOSApplicationService | None = None,
    ) -> None:
        self.service = service or ACOSApplicationService()

    def build_state(self, scenario: ScenarioInput):
        scenario.validate()
        return BusinessStateBuilder.build_from_manual_input(
            product_id=scenario.product_id.strip(),
            inventory=scenario.inventory,
            demand=scenario.demand,
            conversion_rate=scenario.calculated_conversion_rate,
            advertising_cost=scenario.advertising_cost,
            visitors=scenario.visitors,
            sales=scenario.sales,
            revenue=scenario.revenue,
            profit=scenario.profit,
            season=scenario.season,
            demand_multiplier=scenario.demand_multiplier,
            competitor_price_factor=scenario.competitor_price_factor,
            additional_metrics={
                "current_price": scenario.current_price,
                "unit_cost": scenario.unit_cost,
                "marketing_budget": scenario.marketing_budget,
                "average_selling_price": scenario.average_selling_price,
            },
        )

    def run(self, scenario: ScenarioInput):
        return self.service.run_safely(
            self.build_state(scenario)
        )

    def run_payload(
        self,
        scenario: ScenarioInput,
    ) -> dict[str, Any]:
        result = self.run(scenario)
        payload = self.payload_from_result(result)
        payload["scenario"] = asdict(scenario)
        payload["input_warnings"] = scenario.validation_warnings()
        payload["calculated_metrics"] = {
            "current_price": scenario.current_price,
            "conversion_rate": scenario.calculated_conversion_rate,
            "adjusted_demand": scenario.adjusted_demand,
            "average_selling_price": scenario.average_selling_price,
            "simple_profit": (
                scenario.revenue
                - (scenario.sales * scenario.unit_cost)
                - scenario.advertising_cost
            ),
        }
        return payload

    def payload_from_result(
        self,
        result: Any,
    ) -> dict[str, Any]:
        proposals = []
        for proposal in getattr(result, "proposals", []) or []:
            action = getattr(proposal, "business_action", None)
            proposals.append(
                {
                    "agent": getattr(proposal, "agent_id", "Unknown Agent"),
                    "goal": getattr(proposal, "goal", ""),
                    "operation": getattr(action, "operation", ""),
                    "action_type": getattr(action, "action_type", ""),
                    "target": getattr(action, "target", ""),
                    "value": getattr(action, "value", None),
                    "unit": getattr(action, "unit", None),
                    "rationale": getattr(action, "rationale", ""),
                    "confidence": float(
                        getattr(proposal, "confidence", 0.0) or 0.0
                    ),
                    "risk": float(
                        getattr(proposal, "risk", 0.0) or 0.0
                    ),
                    "evidence": list(
                        getattr(proposal, "evidence", []) or []
                    ),
                    "raw": to_serializable(proposal),
                }
            )

        summary = result.summary() if hasattr(result, "summary") else {}
        return {
            "summary": to_serializable(summary),
            "run_id": getattr(result, "run_id", ""),
            "timestamp": getattr(result, "timestamp", ""),
            "status": getattr(result, "status", "UNKNOWN"),
            "successful": bool(getattr(result, "successful", False)),
            "errors": list(getattr(result, "errors", []) or []),
            "business_state": to_serializable(
                getattr(result, "business_state", None)
            ),
            "proposals": proposals,
            "conflicts": to_serializable(
                getattr(result, "conflicts", [])
            ),
            "negotiation_required": bool(
                getattr(result, "negotiation_required", False)
            ),
            "negotiation_result": to_serializable(
                getattr(result, "negotiation_result", None)
            ),
            "mocra_result": to_serializable(
                getattr(result, "mocra_result", None)
            ),
            "final_decision": to_serializable(
                getattr(result, "final_decision", None)
            ),
            "metadata": to_serializable(
                getattr(result, "metadata", {})
            ),
            "raw": to_serializable(result),
        }
