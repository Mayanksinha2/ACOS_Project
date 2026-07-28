# ACOS Demonstration Platform — UI Phase 1

This package adds a working Streamlit interface on top of the current ACOS architecture.
It calls `ACOSApplicationService` and `BusinessStateBuilder` directly and does not copy agent logic.

## 1. Copy files

Copy the `acos_ui` folder into:

```text
ACOS_Project/src/acos_ui/
```

Copy these files into `ACOS_Project/src/`:

```text
run_acos_ui.py
test_acos_ui_integration.py
requirements-ui.txt
```

## 2. Install Streamlit

Activate your existing virtual environment, then run from the project root:

```powershell
pip install -r srcequirements-ui.txt
```

## 3. Verify integration first

```powershell
python -u src	est_acos_ui_integration.py
```

Expected final line:

```text
ACOS UI integration tests passed.
```

## 4. Launch the platform

```powershell
streamlit run srcun_acos_ui.py
```

The browser should open automatically. If it does not, use the local URL printed by Streamlit.

## Included in Phase 1

- Manual scenario builder
- Real execution through the existing ACOS pipeline
- Pricing, inventory, and marketing proposal cards
- Confidence and risk visualization
- Conflict detection output
- Negotiation result
- MOCRA result
- Final decision view
- Error diagnostics
- JSON download
- Browser-session run history

## Architecture

```text
Streamlit UI
    -> ACOSUIAdapter
    -> BusinessStateBuilder
    -> ACOSApplicationService
    -> Existing agents and DecisionManager
```

No existing source file must be edited for this phase.
