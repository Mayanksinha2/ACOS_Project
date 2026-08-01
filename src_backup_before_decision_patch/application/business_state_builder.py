"""
Business state construction layer for ACOS.

This module converts manual business input, simulator environments,
and generated commerce scenarios into the canonical BusinessState
consumed by ACOS agents and reasoners.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from models.business_state import BusinessState


class BusinessStateBuilder:
    """
    Build validated BusinessState objects from multiple data sources.

    The builder is the common input layer for:

    - Manual user input
    - Scenario Generator
    - E-commerce simulator
    - Experiment Runner
    - Future API and Streamlit interface
    """

    DEFAULT_DEMAND_SCORE = 50.0
    DEFAULT_ADVERTISING_COST = 0.0
    DEFAULT_CONVERSION_RATE = 0.0

    DEMAND_LEVEL_SCORES = {
        "LOW": 25.0,
        "MEDIUM": 55.0,
        "HIGH": 85.0,
    }

    @classmethod
    def build_from_manual_input(
        cls,
        *,
        product_id: str,
        inventory: int,
        demand: float,
        conversion_rate: float,
        advertising_cost: float,
        products: Optional[List[Any]] = None,
        customers: Optional[List[Any]] = None,
        sales: int = 0,
        revenue: float = 0.0,
        profit: float = 0.0,
        visitors: int = 0,
        season: str = "NORMAL",
        demand_multiplier: float = 1.0,
        competitor_price_factor: float = 1.0,
        additional_metrics: Optional[Dict[str, Any]] = None,
        additional_market: Optional[Dict[str, Any]] = None,
    ) -> BusinessState:
        """
        Build a BusinessState from explicit user or API input.
        """

        cls._validate_product_id(product_id)
        cls._validate_inventory(inventory)
        cls._validate_demand(demand)
        cls._validate_conversion_rate(conversion_rate)
        cls._validate_non_negative(
            advertising_cost,
            "advertising_cost",
        )
        cls._validate_non_negative(sales, "sales")
        cls._validate_non_negative(revenue, "revenue")
        cls._validate_non_negative(visitors, "visitors")
        cls._validate_positive(
            demand_multiplier,
            "demand_multiplier",
        )
        cls._validate_positive(
            competitor_price_factor,
            "competitor_price_factor",
        )

        metrics: Dict[str, Any] = {
            "product_id": product_id,
            "inventory": int(inventory),
            "conversion_rate": float(conversion_rate),
            "sales": int(sales),
            "revenue": float(revenue),
            "profit": float(profit),
            "visitors": int(visitors),
        }

        market: Dict[str, Any] = {
            "demand": float(demand),
            "advertising_cost": float(advertising_cost),
            "season": str(season).upper(),
            "demand_multiplier": float(demand_multiplier),
            "competitor_price_factor": float(
                competitor_price_factor
            ),
        }

        if additional_metrics:
            metrics.update(additional_metrics)

        if additional_market:
            market.update(additional_market)

        return BusinessState(
            products=list(products or []),
            customers=list(customers or []),
            market=market,
            metrics=metrics,
        )

    @classmethod
    def build_from_scenario(
        cls,
        scenario: Any,
        *,
        visitors: Optional[int] = None,
        sales: Optional[int] = None,
        revenue: Optional[float] = None,
        profit: Optional[float] = None,
        conversion_rate: Optional[float] = None,
    ) -> BusinessState:
        """
        Convert a CommerceScenario into a canonical BusinessState.

        Optional values can override values inferred from the scenario.
        """

        if scenario is None:
            raise ValueError("scenario cannot be None")

        product = getattr(scenario, "product", None)
        market_object = getattr(scenario, "market", None)
        environment = getattr(scenario, "environment", None)
        customers = list(
            getattr(scenario, "customers", []) or []
        )

        if product is None:
            raise ValueError(
                "scenario must contain a product"
            )

        product_id = getattr(
            product,
            "product_id",
            None,
        )

        cls._validate_product_id(product_id)

        inventory = cls._safe_int(
            getattr(product, "inventory", 0),
            default=0,
        )

        demand_level = str(
            getattr(
                product,
                "demand_level",
                "MEDIUM",
            )
        ).upper()

        demand_multiplier = cls._safe_float(
            getattr(
                market_object,
                "demand_multiplier",
                1.0,
            ),
            default=1.0,
        )

        demand = cls._calculate_demand_score(
            demand_level=demand_level,
            demand_multiplier=demand_multiplier,
        )

        inferred_visitors = (
            len(customers)
            if visitors is None
            else int(visitors)
        )

        environment_sales = cls._safe_int(
            getattr(
                environment,
                "total_sales",
                0,
            ),
            default=0,
        )

        environment_revenue = cls._safe_float(
            getattr(
                environment,
                "total_revenue",
                0.0,
            ),
            default=0.0,
        )

        final_sales = (
            environment_sales
            if sales is None
            else int(sales)
        )

        final_revenue = (
            environment_revenue
            if revenue is None
            else float(revenue)
        )

        inferred_conversion_rate = (
            final_sales / inferred_visitors
            if inferred_visitors > 0
            else cls.DEFAULT_CONVERSION_RATE
        )

        final_conversion_rate = (
            inferred_conversion_rate
            if conversion_rate is None
            else float(conversion_rate)
        )

        inferred_profit = cls._calculate_profit(
            product=product,
            sales=final_sales,
            revenue=final_revenue,
        )

        final_profit = (
            inferred_profit
            if profit is None
            else float(profit)
        )

        metadata = dict(
            getattr(
                scenario,
                "metadata",
                {},
            )
            or {}
        )

        return cls.build_from_manual_input(
            product_id=product_id,
            inventory=inventory,
            demand=demand,
            conversion_rate=final_conversion_rate,
            advertising_cost=cls._safe_float(
                getattr(
                    market_object,
                    "advertising_cost",
                    cls.DEFAULT_ADVERTISING_COST,
                ),
                default=cls.DEFAULT_ADVERTISING_COST,
            ),
            products=[product],
            customers=customers,
            sales=final_sales,
            revenue=final_revenue,
            profit=final_profit,
            visitors=inferred_visitors,
            season=str(
                getattr(
                    market_object,
                    "season",
                    "NORMAL",
                )
            ),
            demand_multiplier=demand_multiplier,
            competitor_price_factor=cls._safe_float(
                getattr(
                    market_object,
                    "competitor_price_factor",
                    1.0,
                ),
                default=1.0,
            ),
            additional_metrics={
                "product_name": getattr(
                    product,
                    "name",
                    None,
                ),
                "category": getattr(
                    product,
                    "category",
                    None,
                ),
                "cost_price": cls._safe_float(
                    getattr(
                        product,
                        "cost_price",
                        0.0,
                    )
                ),
                "selling_price": cls._safe_float(
                    getattr(
                        product,
                        "selling_price",
                        0.0,
                    )
                ),
                "demand_level": demand_level,
                "scenario_id": getattr(
                    scenario,
                    "scenario_id",
                    None,
                ),
                "scenario_name": getattr(
                    scenario,
                    "scenario_name",
                    None,
                ),
            },
            additional_market={
                "scenario_metadata": metadata,
            },
        )

    @classmethod
    def build_from_environment(
        cls,
        environment: Any,
        *,
        product_id: Optional[str] = None,
        visitors: Optional[int] = None,
        conversion_rate: Optional[float] = None,
        demand: Optional[float] = None,
    ) -> BusinessState:
        """
        Build BusinessState directly from EcommerceEnvironment.
        """

        if environment is None:
            raise ValueError(
                "environment cannot be None"
            )

        products = list(
            getattr(environment, "products", []) or []
        )

        customers = list(
            getattr(environment, "customers", []) or []
        )

        if not products:
            raise ValueError(
                "environment must contain at least one product"
            )

        product = cls._select_product(
            products=products,
            product_id=product_id,
        )

        market_object = getattr(
            environment,
            "market",
            None,
        )

        selected_product_id = getattr(
            product,
            "product_id",
            None,
        )

        demand_level = str(
            getattr(
                product,
                "demand_level",
                "MEDIUM",
            )
        ).upper()

        demand_multiplier = cls._safe_float(
            getattr(
                market_object,
                "demand_multiplier",
                1.0,
            ),
            default=1.0,
        )

        final_demand = (
            cls._calculate_demand_score(
                demand_level,
                demand_multiplier,
            )
            if demand is None
            else float(demand)
        )

        final_visitors = (
            len(customers)
            if visitors is None
            else int(visitors)
        )

        total_sales = cls._safe_int(
            getattr(
                environment,
                "total_sales",
                0,
            )
        )

        total_revenue = cls._safe_float(
            getattr(
                environment,
                "total_revenue",
                0.0,
            )
        )

        inferred_conversion = (
            total_sales / final_visitors
            if final_visitors > 0
            else cls.DEFAULT_CONVERSION_RATE
        )

        final_conversion = (
            inferred_conversion
            if conversion_rate is None
            else float(conversion_rate)
        )

        return cls.build_from_manual_input(
            product_id=selected_product_id,
            inventory=cls._safe_int(
                getattr(
                    product,
                    "inventory",
                    0,
                )
            ),
            demand=final_demand,
            conversion_rate=final_conversion,
            advertising_cost=cls._safe_float(
                getattr(
                    market_object,
                    "advertising_cost",
                    0.0,
                )
            ),
            products=products,
            customers=customers,
            sales=total_sales,
            revenue=total_revenue,
            profit=cls._calculate_profit(
                product=product,
                sales=total_sales,
                revenue=total_revenue,
            ),
            visitors=final_visitors,
            season=str(
                getattr(
                    market_object,
                    "season",
                    "NORMAL",
                )
            ),
            demand_multiplier=demand_multiplier,
            competitor_price_factor=cls._safe_float(
                getattr(
                    market_object,
                    "competitor_price_factor",
                    1.0,
                ),
                default=1.0,
            ),
            additional_metrics={
                "product_name": getattr(
                    product,
                    "name",
                    None,
                ),
                "category": getattr(
                    product,
                    "category",
                    None,
                ),
                "cost_price": cls._safe_float(
                    getattr(
                        product,
                        "cost_price",
                        0.0,
                    )
                ),
                "selling_price": cls._safe_float(
                    getattr(
                        product,
                        "selling_price",
                        0.0,
                    )
                ),
                "demand_level": demand_level,
            },
        )

    @classmethod
    def build_from_metrics(
        cls,
        *,
        products: Optional[List[Any]] = None,
        customers: Optional[List[Any]] = None,
        market: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> BusinessState:
        """
        Build BusinessState from already prepared dictionaries.
        """

        if not isinstance(market, dict):
            raise TypeError(
                "market must be a dictionary"
            )

        if not isinstance(metrics, dict):
            raise TypeError(
                "metrics must be a dictionary"
            )

        required_metric_keys = {
            "product_id",
            "inventory",
            "conversion_rate",
        }

        required_market_keys = {
            "demand",
            "advertising_cost",
        }

        missing_metrics = (
            required_metric_keys - metrics.keys()
        )

        missing_market = (
            required_market_keys - market.keys()
        )

        if missing_metrics:
            raise ValueError(
                "Missing metric keys: "
                + ", ".join(
                    sorted(missing_metrics)
                )
            )

        if missing_market:
            raise ValueError(
                "Missing market keys: "
                + ", ".join(
                    sorted(missing_market)
                )
            )

        return cls.build_from_manual_input(
            product_id=str(
                metrics["product_id"]
            ),
            inventory=int(
                metrics["inventory"]
            ),
            demand=float(
                market["demand"]
            ),
            conversion_rate=float(
                metrics["conversion_rate"]
            ),
            advertising_cost=float(
                market["advertising_cost"]
            ),
            products=products,
            customers=customers,
            sales=int(
                metrics.get("sales", 0)
            ),
            revenue=float(
                metrics.get("revenue", 0.0)
            ),
            profit=float(
                metrics.get("profit", 0.0)
            ),
            visitors=int(
                metrics.get("visitors", 0)
            ),
            season=str(
                market.get("season", "NORMAL")
            ),
            demand_multiplier=float(
                market.get(
                    "demand_multiplier",
                    1.0,
                )
            ),
            competitor_price_factor=float(
                market.get(
                    "competitor_price_factor",
                    1.0,
                )
            ),
            additional_metrics={
                key: value
                for key, value in metrics.items()
                if key
                not in {
                    "product_id",
                    "inventory",
                    "conversion_rate",
                    "sales",
                    "revenue",
                    "profit",
                    "visitors",
                }
            },
            additional_market={
                key: value
                for key, value in market.items()
                if key
                not in {
                    "demand",
                    "advertising_cost",
                    "season",
                    "demand_multiplier",
                    "competitor_price_factor",
                }
            },
        )

    @classmethod
    def _calculate_demand_score(
        cls,
        demand_level: str,
        demand_multiplier: float,
    ) -> float:
        """
        Convert textual demand level into the 0-100 scale
        expected by current rule reasoners.
        """

        base_score = cls.DEMAND_LEVEL_SCORES.get(
            str(demand_level).upper(),
            cls.DEFAULT_DEMAND_SCORE,
        )

        score = base_score * float(
            demand_multiplier
        )

        return round(
            max(0.0, min(100.0, score)),
            4,
        )

    @staticmethod
    def _calculate_profit(
        *,
        product: Any,
        sales: int,
        revenue: float,
    ) -> float:
        cost_price = BusinessStateBuilder._safe_float(
            getattr(
                product,
                "cost_price",
                0.0,
            )
        )

        total_cost = cost_price * int(sales)

        return round(
            float(revenue) - total_cost,
            2,
        )

    @staticmethod
    def _select_product(
        *,
        products: Iterable[Any],
        product_id: Optional[str],
    ) -> Any:
        products_list = list(products)

        if product_id is None:
            return products_list[0]

        for product in products_list:
            if (
                str(
                    getattr(
                        product,
                        "product_id",
                        "",
                    )
                )
                == str(product_id)
            ):
                return product

        raise ValueError(
            f"Product '{product_id}' was not found "
            "in the environment."
        )

    @staticmethod
    def _validate_product_id(
        product_id: Any,
    ) -> None:
        if product_id is None:
            raise ValueError(
                "product_id cannot be None"
            )

        if not str(product_id).strip():
            raise ValueError(
                "product_id cannot be empty"
            )

    @staticmethod
    def _validate_inventory(
        inventory: int,
    ) -> None:
        if int(inventory) < 0:
            raise ValueError(
                "inventory cannot be negative"
            )

    @staticmethod
    def _validate_demand(
        demand: float,
    ) -> None:
        numeric_demand = float(demand)

        if not 0.0 <= numeric_demand <= 100.0:
            raise ValueError(
                "demand must be between 0 and 100"
            )

    @staticmethod
    def _validate_conversion_rate(
        conversion_rate: float,
    ) -> None:
        numeric_rate = float(
            conversion_rate
        )

        if not 0.0 <= numeric_rate <= 1.0:
            raise ValueError(
                "conversion_rate must be between 0 and 1"
            )

    @staticmethod
    def _validate_non_negative(
        value: float,
        name: str,
    ) -> None:
        if float(value) < 0:
            raise ValueError(
                f"{name} cannot be negative"
            )

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> None:
        if float(value) <= 0:
            raise ValueError(
                f"{name} must be greater than zero"
            )

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)