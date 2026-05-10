"""ML Dashboard UI components for Module 5.

Provides visualization components for:
- Demand forecasting heatmap (10x10 grid)
- Anomaly alerts panel
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from typing import Dict, Any, List
import importlib.util
import sys
from pathlib import Path

from app_.shared_utils.main import Grid


def display_demand_heatmap(demand_forecast: Dict[str, float], step: int) -> None:
	"""
	Create and display a 10x10 heatmap from demand_forecast dict.
	
	Args:
		demand_forecast: dict with keys "cell_(row,col)" and float demand values
		step: simulation step number (for title)
	"""
	# Parse demand_forecast into a 10x10 grid
	grid_data = np.zeros((10, 10))
	
	for key, value in demand_forecast.items():
		# Parse "cell_(row,col)" format
		try:
			parts = key.replace("cell_(", "").replace(")", "").split(",")
			row = int(parts[0])
			col = int(parts[1])
			grid_data[row, col] = float(value)
		except (ValueError, IndexError):
			continue
	
	# Create matplotlib figure with seaborn heatmap
	fig, ax = plt.subplots(figsize=(10, 8))
	
	# Use RdYlGn_r colormap (Red=high demand, Green=low demand)
	sns.heatmap(
		grid_data,
		annot=True,
		fmt=".1f",
		cmap="RdYlGn_r",
		cbar_kws={"label": "Demand (units)"},
		linewidths=0.5,
		linecolor="gray",
		ax=ax,
		xticklabels=[f"Col {i}" for i in range(10)],
		yticklabels=[f"Row {i}" for i in range(10)],
	)
	
	ax.set_title(f"Delivery Demand Heatmap - Step {step}", fontsize=14, fontweight="bold")
	ax.set_xlabel("Column", fontsize=11)
	ax.set_ylabel("Row", fontsize=11)
	
	plt.tight_layout()
	
	# Display in Streamlit
	st.pyplot(fig)
	
	# Show statistics
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.metric("Max Demand", f"{grid_data.max():.1f}")
	with col2:
		st.metric("Min Demand", f"{grid_data.min():.1f}")
	with col3:
		st.metric("Avg Demand", f"{grid_data.mean():.1f}")
	with col4:
		st.metric("Total Demand", f"{grid_data.sum():.1f}")


def display_anomaly_alerts(anomaly_alerts: List[Dict[str, Any]], step: int) -> None:
	"""
	Display anomaly alerts as a formatted, color-coded table.
	
	Args:
		anomaly_alerts: list of dicts with keys: drone_id, type, confidence
		step: simulation step number
	"""
	if not anomaly_alerts:
		st.info("✅ No anomalies detected at this step")
		return
	
	# Build alerts dataframe
	alert_data = []
	for alert in anomaly_alerts:
		alert_data.append({
			"Step": step,
			"Drone ID": alert.get("drone_id", "Unknown"),
			"Anomaly Type": alert.get("type", "unknown").replace("_", " ").upper(),
			"Confidence": f"{alert.get('confidence', 0):.1%}",
		})
	
	df_alerts = pd.DataFrame(alert_data)
	
	# Display count and severity summary
	col1, col2, col3 = st.columns(3)
	with col1:
		st.metric("🚨 Total Alerts", len(df_alerts))
	with col2:
		battery_count = len([a for a in anomaly_alerts if a.get("type") == "battery_anomaly"])
		st.metric("🔴 Battery Issues", battery_count)
	with col3:
		route_count = len([a for a in anomaly_alerts if a.get("type") == "route_anomaly"])
		st.metric("🟠 Route Issues", route_count)
	
	# Display table with conditional coloring
	st.write("**Alert Details:**")
	
	# Create color mapping for alert types
	def color_anomaly_type(val: str) -> str:
		if "BATTERY" in val:
			return "background-color: #ffcccc"  # Light red
		elif "ROUTE" in val:
			return "background-color: #ffe6cc"  # Light orange
		elif "SENSOR" in val:
			return "background-color: #ffffcc"  # Light yellow
		return ""
	
	# Apply styling and display
	styled_df = df_alerts.style.applymap(
		color_anomaly_type,
		subset=["Anomaly Type"]
	)
	st.dataframe(styled_df, use_container_width=True)
	
	# Recommendations
	st.write("**Recommendations:**")
	for alert in anomaly_alerts:
		anomaly_type = alert.get("type", "")
		drone_id = alert.get("drone_id", "")
		confidence = alert.get("confidence", 0)
		
		if anomaly_type == "battery_anomaly":
			st.warning(f"⚠️ {drone_id}: Land at nearest charging pad immediately (confidence: {confidence:.0%})")
		elif anomaly_type == "route_anomaly":
			st.warning(f"⚠️ {drone_id}: Reroute to safe path (confidence: {confidence:.0%})")
		elif anomaly_type == "sensor_spike":
			st.warning(f"⚠️ {drone_id}: Verify sensor calibration, continue with caution (confidence: {confidence:.0%})")


def refresh_ml_dashboard(grid: Grid, step: int) -> None:
	"""
	Main integration function for ML Pipeline dashboard.
	
	Calls get_module_5_output and displays both heatmap and anomaly alerts.
	
	Args:
		grid: 10x10 Grid object from shared_utils
		step: current simulation step
	"""
	# Import here to avoid circular dependency (using importlib for digit-prefixed module)
	get_module_5_output = None
	try:
		ML_DIR = Path(__file__).resolve().parent.parent / "5_ml_pipeline"
		ml_spec = importlib.util.spec_from_file_location("ml_pipeline", str(ML_DIR / "ml_pipeline.py"))
		if ml_spec:
			ml_module = importlib.util.module_from_spec(ml_spec)
			ml_spec.loader.exec_module(ml_module)
			get_module_5_output = ml_module.get_module_5_output
	except Exception as e:
		st.error(f"ML Pipeline module not available: {e}")
		return
	
	if get_module_5_output is None:
		st.error("ML Pipeline module not available")
		return
	
	# Get output from ML pipeline
	try:
		output = get_module_5_output(grid, step)
	except Exception as e:
		st.error(f"Failed to generate ML pipeline output: {e}")
		return
	
	# Create tabs
	heatmap_tab, alerts_tab = st.tabs(["📈 Demand Heatmap", "⚠️ Anomaly Alerts"])
	
	with heatmap_tab:
		st.write(f"**Step {step}**: Forecasted delivery demand across the 10x10 grid")
		display_demand_heatmap(output.get("demand_forecast", {}), step)
	
	with alerts_tab:
		st.write(f"**Step {step}**: Real-time drone telemetry anomalies")
		display_anomaly_alerts(output.get("anomaly_alerts", []), step)
	
	# Show model metrics if available
	metrics = output.get("model_metrics", {})
	if metrics.get("mae") is not None or metrics.get("accuracy") is not None:
		st.write("**Model Metrics:**")
		col1, col2 = st.columns(2)
		if metrics.get("mae") is not None:
			with col1:
				st.metric("Demand Model MAE", f"{metrics['mae']:.2f}")
		if metrics.get("accuracy") is not None:
			with col2:
				st.metric("Anomaly Model Accuracy", f"{metrics['accuracy']:.2%}")
