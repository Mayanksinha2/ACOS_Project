"""
Scenario generation for ACOS.

This module creates manual and randomized e-commerce scenarios
using the existing Product, Customer, Market, and
EcommerceEnvironment classes.

It does not duplicate the business environment. It prepares
valid inputs for the existing ACOS simulator and future interface.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from simulator.customer import Customer
from simulator.ecommerce_environment import EcommerceEnvironment
from simulator.market import Market
from simulator.product import Product


@dataclass
class CommerceScenario:
    """
    Complete business scenario that can be supplied to ACOS.
    """

    scenario_id: str
    scenario_name: str
    product: Product
    customers: List[Customer]
    market: Market
    environment: EcommerceEnvironment

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def summary(self) -> Dict[str, Any]:
        """
        Return a serializable summary of the scenario.
        """

        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "created_at": self.created_at,
            "product": {
                "product_id": getattr(
                    self.product,
                    "product_id",
                    None,
                ),
                "name": getattr(
                    self.product,
                    "name",
                    None,
                ),
                "category": getattr(
                    self.product,
                    "category",
                    None,
                ),
                "cost_price": getattr(
                    self.product,
                    "cost_price",
                    None,
                ),
                "selling_price": getattr(
                    self.product,
                    "selling_price",
                    None,
                ),
                "inventory": getattr(
                    self.product,
                    "inventory",
                    None,
                ),
                "demand_level": getattr(
                    self.product,
                    "demand_level",
                    None,
                ),
            },
            "market": {
                "season": getattr(
                    self.market,
                    "season",
                    None,
                ),
                "demand_multiplier": getattr(
                    self.market,
                    "demand_multiplier",
                    None,
                ),
                "competitor_price_factor": getattr(
                    self.market,
                    "competitor_price_factor",
                    None,
                ),
                "advertising_cost": getattr(
                    self.market,
                    "advertising_cost",
                    None,
                ),
            },
            "customer_count": len(
                self.customers
            ),
            "metadata": dict(
                self.metadata
            ),
        }


class ScenarioGenerator:
    """
    Generate manual and randomized ACOS commerce scenarios.
    """

    VALID_DEMAND_LEVELS = (
        "LOW",
        "MEDIUM",
        "HIGH",
    )

    VALID_SEASONS = (
        "NORMAL",
        "SUMMER",
        "MONSOON",
        "FESTIVAL",
        "WEDDING",
        "WINTER",
    )

    VALID_PREFERENCES = (
        "PRICE",
        "QUALITY",
        "FASHION",
        "COMFORT",
        "BRAND",
    )

    VALID_CATEGORIES = (
        "KIDS_FROCK",
        "ETHNIC_WEAR",
        "PARTY_WEAR",
        "CASUAL_WEAR",
        "NIGHTWEAR",
        "BOYS_WEAR",
    )

    def __init__(
        self,
        random_seed: Optional[int] = None,
    ):
        self._random = random.Random(
            random_seed
        )

    def create_manual_scenario(
        self,
        scenario_name: str,
        product_id: str,
        product_name: str,
        category: str,
        cost_price: float,
        selling_price: float,
        inventory: int,
        demand_level: str,
        season: str,
        demand_multiplier: float,
        competitor_price_factor: float,
        advertising_cost: float,
        customer_count: int = 20,
        customer_budget_minimum: float = 500.0,
        customer_budget_maximum: float = 2000.0,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> CommerceScenario:
        """
        Build a scenario from user-provided values.
        """

        self._validate_product_values(
            cost_price=cost_price,
            selling_price=selling_price,
            inventory=inventory,
            demand_level=demand_level,
        )

        self._validate_market_values(
            demand_multiplier=demand_multiplier,
            competitor_price_factor=(
                competitor_price_factor
            ),
            advertising_cost=advertising_cost,
        )

        if customer_count <= 0:
            raise ValueError(
                "Customer count must be greater than zero."
            )

        if customer_budget_minimum <= 0:
            raise ValueError(
                "Minimum customer budget must be positive."
            )

        if (
            customer_budget_maximum
            < customer_budget_minimum
        ):
            raise ValueError(
                "Maximum customer budget cannot be "
                "lower than the minimum budget."
            )

        product = Product(
            product_id=product_id,
            name=product_name,
            category=category,
            cost_price=float(cost_price),
            selling_price=float(selling_price),
            inventory=int(inventory),
            demand_level=demand_level.upper(),
        )

        market = Market(
            season=season.upper(),
            demand_multiplier=float(
                demand_multiplier
            ),
            competitor_price_factor=float(
                competitor_price_factor
            ),
            advertising_cost=float(
                advertising_cost
            ),
        )

        customers = self._generate_customers(
            customer_count=customer_count,
            minimum_budget=(
                customer_budget_minimum
            ),
            maximum_budget=(
                customer_budget_maximum
            ),
        )

        environment = EcommerceEnvironment(
            products=[product],
            customers=customers,
            market=market,
        )

        return CommerceScenario(
            scenario_id=self._create_id(
                "SCENARIO"
            ),
            scenario_name=scenario_name,
            product=product,
            customers=customers,
            market=market,
            environment=environment,
            metadata=metadata or {
                "generation_mode": "MANUAL"
            },
        )

    def generate_random_scenario(
        self,
        scenario_name: Optional[str] = None,
        customer_count: Optional[int] = None,
    ) -> CommerceScenario:
        """
        Generate one randomized commerce scenario.
        """

        demand_level = self._random.choice(
            self.VALID_DEMAND_LEVELS
        )

        season = self._random.choice(
            self.VALID_SEASONS
        )

        category = self._random.choice(
            self.VALID_CATEGORIES
        )

        cost_price = round(
            self._random.uniform(
                250.0,
                900.0,
            ),
            2,
        )

        markup_percentage = self._random.uniform(
            0.25,
            1.20,
        )

        selling_price = round(
            cost_price
            * (1.0 + markup_percentage),
            2,
        )

        inventory = self._random.randint(
            5,
            500,
        )

        demand_multiplier = self._demand_multiplier(
            demand_level=demand_level,
            season=season,
        )

        competitor_price_factor = round(
            self._random.uniform(
                0.80,
                1.25,
            ),
            4,
        )

        advertising_cost = round(
            self._random.uniform(
                100.0,
                5000.0,
            ),
            2,
        )

        generated_customer_count = (
            customer_count
            if customer_count is not None
            else self._random.randint(
                20,
                100,
            )
        )

        scenario_number = self._random.randint(
            1000,
            9999,
        )

        return self.create_manual_scenario(
            scenario_name=(
                scenario_name
                or f"Generated Scenario {scenario_number}"
            ),
            product_id=self._create_id(
                "PRODUCT"
            ),
            product_name=(
                f"{category.replace('_', ' ').title()} "
                f"{scenario_number}"
            ),
            category=category,
            cost_price=cost_price,
            selling_price=selling_price,
            inventory=inventory,
            demand_level=demand_level,
            season=season,
            demand_multiplier=demand_multiplier,
            competitor_price_factor=(
                competitor_price_factor
            ),
            advertising_cost=advertising_cost,
            customer_count=(
                generated_customer_count
            ),
            customer_budget_minimum=500.0,
            customer_budget_maximum=3000.0,
            metadata={
                "generation_mode": "RANDOM",
                "markup_percentage": round(
                    markup_percentage,
                    4,
                ),
            },
        )

    def generate_batch(
        self,
        number_of_scenarios: int,
        customer_count: Optional[int] = None,
    ) -> List[CommerceScenario]:
        """
        Generate several randomized scenarios.
        """

        if number_of_scenarios <= 0:
            raise ValueError(
                "Number of scenarios must be greater "
                "than zero."
            )

        return [
            self.generate_random_scenario(
                scenario_name=(
                    f"Scenario {index + 1}"
                ),
                customer_count=customer_count,
            )
            for index in range(
                number_of_scenarios
            )
        ]

    def _generate_customers(
        self,
        customer_count: int,
        minimum_budget: float,
        maximum_budget: float,
    ) -> List[Customer]:
        """
        Create randomized customers using the existing model.
        """

        customers: List[Customer] = []

        for _ in range(customer_count):
            customer = Customer(
                customer_id=self._create_id(
                    "CUSTOMER"
                ),
                age=self._random.randint(
                    18,
                    60,
                ),
                budget=round(
                    self._random.uniform(
                        minimum_budget,
                        maximum_budget,
                    ),
                    2,
                ),
                preference=self._random.choice(
                    self.VALID_PREFERENCES
                ),
                price_sensitivity=round(
                    self._random.uniform(
                        0.0,
                        1.0,
                    ),
                    4,
                ),
            )

            customers.append(customer)

        return customers

    def _demand_multiplier(
        self,
        demand_level: str,
        season: str,
    ) -> float:
        """
        Calculate a reasonable randomized demand multiplier.
        """

        demand_ranges = {
            "LOW": (0.60, 0.90),
            "MEDIUM": (0.90, 1.20),
            "HIGH": (1.20, 1.80),
        }

        minimum, maximum = demand_ranges[
            demand_level
        ]

        multiplier = self._random.uniform(
            minimum,
            maximum,
        )

        if season in {
            "FESTIVAL",
            "WEDDING",
        }:
            multiplier *= self._random.uniform(
                1.05,
                1.30,
            )

        return round(
            multiplier,
            4,
        )

    @staticmethod
    def _validate_product_values(
        cost_price: float,
        selling_price: float,
        inventory: int,
        demand_level: str,
    ) -> None:
        if cost_price <= 0:
            raise ValueError(
                "Cost price must be positive."
            )

        if selling_price <= 0:
            raise ValueError(
                "Selling price must be positive."
            )

        if inventory < 0:
            raise ValueError(
                "Inventory cannot be negative."
            )

        if (
            demand_level.upper()
            not in ScenarioGenerator.VALID_DEMAND_LEVELS
        ):
            raise ValueError(
                "Demand level must be LOW, MEDIUM, "
                "or HIGH."
            )

    @staticmethod
    def _validate_market_values(
        demand_multiplier: float,
        competitor_price_factor: float,
        advertising_cost: float,
    ) -> None:
        if demand_multiplier <= 0:
            raise ValueError(
                "Demand multiplier must be positive."
            )

        if competitor_price_factor <= 0:
            raise ValueError(
                "Competitor price factor must be positive."
            )

        if advertising_cost < 0:
            raise ValueError(
                "Advertising cost cannot be negative."
            )

    @staticmethod
    def _create_id(
        prefix: str,
    ) -> str:
        return (
            f"{prefix}-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )