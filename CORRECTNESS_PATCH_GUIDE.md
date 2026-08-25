# ACOS Decision Intelligence Correctness Patch

This patch addresses the integrity issues found during the deep review.

## Corrected

1. Dynamic confidence, risk, priority and action magnitude
2. MOCRA scores now vary with scenario severity
3. Backend evidence now contains actual metrics
4. Removed "Generated using Reasoner" as fake evidence
5. Prevented accidental unchanged outcome submissions
6. Best agent hidden until evidence is sufficient
7. Reliability labelled provisional / insufficient
8. Agent profile connected to real persistent outcomes
9. Marketing card label clarified
10. Persistent outcomes synchronized into KnowledgeBase
11. KnowledgeBase entries influence future MOCRA scores through the
    existing KnowledgeGuidedScoreCalculator

## Learning activation

Knowledge is synchronized only when an agent or operation has:

```text
at least 3 evaluated outcomes
and |average reward| >= 0.05
```

This prevents neutral or single-run noise from modifying MOCRA.

## Backup

```powershell
Copy-Item src src_backup_before_correctness_patch -Recurse
```

## Install

Copy this package's `src` folder into the ACOS project root and replace
matching files.

## Test

```powershell
python -u src\test_decision_intelligence_correctness.py
```

Then run:

```powershell
python -u src\test_pricing_agent.py
python -u src\test_inventory_agent.py
python -u src\test_marketing_agent.py
python -u src\test_acos_ui_phase3c_xai.py
python -u src\test_acos_ui_phase3b.py
python -u src\test_acos_ui_integration.py
```

## Expected behavioral proof

Run two low-conversion scenarios:

```text
Conversion 3.9%
Conversion 1.0%
```

They should no longer produce identical Marketing values, confidence,
risk, priority or MOCRA scores.

Record at least three positive outcomes for the same winning agent and
operation. A later run should show knowledge adjustment fields in the
MOCRA technical result:

```text
base_final_score
knowledge_modifier
knowledge_applied
knowledge_adjustment
```
