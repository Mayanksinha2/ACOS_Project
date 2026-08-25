# ACOS UI Phase 3B — Outcome Feedback and Persistent Learning

Phase 3B connects completed ACOS decisions to real business outcomes.

## What this phase adds

- Evaluate Outcome page
- before-versus-after business metrics
- transparent reward calculation
- SUCCESS / NEUTRAL / FAILURE classification
- persistent SQLite learning store
- Learning Dashboard
- reward trend
- agent reliability
- agent success and failure rates
- operation performance
- persistent experience explorer
- stored run snapshots
- safe compatibility bridge for existing research learning modules

## Important architecture decision

This phase does **not** guess or replace undocumented constructors in the
existing research learning package.

It adds a stable feedback and persistence boundary:

```text
ACOS decision
→ Real business outcome
→ UIOutcomeEvaluator
→ PersistentLearningStore
→ ExistingLearningBridge
```

The bridge confirms which existing learning modules are importable and
creates a stable feedback payload for the deeper research integration.

## Backup

From the project root:

```powershell
Copy-Item src\acos_ui src\acos_ui_backup_before_phase3b -Recurse
```

## Install

Extract the ZIP and copy its `src` folder into:

```text
C:\Users\mayan\OneDrive\Desktop\ACOS_Project\
```

Choose **Replace files in the destination**.

## Run the Phase 3B test

```powershell
python -u src\test_acos_ui_phase3b.py
```

Expected:

```text
ACOS UI Phase 3B tests passed.
```

## Regression tests

```powershell
python -u src\test_acos_ui_phase3a.py
python -u src\test_acos_ui_phase2.py
python -u src\test_acos_ui_integration.py
```

## Start the platform

```powershell
python -m streamlit run src\run_acos_ui.py
```

## Workflow

1. Run a scenario.
2. Review the final decision.
3. Apply the recommendation in a real or simulated business setting.
4. Open **Evaluate outcome**.
5. Enter the actual after-result metrics.
6. Save the evaluation.
7. Open **Learning dashboard**.

## Reward formula

```text
Profit                  35%
Conversion              25%
Revenue                 20%
Inventory health        10%
Customer satisfaction   10%
```

Each relative metric change is bounded between -1 and +1 before the
weight is applied. Final reward is also bounded between -1 and +1.

Classification:

```text
reward >= +0.05  → SUCCESS
reward <= -0.05  → FAILURE
otherwise        → NEUTRAL
```

## Persistence

Default database:

```text
data\acos_learning.db
```

Override it with an environment variable:

```powershell
$env:ACOS_LEARNING_DB = "C:\path\to\learning.db"
```

The experience data remains available after restarting Streamlit or
restarting the computer.

## Next milestone

Phase 3C will intentionally map the stable Phase 3B feedback payload into
the exact existing `LearningEngine`, `ExperienceMemory`,
`AdaptiveWeightOptimizer`, and `KnowledgeBase` APIs, then show learned
weight modifiers influencing later MOCRA decisions.
