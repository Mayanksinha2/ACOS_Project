# Real ACOS Pipeline Patch Guide

The ablation executor activates one `ACOSFeatureFlags` object for each run.

For variants to be genuinely different, each real ACOS component must read its corresponding flag.

## 1. Conflict Detector

At the beginning of the conflict-detection method:

```python
from ablation_execution import (
    conflict_detection_enabled,
)

if not conflict_detection_enabled():
    return []
```

Use the empty or neutral conflict result type expected by your existing pipeline.

## 2. Adaptive Negotiation Engine

Before negotiation:

```python
from ablation_execution import negotiation_enabled

if not negotiation_enabled():
    return None
```

The caller should fall back to the highest-ranked proposal or current decision.

## 3. MOCRA Decision Engine

At the point where MOCRA selects an alternative:

```python
from ablation_execution import mocra_enabled

if not mocra_enabled():
    return max(
        proposals,
        key=lambda proposal: proposal.confidence,
    )
```

This creates a meaningful non-MOCRA baseline using the highest-confidence proposal.

## 4. Adaptive Weight Optimizer

Before updating learned weights:

```python
from ablation_execution import (
    adaptive_learning_enabled,
)

if not adaptive_learning_enabled():
    return current_weights
```

## 5. Outcome Evaluator

Before post-decision outcome evaluation:

```python
from ablation_execution import (
    outcome_evaluation_enabled,
)

if not outcome_evaluation_enabled():
    return None
```

## 6. Run real variants through the existing adapter

```python
from ablation_execution import AblationExecutor
from experiment_manager import (
    execute_acos_experiment,
)

executor = AblationExecutor(
    execute=execute_acos_experiment,
)

batch = executor.execute_batch(
    base_request=request,
    variant_names=[
        "baseline",
        "without_conflict_detection",
        "without_negotiation",
        "without_mocra",
        "without_adaptive_learning",
        "without_outcome_evaluation",
    ],
    repetitions=10,
    base_seed=1000,
)
```

## 7. Feed results into aggregated evaluation

```python
from aggregated_evaluation import (
    AggregatedEvaluator,
    AggregatedEvaluationConfig,
)

evaluation = AggregatedEvaluator(
    AggregatedEvaluationConfig(
        group_by_metadata_key="ablation_variant",
        include_failed_rewards=True,
        reward_failure_value=0.0,
    )
).evaluate(batch.runs)
```

Each `AblationRunResult` already contains:

```python
metadata={
    "ablation_variant": "...",
    "feature_flags": {...},
}
```

Therefore the previously completed aggregated evaluator can group the real runs directly.
