"""Script to train both models - Run this directly from the module folder"""

import sys
import os

# Add parent directory to path for shared_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_pipeline import train_demand_model, create_synthetic_telemetry, train_anomaly_model


def train_all():
    print("=" * 60)
    print("TRAINING MODULE 5 MODELS")
    print("=" * 60)
    
    # Create directories if they don't exist
    os.makedirs("../../data/processed", exist_ok=True)
    os.makedirs("../../data/raw", exist_ok=True)
    
    print("\n📊 Step 1: Training demand forecasting model...")
    try:
        demand_metrics = train_demand_model(
            csv_path="../../data/raw/train.csv",
            model_path="../../data/processed/demand_model.pkl"
        )
        print(f"✅ Demand model trained successfully!")
        print(f"   MAE: {demand_metrics['mae']:.2f}")
        print(f"   RMSE: {demand_metrics['rmse']:.2f}")
    except FileNotFoundError:
        print("❌ train.csv not found! Please place train.csv in data/raw/ folder")
    except Exception as e:
        print(f"❌ Failed to train demand model: {e}")

    print("\n📊 Step 2: Creating synthetic telemetry data...")
    try:
        create_synthetic_telemetry(
            output_path="../../data/raw/synthetic_telemetry.csv",
            n_samples=1000
        )
        print(f"✅ Synthetic telemetry created successfully!")
    except Exception as e:
        print(f"❌ Failed to create synthetic telemetry: {e}")

    print("\n📊 Step 3: Training anomaly detection model...")
    try:
        anomaly_metrics = train_anomaly_model(
            csv_path="../../data/raw/synthetic_telemetry.csv",
            model_path="../../data/processed/anomaly_model.pkl"
        )
        print(f"✅ Anomaly model trained successfully!")
        print(f"   Accuracy: {anomaly_metrics['accuracy']*100:.2f}%")
    except Exception as e:
        print(f"❌ Failed to train anomaly model: {e}")

    print("\n" + "=" * 60)
    print("✅ All models trained and saved to data/processed/")
    print("=" * 60)


if __name__ == "__main__":
    train_all()