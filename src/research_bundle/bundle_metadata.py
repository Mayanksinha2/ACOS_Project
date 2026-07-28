from __future__ import annotations

import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class BundleMetadata:
    """
    Reproducibility and provenance metadata
    for one ACOS research bundle.
    """

    project_name: str = (
        "Autonomous Commerce Optimization System"
    )

    project_acronym: str = "ACOS"
    project_version: str = "1.0.0"
    framework_version: str = "1.0.0"

    researcher_name: Optional[str] = None
    institution_name: Optional[str] = None

    experiment_id: Optional[str] = None
    experiment_name: Optional[str] = None

    git_commit: Optional[str] = None
    random_seed: Optional[int] = None

    bundle_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    python_version: str = field(
        default_factory=lambda: (
            sys.version.split()[0]
        )
    )

    operating_system: str = field(
        default_factory=platform.platform
    )

    additional_metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)