# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AeroNet Lite System                      │
└─────────────────────────────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
            ┌───────▼──────┐  ┌──▼─────────┐
            │ Configuration│  │ Shared Grid│
            │    & Input   │  │   Model    │
            └──────┬───────┘  └──┬─────────┘
                   │             │
         ┌─────────┴─────────────┴────────────┐
         │                                    │
    ┌────▼────────┐        ┌────────────┬────▼────────────┐
    │ CSP Validator├───────►│Grid Status │ Fleet Selector  │
    │(Module 1)   │        │(Valid/     ├────────────────►│
    └─────────────┘        │Invalid)    │ (Module 2)      │
                           └────────────┴─────────────────┘
                                                │
                           ┌────────────────────┴────────┐
                           │                             │
                    ┌──────▼──────────┐    ┌────────────▼────┐
                    │ A* Path Planner │    │ Route Directory │
                    │ (Module 3)      │    │ & Delivery List │
                    └──────┬──────────┘    └────────────┬────┘
                           │                            │
                    ┌──────▼────────────────────────────▼───┐
                    │  Disruption Handler (Module 4)       │
                    │  - Detect no-fly zone activations   │
                    │  - Trigger rerouting                │
                    │  - Update route status              │
                    └──────┬─────────────────────────────┬─┘
                           │                             │
                    ┌──────▼──┐            ┌─────────────▼────┐
                    │Historical│           │ Updated Routes & │
                    │Data Logs │           │ Delivery Status  │
                    └──────┬──┘            └────────────┬─────┘
                           │                            │
                           └────────────────┬───────────┘
                                            │
                    ┌───────────────────────▼──────────┐
                    │  ML Pipeline (Module 5)          │
                    │  - Demand Forecasting            │
                    │  - Flight Anomaly Detection      │
                    │  - Pattern Analysis              │
                    └───────────────────┬──────────────┘
                                        │
                    ┌───────────────────▼──────────┐
                    │ Streamlit UI Dashboard       │
                    │ - Grid Visualization         │
                    │ - Routes & Hubs              │
                    │ - Fleet Status               │
                    │ - Alerts & Forecasts         │
                    └──────────────────────────────┘
```

## Module Interface Specifications

### Module 1: CSP Validator
**Input**: Grid model  
**Output**: Validation report (valid: bool, errors: list)  
**Algorithm**: Constraint checking (4 rules)

```python
validator.check_all_constraints(grid) → {
    "valid": bool,
    "errors": [{"rule": str, "cell": tuple, "message": str}],
    "warnings": [str]
}
```

### Module 2: Fleet Selector
**Input**: Validated grid + demand estimates  
**Output**: Selected drone fleet list  
**Algorithm**: Heuristic/Genetic Algorithm

```python
selector.select_fleet(grid, budget=10000) → {
    "fleet": [{"type": str, "id": int, "location": tuple}],
    "total_cost": float,
    "coverage": float,
    "efficiency_score": float
}
```

### Module 3: A* Path Planner
**Input**: Grid + deliveries + fleet  
**Output**: Routes for each drone  
**Algorithm**: A* search

```python
planner.plan_delivery(grid, deliveries, fleet) → {
    "routes": [{"drone_id": int, "path": [(row, col), ...], "cost": float}],
    "total_distance": float,
    "feasible": bool
}
```

### Module 4: Disruption Handler
**Input**: Current routes + new no-fly cells  
**Output**: Rerouting instructions  
**Algorithm**: Optimization/replanning

```python
handler.handle_disruption(grid, active_routes, new_no_fly_cells) → {
    "affected_routes": [int],
    "new_routes": [dict],
    "rerouting_cost": float,
    "success": bool
}
```

### Module 5: ML Pipeline
**Input**: Historical data + current deliveries  
**Output**: Forecasts + anomaly alerts  
**Algorithm**: Regression + Classification

```python
ml.analyze(grid, history_data, flight_logs) → {
    "demand_forecast": dict,
    "anomaly_alerts": [dict],
    "confidence_scores": dict
}
```

## Data Structures

### Grid Cell
```python
GridCell = {
    "row": int,
    "col": int,
    "zone": Literal["Residential", "Industrial", "Hospital", "School", "Open Field"],
    "density": int,
    "is_hub": bool,
    "is_charging": bool,
    "is_medical_pickup": bool,
    "no_fly": bool,
    "demand": float
}
```

### Drone
```python
Drone = {
    "id": int,
    "type": Literal["Light", "Heavy"],
    "location": tuple,  # (row, col)
    "capacity": float,  # kg
    "range": float,    # cells
    "available": bool
}
```

### Delivery
```python
Delivery = {
    "id": int,
    "origin": tuple,    # (row, col)
    "destination": tuple,  # (row, col)
    "weight": float,    # kg
    "priority": Literal["Normal", "High", "Medical"],
    "deadline": int     # simulation steps
}
```

## Integration Checklist

- [ ] Shared grid model finalized and tested
- [ ] Module 1 (CSP) validates grid without errors
- [ ] Module 2 (Fleet) selects viable fleet
- [ ] Module 3 (A*) plans feasible routes
- [ ] Module 4 (Disruption) handles rerouting
- [ ] Module 5 (ML) produces forecasts
- [ ] UI integrates all results
- [ ] Full 20-step simulation runs end-to-end
- [ ] Dashboard displays real-time updates

## Testing Strategy

### Unit Tests (Per Module)
- Test with sample grids
- Test edge cases and boundary conditions
- Mock external dependencies

### Integration Tests
- Test module chaining
- Verify data format compatibility
- Simulate full pipeline

### System Tests
- Run 20-step simulation
- Verify dashboard responsiveness
- Check output validity

## Performance Targets

| Component | Target | Notes |
|-----------|--------|-------|
| Grid Validation | < 100ms | 10x10 grid |
| Fleet Selection | < 500ms | Max 50 drones |
| Path Planning (one route) | < 100ms | A* with heuristic |
| Disruption Response | < 200ms | Real-time requirement |
| Dashboard Update | < 1s | Streamlit refresh |
| Full Simulation Step | < 1s | 20 total steps |
