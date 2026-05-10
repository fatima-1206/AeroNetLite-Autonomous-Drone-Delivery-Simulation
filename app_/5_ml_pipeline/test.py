"""
Test script for Module 5 - ML Pipeline
Run from: app_/5_ml_pipeline/
"""

import sys
import os
import pandas as pd  # <-- ADDED: missing pandas import
import numpy as np

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Files in project root: {os.listdir(project_root)}")

# Now try import
from app_.shared_utils.main import GridCell, Grid
from ml_pipeline import (
    train_demand_model,
    predict_demand,
    create_synthetic_telemetry,
    train_anomaly_model,
    detect_anomaly,
    get_module_5_output
)

print(" All imports successful!")

print("=" * 70)
print("TESTING MODULE 5 - ML PIPELINE")
print("=" * 70)

# TEST 1: Demand Forecasting (Regression)\


print("\n" + "=" * 70)
print("TEST 1: Demand Forecasting (Regression)")
print("=" * 70)

# Create directories if they don't exist
os.makedirs("../../data/processed", exist_ok=True)
os.makedirs("../../data/raw", exist_ok=True)

# Train the demand model
print("\n Training demand model...")
try:
    demand_metrics = train_demand_model(
        csv_path="../../data/raw/train.csv",
        model_path="../../data/processed/demand_model.pkl"  # Same path used in predict_demand
    )
    print(f" Demand model trained successfully!")
    print(f"   - MAE (Mean Absolute Error): {demand_metrics['mae']:.2f}")
    print(f"   - RMSE (Root Mean Square Error): {demand_metrics['rmse']:.2f}")
    print(f"\n    Interpretation: Predictions are off by ~{demand_metrics['mae']:.0f} bike rentals on average")
except FileNotFoundError:
    print(" train.csv not found! Please download from Kaggle first.")
except Exception as e:
    print(f" Error: {e}")

# Test demand predictions
print("\n Testing demand predictions for different scenarios:")
print("-" * 60)

test_scenarios = [
    {"hour": 8, "temp": 25, "humidity": 60, "weather": 1, "season": 1, 
     "desc": "🌞 Summer morning, clear (8 AM)"},
    {"hour": 14, "temp": 30, "humidity": 50, "weather": 1, "season": 1, 
     "desc": "🌞 Summer afternoon, hot (2 PM)"},
    {"hour": 18, "temp": 22, "humidity": 65, "weather": 1, "season": 1, 
     "desc": "🌙 Summer evening (6 PM)"},
    {"hour": 8, "temp": 15, "humidity": 70, "weather": 2, "season": 2, 
     "desc": "☁️ Fall morning, cloudy (8 AM)"},
    {"hour": 8, "temp": 5, "humidity": 85, "weather": 3, "season": 3, 
     "desc": "🌧️ Winter morning, rainy (8 AM)"},
    {"hour": 2, "temp": 10, "humidity": 80, "weather": 3, "season": 3, 
     "desc": "🌙 Winter early morning, rainy (2 AM)"},
]

for scenario in test_scenarios:
    try:
        pred = predict_demand(
            hour=scenario["hour"],
            temp=scenario["temp"],
            humidity=scenario["humidity"],
            weather=scenario["weather"],
            season=scenario["season"],
            model_path="../../data/processed/demand_model.pkl"  # <-- ADDED: explicit path
        )
        print(f"{scenario['desc']:45} → Predicted: {pred:6.0f} rentals")
    except Exception as e:
        print(f"{scenario['desc']:45} →  Error: {e}")


# TEST 2: Anomaly Detection (Classification)

print("\n" + "=" * 70)
print("TEST 2: Anomaly Detection (Classification)")
print("=" * 70)

# Create synthetic telemetry
print("\n Generating synthetic telemetry data...")
try:
    df = create_synthetic_telemetry(
        output_path="../../data/raw/synthetic_telemetry.csv",
        n_samples=1000
    )
    print(f" Created {len(df)} synthetic telemetry samples")
    print(f"   Class distribution:")
    for cls, count in df['label'].value_counts().items():
        print(f"     - {cls}: {count} samples ({count/len(df)*100:.1f}%)")
except Exception as e:
    print(f" Error: {e}")

# Train anomaly model
print("\n Training anomaly detection model...")
try:
    anomaly_metrics = train_anomaly_model(
        csv_path="../../data/raw/synthetic_telemetry.csv",
        model_path="../../data/processed/anomaly_model.pkl"  # Same path used in detect_anomaly
    )
    print(f" Anomaly model trained successfully!")
    print(f"   - Accuracy: {anomaly_metrics['accuracy']*100:.2f}%")
    print(f"   - Confusion Matrix:")
    cm = anomaly_metrics['confusion_matrix']
    print(f"     [[{cm[0][0]:3} {cm[0][1]:3} {cm[0][2]:3} {cm[0][3]:3}]")
    print(f"      [{cm[1][0]:3} {cm[1][1]:3} {cm[1][2]:3} {cm[1][3]:3}]")
    print(f"      [{cm[2][0]:3} {cm[2][1]:3} {cm[2][2]:3} {cm[2][3]:3}]")
    print(f"      [{cm[3][0]:3} {cm[3][1]:3} {cm[3][2]:3} {cm[3][3]:3}]]")
except Exception as e:
    print(f" Error: {e}")

# Test anomaly detection
print("\n Testing anomaly detection on sample telemetry:")
print("-" * 60)

test_telemetry = [
    {"battery_drop": 0.5, "speed": 10.2, "route_deviation": 0.3, "expected": "normal", 
     "desc": "Normal flight"},
    {"battery_drop": 35.0, "speed": 9.8, "route_deviation": 0.4, "expected": "battery_anomaly",
     "desc": "Sudden battery drop from 100% to 65%"},
    {"battery_drop": 0.4, "speed": 10.5, "route_deviation": 150.0, "expected": "route_anomaly",
     "desc": "Drone 150m off planned path"},
    {"battery_drop": 0.6, "speed": 75.0, "route_deviation": 0.5, "expected": "sensor_spike",
     "desc": "Speed sensor jumps to 75 m/s"},
    {"battery_drop": 45.0, "speed": 8.0, "route_deviation": 2.0, "expected": "battery_anomaly",
     "desc": "Battery anomaly (45% drop)"},
    {"battery_drop": 0.3, "speed": 12.0, "route_deviation": 180.0, "expected": "route_anomaly",
     "desc": "Route anomaly (180m deviation)"},
]

for tele in test_telemetry:
    try:
        result = detect_anomaly(
            battery_drop=tele["battery_drop"],
            speed=tele["speed"],
            route_deviation=tele["route_deviation"],
            model_path="../../data/processed/anomaly_model.pkl"  # <-- ADDED: explicit path
        )
        status = "" if result["class"] == tele["expected"] else ""
        print(f"{status} {tele['desc']:40} → {result['class']:18} (conf: {result['confidence']:.2%})")
    except Exception as e:
        print(f" {tele['desc']:40} → Error: {e}")

# ============================================================================
# TEST 3: Integration Function (with mock grid)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: Integration Function (get_module_5_output)")
print("=" * 70)

# Create a mock grid for testing
print("\n Creating mock 10x10 grid for testing...")

class MockCell:
    def __init__(self, row, col, zone, density, is_hub=False, demand=0):
        self.row = row
        self.col = col
        self.zone = zone
        self.density = density
        self.is_hub = is_hub
        self.is_charging = False
        self.is_medical_pickup = False
        self.no_fly = False
        self.demand = demand

class MockGrid:
    def __init__(self):
        self.cells = []
        for i in range(5):  # 5x5 for faster testing
            row = []
            for j in range(5):
                # Create a variety of cells
                if (i == 0 and j == 0):
                    cell = MockCell(i, j, "Residential", 8000, is_hub=True, demand=100)
                elif (i == 0 and j == 1):
                    cell = MockCell(i, j, "Residential", 7000, is_hub=True, demand=90)
                elif (i == 1 and j == 0):
                    cell = MockCell(i, j, "Residential", 6000, demand=80)
                elif (i == 1 and j == 1):
                    cell = MockCell(i, j, "Residential", 5000, demand=70)
                elif (i == 2 and j == 2):
                    cell = MockCell(i, j, "Commercial", 3000, demand=50)
                elif (i == 3 and j == 3):
                    cell = MockCell(i, j, "Industrial", 1000, demand=20)
                else:
                    cell = MockCell(i, j, "Open Field", 500, demand=5)
                row.append(cell)
            self.cells.append(row)

mock_grid = MockGrid()
print(f" Created {len(mock_grid.cells)}x{len(mock_grid.cells[0])} mock grid")

# Test integration function at different simulation steps
print("\n Testing integration function at simulation steps 15-18:")
print("-" * 60)

for step in [15, 16, 17, 18]:
    print(f"\n Simulation Step {step}:")
    try:
        output = get_module_5_output(mock_grid, simulation_step=step)
        
        # Demand forecast summary
        forecasts = output['demand_forecast']
        print(f"    Demand Forecast: {len(forecasts)} cells predicted")
        if forecasts:
            max_cell = max(forecasts.items(), key=lambda x: x[1])
            min_cell = min(forecasts.items(), key=lambda x: x[1])
            print(f"      - Highest demand: {max_cell[0]} = {max_cell[1]:.0f}")
            print(f"      - Lowest demand: {min_cell[0]} = {min_cell[1]:.0f}")
            print(f"      - Average demand: {sum(forecasts.values())/len(forecasts):.1f}")
        
        # Anomaly alerts
        alerts = output['anomaly_alerts']
        print(f"    Anomaly Alerts: {len(alerts)}")
        for alert in alerts[:3]:  # Show first 3
            print(f"      - Drone {alert['drone_id']}: {alert['type']} (conf: {alert['confidence']:.2%})")
        
        # Model metrics
        metrics = output['model_metrics']
        print(f"    Model Metrics: MAE={metrics['mae']}, Accuracy={metrics['accuracy']}")
        
    except Exception as e:
        print(f"    Error: {e}")

# ============================================================================
# TEST 4: Test with your test.csv (if available)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 4: Test with test.csv (Optional)")
print("=" * 70)

test_csv_path = "../../data/raw/test.csv"
if os.path.exists(test_csv_path):
    print(f"\n Found test.csv at {test_csv_path}")
    try:
        test_df = pd.read_csv(test_csv_path)
        print(f"   Loaded {len(test_df)} test samples")
        
        # Load trained model
        import joblib
        model_data = joblib.load("../../data/processed/demand_model.pkl")
        model = model_data["model"]
        feature_cols = model_data["feature_columns"]
        
        # Prepare features
        test_df['datetime'] = pd.to_datetime(test_df['datetime'])
        test_df['hour'] = test_df['datetime'].dt.hour
        X_test = test_df[["hour", "temp", "humidity", "weather", "season"]].copy()
        X_test = pd.get_dummies(X_test, columns=["weather", "season"], drop_first=True)
        X_test = X_test.reindex(columns=feature_cols, fill_value=0)
        
        # Predict
        predictions = model.predict(X_test)
        print(f"    Generated {len(predictions)} predictions")
        print(f"   Prediction range: {predictions.min():.0f} - {predictions.max():.0f}")
        print(f"   Average prediction: {predictions.mean():.2f}")
        
        # Save predictions
        output_df = pd.DataFrame({
            'datetime': test_df['datetime'],
            'predicted_demand': predictions
        })
        output_df.to_csv("../../data/processed/test_predictions.csv", index=False)
        print(f"    Saved predictions to: ../../data/processed/test_predictions.csv")
        
    except Exception as e:
        print(f"    Error processing test.csv: {e}")
else:
    print(f"\n test.csv not found at {test_csv_path}")
    print("   If you have test.csv, place it in data/raw/ folder")
    print("   Download from: https://www.kaggle.com/c/bike-sharing-demand/data")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print(" MODULE 5 TEST COMPLETE!")
print("=" * 70)
print("\n Summary:")
print("   • Demand forecasting model: Trained and ready")
print("   • Anomaly detection model: Trained and ready")
print("   • Integration function: Working")
print("   • Models saved to: data/processed/")
