# [AeroNet Lite - Autonomous Drone Delivery Simulation](https://aeronetlite.streamlit.app/)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://aeronetlite.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Academic%20Project-0A7E8C)](./README.md)

AeroNet Lite is an AI-powered drone delivery simulator on a 10x10 city grid. It combines CSP validation, fleet optimization, A* routing, disruption-aware rerouting, and ML forecasting into one integrated system.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?logo=plotly&logoColor=white)

## Live App

- Demo URL: https://aeronetlite.streamlit.app/

## Core Modules

| Module | Purpose | AI Technique |
|---|---|---|
| `1_csp_validator` | Validates city layout constraints | CSP rule checking |
| `2_fleet_selector` | Picks light/heavy drone counts under budget | Heuristic / Genetic Algorithm |
| `3_astar_planner` | Computes safe shortest routes | A* Search |
| `4_disruption_handler` | Handles dynamic no-fly disruptions and reroutes | Real-time replanning |
| `5_ml_pipeline` | Forecasts demand and detects anomalies | Regression + Classification |
| `shared_utils` | Shared grid model and utility logic | Reusable core utilities |
| `ui_streamlit` | Interactive simulation and analytics dashboard | Streamlit UI |

## Project Structure

```text
asst3/
├── app_/
│   ├── 1_csp_validator/
│   ├── 2_fleet_selector/
│   ├── 3_astar_planner/
│   ├── 4_disruption_handler/
│   ├── 5_ml_pipeline/
│   ├── shared_utils/
│   └── ui_streamlit/
├── data/
├── notebooks/
├── ProblemStatement.md
├── requirements.txt
└── README.md
```

## Quick Start

1. Clone the repo and move into the project directory.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Run the Streamlit UI.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_/ui_streamlit/main.py
```

## Grid Model Snapshot

Each grid cell includes location, zoning, operations, and demand fields.

```python
{
    "row": int,
    "col": int,
    "zone": str,
    "density": int,
    "is_hub": bool,
    "is_charging": bool,
    "is_medical_pickup": bool,
    "no_fly": bool,
    "demand": float
}
```

## Team Workflow

1. Create a branch per module:

```bash
git checkout -b <your-name>/<module-name>
```

2. Commit your changes:

```bash
git add .
git commit -m "Descriptive commit message"
```

3. Push and open a PR to `main`:

```bash
git push origin <your-name>/<module-name>
```

## References

- Full scope and requirements: `ProblemStatement.md`
- Module notes: `app_/*/_.md`
- Examples/tests: `app_/*/test.py`


