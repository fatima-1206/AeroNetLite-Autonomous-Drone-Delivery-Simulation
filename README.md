# AeroNet Lite - Autonomous Drone Delivery Simulation

A comprehensive drone delivery simulator implementing Constraint Satisfaction Problems (CSP), fleet planning, A* routing, disruption handling, and ML-based demand forecasting.

## Development Instructions

### Git Workflow
1. **Create your own branch** for your module:
   ```bash
   git checkout -b <your-name>/<module-name>
   # Example: git checkout -b fatima/csp-validator
   ```

2. **Develop and commit** on your branch:
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

3. **Push to your branch**:
   ```bash
   git push origin <your-name>/<module-name>
   ```

4. **Open a Pull Request (PR)** when ready:
   - Push your branch to GitHub
   - Go to the repository and create a PR to `main`
   - Wait for team review and approval before merging

**Note:** Always work on your own branch. Never commit directly to `main`.


## 🚁 Project Overview

AeroNet Lite models a 10x10 city grid where autonomous drones deliver packages. The system integrates five core AI modules:

| Module | Description | AI Technique |
|--------|-------------|--------------|
| **1. CSP Validator** | Validates city layout against operational constraints | Constraint Satisfaction Problem |
| **2. Fleet Selector** | Selects optimal drone fleet under budget constraints | Heuristic/Genetic Algorithm |
| **3. A* Planner** | Plans shortest safe delivery routes | A* Search |
| **4. Disruption Handler** | Reacts to no-fly zones and reroutes affected drones | Optimization |
| **5. ML Pipeline** | Forecasts demand and detects flight anomalies | Regression & Classification |

## 📁 Project Structure

```
asst3/
├── app_/
│   ├── 1_csp_validator/      # Grid layout constraint validation
│   ├── 2_fleet_selector/     # Drone fleet optimization
│   ├── 3_astar_planner/      # Delivery route planning
│   ├── 4_disruption_handler/ # Dynamic rerouting on disruptions
│   ├── 5_ml_pipeline/        # Demand forecasting & anomaly detection
│   ├── shared_utils/         # Shared grid model and utilities
│   └── ui_streamlit/         # Dashboard and visualization
├── ProblemStatement.md        # Full requirements and specifications
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```


## 🗺️ Grid Model (Shared Across All Modules)

Each cell in the 10x10 grid contains:

```python
{
    "row": int,                    # Row index (0-9)
    "col": int,                    # Column index (0-9)
    "zone": str,                   # Zone type: "Residential", "Industrial", "Hospital", "School", "Open Field"
    "density": int,                # Population density (used for demand estimation)
    "is_hub": bool,                # Drone hub location
    "is_charging": bool,           # Charging pad location
    "is_medical_pickup": bool,     # Medical supply pickup point
    "no_fly": bool,                # No-fly restriction (blocks routing)
    "demand": float                # Estimated delivery demand
}
```

## 👥 Team Quick Reference

### Module Assignments
- **1_csp_validator**: Geography/Constraints specialist
- **2_fleet_selector**: Optimization/Search specialist
- **3_astar_planner**: Pathfinding specialist
- **4_disruption_handler**: Real-time systems specialist
- **5_ml_pipeline**: Machine Learning specialist
- **shared_utils**: Data model owner (coordinate with all modules)
- **ui_streamlit**: Integration/Visualization specialist

### Collaboration Best Practices
1. **Always use the shared grid model** from `shared_utils/` - don't create duplicate definitions
2. **Test your module independently** before integration
3. **Document assumptions** about grid data format in your module
4. **Commit early and often** with descriptive messages
5. **Update shared_utils/** if grid model needs changes (communicate with team)

## 📚 Additional Resources

- See `ProblemStatement.md` for full technical specifications
- Each module directory contains a `_.txt` file with module-specific notes
- Check `test.py` files for usage examples


