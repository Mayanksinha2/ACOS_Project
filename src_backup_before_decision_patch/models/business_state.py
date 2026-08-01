from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass(frozen=True)
class BusinessState:

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    products: List[Any] = field(default_factory=list)

    customers: List[Any] = field(default_factory=list)

    market: Dict[str, Any] = field(default_factory=dict)

    metrics: Dict[str, Any] = field(default_factory=dict)