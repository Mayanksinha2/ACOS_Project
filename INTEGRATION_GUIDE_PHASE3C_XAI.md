# ACOS UI Phase 3C — Dynamic Explainable AI

This patch replaces repeated template evidence with dynamic, metric-backed
explanations generated from the actual scenario values.

## What changes

Each agent card now shows:

- Conclusion
- Observed business facts
- Reasoning chain
- Metric-backed evidence

The explanation changes with every scenario because it reads:

- current price;
- competitor price factor;
- adjusted demand;
- conversion;
- profit and revenue;
- inventory;
- visitors and sales;
- advertising cost;
- marketing budget;
- season;
- the agent's actual operation and value.

## Important distinction

This is a deterministic explainability engine, not a generative LLM.
That is intentional for research reproducibility. It never invents facts;
every displayed number comes from the completed ACOS payload.

## Install

Back up:

```powershell
Copy-Item src\acos_ui src\acos_ui_backup_before_phase3c_xai -Recurse
```

Copy this package's `src` folder into the ACOS project root and replace
the matching UI files.

## Test

```powershell
python -u src\test_acos_ui_phase3c_xai.py
```

Expected:

```text
ACOS UI Phase 3C XAI tests passed.
```

Run regression tests:

```powershell
python -u src\test_acos_ui_phase3b.py
python -u src\test_acos_ui_phase3a.py
python -u src\test_acos_ui_phase2.py
python -u src\test_acos_ui_integration.py
```

Start:

```powershell
python -m streamlit run src\run_acos_ui.py
```
