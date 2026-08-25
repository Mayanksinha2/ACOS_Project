from __future__ import annotations

from typing import Any


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(minimum, min(float(value), maximum))


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def adjusted_demand(business_state: Any) -> float:
    market = getattr(business_state, "market", {}) or {}
    base = safe_float(market.get("demand"), 50.0)
    multiplier = safe_float(
        market.get("demand_multiplier"),
        1.0,
    )
    return clamp(base * multiplier, 0.0, 100.0)


def conversion_rate(business_state: Any) -> float:
    metrics = getattr(business_state, "metrics", {}) or {}
    visitors = safe_float(metrics.get("visitors"))
    sales = safe_float(metrics.get("sales"))

    if visitors > 0:
        return clamp(sales / visitors, 0.0, 1.0)

    return clamp(
        safe_float(metrics.get("conversion_rate"), 0.0),
        0.0,
        1.0,
    )


def current_price(business_state: Any) -> float:
    metrics = getattr(business_state, "metrics", {}) or {}
    return max(
        0.0,
        safe_float(
            metrics.get(
                "current_price",
                metrics.get(
                    "selling_price",
                    0.0,
                ),
            )
        ),
    )


def competitor_factor(business_state: Any) -> float:
    market = getattr(business_state, "market", {}) or {}
    return max(
        0.1,
        safe_float(
            market.get("competitor_price_factor"),
            1.0,
        ),
    )


def profit_margin(business_state: Any) -> float:
    metrics = getattr(business_state, "metrics", {}) or {}
    revenue = safe_float(metrics.get("revenue"))
    profit = safe_float(metrics.get("profit"))
    if revenue <= 0:
        return 0.0
    return clamp(profit / revenue, -1.0, 1.0)


def product_id(business_state: Any) -> str:
    metrics = getattr(business_state, "metrics", {}) or {}
    return str(
        metrics.get("product_id")
        or "UNKNOWN_PRODUCT"
    )


def inventory_level(business_state: Any) -> float:
    metrics = getattr(business_state, "metrics", {}) or {}
    return max(0.0, safe_float(metrics.get("inventory"), 0.0))


def sales_volume(business_state: Any) -> float:
    metrics = getattr(business_state, "metrics", {}) or {}
    return max(0.0, safe_float(metrics.get("sales"), 0.0))


def visitors_count(business_state: Any) -> float:
    metrics = getattr(business_state, "metrics", {}) or {}
    return max(0.0, safe_float(metrics.get("visitors"), 0.0))


def advertising_cost(business_state: Any) -> float:
    market = getattr(business_state, "market", {}) or {}
    return max(
        0.0,
        safe_float(market.get("advertising_cost"), 0.0),
    )


def season(business_state: Any) -> str:
    market = getattr(business_state, "market", {}) or {}
    return str(market.get("season") or "NORMAL").upper()


def round_step(
    value: float,
    step: float = 1.0,
) -> float:
    if step <= 0:
        return float(value)
    return round(float(value) / step) * step
