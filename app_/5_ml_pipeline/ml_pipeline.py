"""ML pipeline for Module 5: demand forecasting and anomaly detection.

Assumptions and notes:
- Bike sharing `cnt` is used as a proxy for delivery demand (simplification).
- Synthetic telemetry rules: classes are created with fixed proportions (normal 85%,
  three anomaly types 5% each). Features are simple numeric signals for demo.
- Uses the shared grid model from `app_.shared_utils.main` (source-of-truth).

All file paths are relative to the project root (default arguments).
"""

# to run : puthon test.py

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

try:
    from app_.shared_utils.main import GridCell, Grid
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app_.shared_utils.main import GridCell, Grid
    
RANDOM_SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEMAND_MODEL_PATH = PROJECT_ROOT / "data" / "processed" / "demand_model.pkl"
DEFAULT_ANOMALY_MODEL_PATH = PROJECT_ROOT / "data" / "processed" / "anomaly_model.pkl"


def _zone_multiplier(cell: GridCell) -> float:
    zone_weights = {
        "Residential": 1.18,
        "Commercial": 1.05,
        "Hospital": 1.28,
        "School": 0.92,
        "Industrial": 0.72,
        "Open Field": 0.42,
    }
    multiplier = zone_weights.get(cell.zone, 1.0)
    if cell.is_hub:
        multiplier *= 1.12
    if cell.is_charging:
        multiplier *= 1.04
    if cell.is_medical_pickup:
        multiplier *= 1.08
    return multiplier


def _ensure_dir_for(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def train_demand_model(csv_path: str = "data/raw/train.csv", model_path: str = str(DEFAULT_DEMAND_MODEL_PATH)) -> Dict[str, float]:
    """
    Train RandomForestRegressor on bike sharing `train.csv`.

    Returns: dict with 'mae' and 'rmse'.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Demand CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Expected columns: datetime (for hour extraction), temp, humidity, weather, season, count
    required_cols = {"datetime", "temp", "humidity", "weather", "season", "count"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"train.csv missing required columns. Expected at least: {required_cols}")

    # Extract hour from datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['hour'] = df['datetime'].dt.hour

    X = df[["hour", "temp", "humidity", "weather", "season"]].copy()
    y = df["count"].astype(float)

    # One-hot / simple encoding for categorical features
    X = pd.get_dummies(X, columns=["weather", "season"], drop_first=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

    model = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    mse = mean_squared_error(y_test, preds)
    rmse = float(np.sqrt(mse))

    _ensure_dir_for(model_path)
    joblib.dump({"model": model, "feature_columns": X.columns.tolist()}, model_path)

    return {"mae": mae, "rmse": rmse}


def predict_demand(hour: int, temp: float, humidity: float, weather: Any, season: Any, model_path: str = str(DEFAULT_DEMAND_MODEL_PATH)) -> float:
    """Load trained demand model and predict a single demand value."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Demand model not found: {model_path}")

    payload = joblib.load(model_path)
    model = payload["model"]
    cols = payload["feature_columns"]

    sample = pd.DataFrame([{"hour": hour, "temp": temp, "humidity": humidity, "weather": weather, "season": season}])
    sample = pd.get_dummies(sample, columns=["weather", "season"], drop_first=True)

    # Reindex to match training columns, missing cols -> 0
    sample = sample.reindex(columns=cols, fill_value=0)

    pred = model.predict(sample)[0]
    return float(pred)


def create_synthetic_telemetry(output_path: str = "data/raw/synthetic_telemetry.csv", n_samples: int = 1000, random_seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate synthetic telemetry with classes: normal (85%), battery_anomaly (5%),
    route_anomaly (5%), sensor_spike (5%). Features: battery_drop, speed, route_deviation.

    Returns: DataFrame and writes to `output_path`.
    """
    rng = np.random.RandomState(random_seed)
    classes = ["normal", "battery_anomaly", "route_anomaly", "sensor_spike"]
    probs = [0.85, 0.05, 0.05, 0.05]

    labels = rng.choice(classes, size=n_samples, p=probs)

    # Baseline distributions
    battery_drop = np.where(labels == "battery_anomaly", rng.uniform(20, 60, size=n_samples), rng.uniform(0, 5, size=n_samples))
    speed = np.where(labels == "route_anomaly", rng.normal(3.0, 1.5, size=n_samples), rng.normal(5.0, 1.0, size=n_samples))
    # sensor spike: large outliers in speed or battery
    sensor_spike_noise = np.where(labels == "sensor_spike", rng.normal(0, 20, size=n_samples), 0.0)
    speed = speed + sensor_spike_noise

    route_deviation = np.where(labels == "route_anomaly", rng.uniform(50, 200, size=n_samples), rng.uniform(0, 10, size=n_samples))

    df = pd.DataFrame({
        "battery_drop": battery_drop.astype(float),
        "speed": speed.astype(float),
        "route_deviation": route_deviation.astype(float),
        "label": labels,
    })

    _ensure_dir_for(output_path)
    df.to_csv(output_path, index=False)
    return df


def train_anomaly_model(csv_path: str = "data/raw/synthetic_telemetry.csv", model_path: str = str(DEFAULT_ANOMALY_MODEL_PATH)) -> Dict[str, Any]:
    """
    Train a RandomForestClassifier on synthetic telemetry.

    Returns: dict with 'accuracy' and 'confusion_matrix' (list).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Telemetry CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if not {"battery_drop", "speed", "route_deviation", "label"}.issubset(df.columns):
        raise ValueError("Synthetic telemetry missing required columns")

    X = df[["battery_drop", "speed", "route_deviation"]].astype(float)
    y = df["label"].astype(str)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=RANDOM_SEED, stratify=y_enc)

    clf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = float(accuracy_score(y_test, preds))
    cm = confusion_matrix(y_test, preds).tolist()

    _ensure_dir_for(model_path)
    joblib.dump({"model": clf, "label_encoder": le}, model_path)

    return {"accuracy": acc, "confusion_matrix": cm}


def detect_anomaly(battery_drop: float, speed: float, route_deviation: float, model_path: str = str(DEFAULT_ANOMALY_MODEL_PATH)) -> Dict[str, Any]:
    """Return predicted class and confidence for a telemetry sample."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Anomaly model not found: {model_path}")

    payload = joblib.load(model_path)
    clf = payload["model"]
    le = payload["label_encoder"]

    sample = pd.DataFrame([[float(battery_drop), float(speed), float(route_deviation)]], columns=["battery_drop", "speed", "route_deviation"])
    preds = clf.predict(sample)
    probs = clf.predict_proba(sample)

    pred_label = le.inverse_transform(preds)[0]
    confidence = float(probs.max())

    return {"class": pred_label, "confidence": confidence}


def get_module_5_output(grid: Grid, simulation_step: int) -> Dict[str, Any]:
    """
    Integration function used by the simulation.

    - demand_forecast: predicts demand for each cell keyed by "cell_(r,c)"
    - anomaly_alerts: simulated per-hub drone telemetry detection
    - model_metrics: aggregated metrics (uses available models if present)
    """
    # Demand forecasting across the grid: use each cell's density/zone to build features
    demand_forecast: Dict[str, float] = {}
    anomaly_alerts: list[Dict[str, Any]] = []
    model_metrics: Dict[str, float] = {"mae": None, "accuracy": None}

    # Try to load demand model and anomaly model; swallow errors to allow graceful fallback
    demand_model_path = str(DEFAULT_DEMAND_MODEL_PATH)
    anomaly_model_path = str(DEFAULT_ANOMALY_MODEL_PATH)

    # For demand predictions we will use a simple heuristic for temperature/humidity/weather/season
    hour = simulation_step % 24
    # Simplifications for demo purposes
    temp = 20.0 + (simulation_step % 10)
    humidity = 50.0
    weather = "Clear"
    season = "Summer"

    # Forecast for each cell. The same model prediction is scaled by cell density,
    # zone type, and special-cell bonuses so neighboring cells do not collapse to
    # identical values even when the base demand predictor is stable.
    for row in grid.cells:
        for cell in row:
            key = f"cell_({cell.row},{cell.col})"
            try:
                pred = predict_demand(hour=hour, temp=temp, humidity=humidity, weather=weather, season=season, model_path=demand_model_path)
                density_factor = max(0.05, cell.density / 10000.0)
                demand_value = pred * density_factor * _zone_multiplier(cell)
                demand_forecast[key] = float(round(demand_value, 2))
            except Exception:
                density_factor = max(0.05, cell.density / 10000.0)
                demand_value = (cell.demand + (hour / 24.0)) * density_factor * _zone_multiplier(cell)
                demand_forecast[key] = float(round(demand_value, 2))

    # For anomaly detection, simulate a telemetry sample per hub cell (if any)
    rng = np.random.RandomState(RANDOM_SEED + simulation_step)
    for row in grid.cells:
        for cell in row:
            if getattr(cell, "is_hub", False):
                # create a synthetic telemetry sample for a drone near this hub
                battery_drop = float(max(0.0, rng.normal(2.0, 3.0)))
                speed = float(max(0.1, rng.normal(5.0, 1.0)))
                route_deviation = float(max(0.0, rng.normal(1.0, 2.0)))
                try:
                    res = detect_anomaly(battery_drop=battery_drop, speed=speed, route_deviation=route_deviation, model_path=anomaly_model_path)
                    if res["class"] != "normal":
                        anomaly_alerts.append({"drone_id": f"drone_{cell.row}_{cell.col}", "type": res["class"], "confidence": res["confidence"]})
                except Exception:
                    # If model missing, skip alerts
                    pass

    # Try to collect metric summaries if models exist
    try:
        if os.path.exists(demand_model_path):
            # We don't recompute metrics here; leave None or load saved metrics if desired
            model_metrics["mae"] = None
    except Exception:
        pass

    try:
        if os.path.exists(anomaly_model_path):
            model_metrics["accuracy"] = None
    except Exception:
        pass

    return {"demand_forecast": demand_forecast, "anomaly_alerts": anomaly_alerts, "model_metrics": model_metrics}
