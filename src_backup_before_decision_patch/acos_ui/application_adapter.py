from __future__ import annotations

from dataclasses import dataclass
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

    def validate(self) -> None:
        if not self.product_id.strip():
            raise ValueError("Product ID is required.")
        if self.inventory < 0 or self.visitors < 0 or self.sales < 0:
            raise ValueError("Inventory, visitors, and sales cannot be negative.")
        if not 0 <= self.demand <= 100:
            raise ValueError("Demand must be between 0 and 100.")
        if not 0 <= self.conversion_rate <= 1:
            raise ValueError("Conversion rate must be between 0 and 1.")
        if self.demand_multiplier <= 0 or self.competitor_price_factor <= 0:
            raise ValueError("Demand and competitor factors must be positive.")


class ACOSUIAdapter:
    """Stable UI boundary over the existing ACOS application service."""

    def __init__(self, service: ACOSApplicationService | None = None) -> None:
        self.service = service or ACOSApplicationService()

    def build_state(self, scenario: ScenarioInput):
        scenario.validate()
        return BusinessStateBuilder.build_from_manual_input(
            product_id=scenario.product_id.strip(),
            inventory=scenario.inventory,
            demand=scenario.demand,
            conversion_rate=scenario.conversion_rate,
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
            },
        )

    def run(self, scenario: ScenarioInput):
        return self.service.run_safely(self.build_state(scenario))

    def run_payload(self, scenario: ScenarioInput) -> dict[str, Any]:
        result = self.run(scenario)
        return self.payload_from_result(result)

    def payload_from_result(self, result: Any) -> dict[str, Any]:
        proposals = []
        for proposal in getattr(result, "proposals", []) or []:
            action = getattr(proposal, "business_action", None)
            proposals.append({
                "agent": getattr(proposal, "agent_id", "Unknown Agent"),
                "goal": getattr(proposal, "goal", ""),
                "operation": getattr(action, "operation", ""),
                "action_type": getattr(action, "action_type", ""),
                "target": getattr(action, "target", ""),
                "value": getattr(action, "value", None),
                "unit": getattr(action, "unit", None),
                "rationale": getattr(action, "rationale", ""),
                "confidence": float(getattr(proposal, "confidence", 0.0) or 0.0),
                "risk": float(getattr(proposal, "risk", 0.0) or 0.0),
                "evidence": list(getattr(proposal, "evidence", []) or []),
                "raw": to_serializable(proposal),
            })

        summary = result.summary() if hasattr(result, "summary") else {}
        return {
            "summary": to_serializable(summary),
            "run_id": getattr(result, "run_id", ""),
            "timestamp": getattr(result, "timestamp", ""),
            "status": getattr(result, "status", "UNKNOWN"),
            "successful": bool(getattr(result, "successful", False)),
            "errors": list(getattr(result, "errors", []) or []),
            "business_state": to_serializable(getattr(result, "business_state", None)),
            "proposals": proposals,
            "conflicts": to_serializable(getattr(result, "conflicts", [])),
            "negotiation_required": bool(getattr(result, "negotiation_required", False)),
            "negotiation_result": to_serializable(getattr(result, "negotiation_result", None)),
            "mocra_result": to_serializable(getattr(result, "mocra_result", None)),
            "final_decision": to_serializable(getattr(result, "final_decision", None)),
            "metadata": to_serializable(getattr(result, "metadata", {})),
            "raw": to_serializable(result),
        }
