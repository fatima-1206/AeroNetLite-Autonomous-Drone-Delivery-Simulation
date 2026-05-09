"""Streamlit UI for AeroNet Lite Grid Visualization.

This module provides an interactive visualization of the 10x10 city grid
used in the autonomous drone delivery simulation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path
import importlib
import os
from typing import Any, Dict, List
from datetime import datetime

MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
VALIDATOR_DIR = APP_DIR / "1_csp_validator"
ASTAR_DIR = APP_DIR / "3_astar_planner"
DISRUPTION_DIR = APP_DIR / "4_disruption_handler"
ML_DIR = APP_DIR / "5_ml_pipeline"

# Add parent directory to path for imports
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(VALIDATOR_DIR))
sys.path.insert(0, str(DISRUPTION_DIR))
sys.path.insert(0, str(ML_DIR))

from shared_utils.main import Grid, GridCell
from shared_utils.grid_defs import (
	create_grid_multi_violation,
	create_grid_r1_violation,
	create_grid_r2_violation,
	create_grid_r3_violation,
	create_grid_r4_violation,
	create_valid_compact_grid,
	create_valid_sample_grid,
)
from backtracking import solve as backtracking_solve
from forward_checking import solve as forward_checking_solve
from arc_consistenct import solve as arc_consistency_solve

# Import A* functions
astar_spec = importlib.util.spec_from_file_location("astar_planner", str(ASTAR_DIR / "main.py"))
astar_module = importlib.util.module_from_spec(astar_spec)
astar_spec.loader.exec_module(astar_module)
astar = astar_module.astar
plan_delivery_route = astar_module.plan_delivery_route

# Import Disruption Handler
disruption_module = None
DisruptionManager = None
Drone = None
activate_no_fly = None
route_contains_blocked_cell = None
reroute_drone = None
force_return_to_hub = None

try:
    disruption_spec = importlib.util.spec_from_file_location("disruption_handler", str(DISRUPTION_DIR / "main.py"))
    if disruption_spec:
        disruption_module = importlib.util.module_from_spec(disruption_spec)
        sys.modules[disruption_spec.name] = disruption_module
        disruption_spec.loader.exec_module(disruption_module)
        DisruptionManager = disruption_module.DisruptionManager
        Drone = disruption_module.Drone
        activate_no_fly = disruption_module.activate_no_fly
        route_contains_blocked_cell = disruption_module.route_contains_blocked_cell
        reroute_drone = disruption_module.reroute_drone
        force_return_to_hub = disruption_module.force_return_to_hub
except Exception as e:
    st.warning(f"Disruption Handler module not available. Some features will be disabled. Error: {e}")

# Import ML Pipeline
ml_module = None
predict_demand = None
detect_anomaly = None
get_module_5_output = None
train_demand_model = None
train_anomaly_model = None
create_synthetic_telemetry = None

try:
    ml_spec = importlib.util.spec_from_file_location("ml_pipeline", str(ML_DIR / "ml_pipeline.py"))
    if ml_spec:
        ml_module = importlib.util.module_from_spec(ml_spec)
        ml_spec.loader.exec_module(ml_module)
        predict_demand = ml_module.predict_demand
        detect_anomaly = ml_module.detect_anomaly
        get_module_5_output = ml_module.get_module_5_output
        train_demand_model = ml_module.train_demand_model
        train_anomaly_model = ml_module.train_anomaly_model
        create_synthetic_telemetry = ml_module.create_synthetic_telemetry
except Exception as e:
    st.warning(f"ML Pipeline module not available. Some features will be disabled. Error: {e}")

# Color mapping for different zone types
ZONE_COLORS = {
	"Residential": "#ADD8E6",      # Light blue
	"Commercial": "#FFD699",        # Light orange
	"Hospital": "#FFB6C1",          # Light pink
	"School": "#90EE90",            # Light green
	"Industrial": "#D2B48C",        # Tan/beige
	"Open Field": "#E8E8E8",        # Light gray
}

# Special marker styles
MARKER_STYLES = {
	"hub": "HUB",
	"charging": "CHG",
	"medical_pickup": "MED",
	"no_fly": "NO-FLY",
}


GRID_PRESETS = [
	("Sample Grid", create_valid_sample_grid),
	("Compact Valid Grid", create_valid_compact_grid),
	("R1 Violation Grid", create_grid_r1_violation),
	("R2 Violation Grid", create_grid_r2_violation),
	("R3 Violation Grid", create_grid_r3_violation),
	("R4 Violation Grid", create_grid_r4_violation),
	("Multi-Violation Grid", create_grid_multi_violation),
]

ALGORITHM_LABELS = {
	"backtracking": "Backtracking",
	"forward_checking": "Forward Checking",
	"arc_consistency": "Arc Consistency",
}

ALGORITHM_SOLVERS = {
	"backtracking": backtracking_solve,
	"forward_checking": forward_checking_solve,
	"arc_consistency": arc_consistency_solve,
}


def get_cell_display_text(cell: GridCell) -> str:
	"""Get display text for a cell including zone name and markers."""
	text = cell.zone
	
	if cell.is_hub:
		text = "HUB"
	elif cell.is_charging:
		text = "CHG"
	elif cell.is_medical_pickup:
		text = "MED"
	elif cell.no_fly:
		text = "NO-FLY"
	
	return text


def create_grid_table(grid: Grid) -> pd.DataFrame:
	"""Create a pandas DataFrame representation of the grid for display."""
	data = []
	for row in grid.cells:
		for cell in row:
			data.append({
				"Row": cell.row,
				"Col": cell.col,
				"Zone": cell.zone,
				"Density": cell.density,
				"Demand": f"{cell.demand:.2f}",
				"Hub": "✓" if cell.is_hub else "",
				"Charging": "✓" if cell.is_charging else "",
				"Medical": "✓" if cell.is_medical_pickup else "",
				"No-Fly": "✓" if cell.no_fly else "",
			})
	return pd.DataFrame(data)


def create_plotly_grid_visualization(grid: Grid, paths: list[list[tuple[int, int]]] = None, points: dict = None) -> go.Figure:
	"""Create an interactive Plotly visualization of the grid."""
	fig = go.Figure()
	
	# Create heatmap data
	grid_size = 10
	z = [[0] * grid_size for _ in range(grid_size)]
	hover_text = [[f"({i},{j})" for j in range(grid_size)] for i in range(grid_size)]
	
	# Create custom colors and text for each cell
	colors = []
	texts = []
	
	for row_idx in range(grid_size):
		color_row = []
		text_row = []
		for col_idx in range(grid_size):
			cell = grid.get_cell(row_idx, col_idx)
			if cell:
				# Get zone color
				color_row.append(ZONE_COLORS.get(cell.zone, "#FFFFFF"))
				
				# Create cell display text
				display_text = f"({row_idx}, {col_idx})<br>{cell.zone}<br>Density: {cell.density}"
				
				# Add markers
				markers = []
				if cell.is_hub:
					markers.append("HUB")
				if cell.is_charging:
					markers.append("CHG")
				if cell.is_medical_pickup:
					markers.append("MED")
				if cell.no_fly:
					markers.append("NO-FLY")
				
				if markers:
					display_text += "<br>" + " | ".join(markers)
				
				display_text += f"<br>Demand: {cell.demand:.1f}"
				text_row.append(display_text)
			else:
				color_row.append("#FFFFFF")
				text_row.append("")
		
		colors.append(color_row)
		texts.append(text_row)
	
	# Create the main grid visualization using rectangles
	for row_idx in range(grid_size):
		for col_idx in range(grid_size):
			cell = grid.get_cell(row_idx, col_idx)
			if cell:
				# Get cell color
				color = ZONE_COLORS.get(cell.zone, "#FFFFFF")
				
				# Create cell display text
				display_text = f"({row_idx}, {col_idx})<br>{cell.zone}<br>Density: {cell.density}"
				
				# Add markers
				markers = []
				if cell.is_hub:
					markers.append("HUB")
				if cell.is_charging:
					markers.append("CHG")
				if cell.is_medical_pickup:
					markers.append("MED")
				if cell.no_fly:
					markers.append("NO-FLY")
				
				if markers:
					display_text += "<br>" + " | ".join(markers)
				
				display_text += f"<br>Demand: {cell.demand:.1f}"
				
				# Add rectangle for each cell
				fig.add_trace(go.Scatter(
					x=[col_idx, col_idx + 1, col_idx + 1, col_idx, col_idx],
					y=[grid_size - row_idx, grid_size - row_idx, grid_size - row_idx - 1, grid_size - row_idx - 1, grid_size - row_idx],
					fill="toself",
					fillcolor=color,
					line=dict(color="#000000", width=1),
					hovertext=display_text,
					hoverinfo="text",
					mode="lines",
					showlegend=False,
					name="",
				))
				
				# Add text label on cell
				cell_label = get_cell_display_text(cell)
				fig.add_annotation(
					x=col_idx + 0.5,
					y=grid_size - row_idx - 0.5,
					text=cell_label,
					showarrow=False,
					font=dict(size=10, color="#000000"),
					xanchor="center",
					yanchor="middle",
				)
	
	# Add paths if provided
	if paths:
		path_colors = ['red', 'blue', 'green']  # hub->pickup, pickup->dropoff, dropoff->hub
		for i, path in enumerate(paths):
			if path:
				x_coords = [p[1] + 0.5 for p in path]
				y_coords = [grid_size - p[0] - 0.5 for p in path]
				fig.add_trace(go.Scatter(
					x=x_coords,
					y=y_coords,
					mode='lines+markers',
					line=dict(color=path_colors[i % len(path_colors)], width=3),
					marker=dict(size=8, color=path_colors[i % len(path_colors)]),
					name=f'Path {i+1}',
					showlegend=True
				))
	
	# Add special points if provided
	if points:
		for label, (r, c) in points.items():
			fig.add_trace(go.Scatter(
				x=[c + 0.5],
				y=[grid_size - r - 0.5],
				mode='markers+text',
				marker=dict(size=15, color='yellow', symbol='star'),
				text=[label],
				textposition="top center",
				name=label,
				showlegend=True
			))
	
	# Update layout
	fig.update_layout(
		title="<b>Sample 10x10 Region Grid</b>",
		xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, grid_size], constrain="domain"),
		yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, grid_size], scaleanchor="x", scaleratio=1),
		hovermode="closest",
		plot_bgcolor="white",
		paper_bgcolor="white",
		autosize=True,
		height=900,
		margin=dict(l=50, r=50, t=80, b=50),
	)
	
	return fig


def create_legend():
	"""Create a legend for zone types and markers."""
	legend_data = {
		"Zone Type": list(ZONE_COLORS.keys()),
		"Color": ["█ " + color for color in ZONE_COLORS.values()],
	}
	
	marker_data = {
		"Marker": ["HUB", "CHG", "MED", "NO-FLY"],
		"Meaning": ["Drone Hub", "Charging Pad", "Medical Supply", "No-Fly Zone"],
	}
	
	return pd.DataFrame(legend_data), pd.DataFrame(marker_data)


def render_zone_legend() -> None:
	"""Render a color legend that matches the grid cells."""
	for zone, color in ZONE_COLORS.items():
		st.markdown(
			f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;'>"
			f"<span style='width:16px;height:16px;background:{color};border:1px solid #666;display:inline-block;'></span>"
			f"<span>{zone}</span>"
			f"</div>",
			unsafe_allow_html=True,
		)


def create_zone_distribution_figure(zone_df: pd.DataFrame) -> go.Figure:
	"""Create a color-matched bar chart for zone distribution."""
	fig = go.Figure(
		go.Bar(
			x=zone_df["Zone"],
			y=zone_df["Count"],
			marker_color=[ZONE_COLORS.get(zone, "#999999") for zone in zone_df["Zone"]],
			text=zone_df["Count"],
			textposition="auto",
		)
	)
	fig.update_layout(
		margin=dict(l=10, r=10, t=10, b=10),
		plot_bgcolor="white",
		paper_bgcolor="white",
		yaxis=dict(title="Cells", gridcolor="#EAEAEA"),
		xaxis=dict(title="Zone", tickangle=-20),
		showlegend=False,
	)
	return fig


def get_grid_preset(index: int) -> tuple[str, Grid]:
	"""Return the selected grid preset name and a freshly built grid."""
	name, factory = GRID_PRESETS[index]
	return name, factory()


def render_validation_summary(validation_result: dict) -> None:
	"""Render the CSP validation result and any rule violations."""
	if validation_result is None:
		st.warning("Validation result not available")
		return
	
	if validation_result.get("valid", False):
		st.success("This grid is valid for the selected CSP algorithm.")
		return

	st.error("This grid is invalid. The validator found the following issue(s):")
	for error in validation_result.get("errors", []):
		cell = error.get("cell", ("?", "?"))
		st.write(f"- {error.get('rule', 'Unknown rule')} at {cell}: {error.get('message', 'No details available')}")

	warnings = validation_result.get("warnings", [])
	if warnings:
		st.caption("Warnings: " + " | ".join(warnings))


def render_disruption_handler(grid: Grid):
    """Render the Disruption Handler UI section."""
    st.subheader("Module 4: Real-Time Disruption Handler")
    
    # Check if module is available
    if DisruptionManager is None or Drone is None:
        st.warning("⚠️ Disruption Handler module not available. Please ensure Module 4 is properly installed.")
        return
    
    # Initialize session state for drones and disruption manager
    if "drones" not in st.session_state:
        st.session_state.drones = []
        st.session_state.disruption_manager = None
        st.session_state.disruption_event_log = []
    
    # Create sample drones
    if st.button("🔄 Initialize Sample Drones", key="init_drones"):
        drone_d1 = Drone(
            id="D1",
            current_position=(1, 1),
            target=(8, 8),
            route=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)],
            status="ACTIVE"
        )
        drone_d2 = Drone(
            id="D2",
            current_position=(0, 0),
            target=(9, 9),
            route=[(0, 0), (1, 1), (2, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 6), (9, 9)],
            status="ACTIVE"
        )
        drone_d3 = Drone(
            id="D3",
            current_position=(5, 0),
            target=(5, 9),
            route=[(5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9)],
            status="ACTIVE"
        )
        st.session_state.drones = [drone_d1, drone_d2, drone_d3]
        st.session_state.disruption_manager = DisruptionManager()
        st.session_state.disruption_manager.add_event("DisruptionManager initialized - monitoring 3 drones")
        st.success("✅ 3 sample drones initialized!")
        st.rerun()
            
    # Display drone status
    if st.session_state.drones:
        st.write("**Current Drone Status:**")
        drone_data = []
        for drone in st.session_state.drones:
            drone_data.append({
                "ID": drone.id,
                "Status": drone.status,
                "Current Position": drone.current_position,
                "Target": drone.target,
                "Route Length": len(drone.route)
            })
        st.dataframe(pd.DataFrame(drone_data), use_container_width=True)
    else:
        st.info("No drones initialized. Click 'Initialize Sample Drones' to start.")
    
    # No-fly zone activation
    if st.session_state.drones:
        st.write("**Activate No-Fly Zone:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            nf_row = st.number_input("Row", 0, 9, 4, key="nf_row")
        with col2:
            nf_col = st.number_input("Col", 0, 9, 7, key="nf_col")
        with col3:
            if st.button("🚫 Activate No-Fly", key="activate_nf"):
                if st.session_state.disruption_manager:
                    st.session_state.disruption_manager.trigger_no_fly(grid, nf_row, nf_col)
                    st.success(f"No-fly zone activated at ({nf_row}, {nf_col})")
                    
                    # Check and reroute affected drones
                    st.session_state.disruption_manager.check_and_reroute(st.session_state.drones, grid)
                    st.rerun()
                else:
                    st.warning("Please initialize drones first")
    
    # Force return to hub
    if st.session_state.drones:
        st.write("**Emergency Return to Hub:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            drone_id = st.selectbox("Select Drone", [d.id for d in st.session_state.drones], key="return_drone")
        with col2:
            hub_row = st.number_input("Hub Row", 0, 9, 0, key="hub_row")
            hub_col = st.number_input("Hub Col", 0, 9, 0, key="hub_col")
        with col3:
            if st.button("🏠 Force Return to Hub", key="force_return"):
                if st.session_state.disruption_manager and force_return_to_hub:
                    for drone in st.session_state.drones:
                        if drone.id == drone_id:
                            result = force_return_to_hub(drone, (hub_row, hub_col), grid)
                            st.session_state.disruption_manager.add_event(result)
                            st.info(result)
                            st.rerun()
                            break
                else:
                    st.warning("Please initialize drones first")
    
    # Display disruption event log
    if st.session_state.disruption_manager and st.session_state.disruption_manager.event_log:
        st.write("**Disruption Event Log:**")
        log_df = pd.DataFrame({"Events": st.session_state.disruption_manager.event_log})
        st.dataframe(log_df, use_container_width=True, height=200)
        
        if st.button("🗑️ Clear Event Log", key="clear_log"):
            st.session_state.disruption_manager.event_log = []
            st.session_state.disruption_manager.step_counter = 0
            st.rerun()


def render_ml_pipeline(grid: Grid):
    """Render the ML Pipeline UI section."""
    st.subheader("Module 5: ML Pipeline - Demand Forecasting & Anomaly Detection")
    
    # Check if module is available
    if predict_demand is None or detect_anomaly is None:
        st.warning("⚠️ ML Pipeline module not available. Please ensure Module 5 is properly installed.")
        return
    
    # Create tabs for different ML features
    ml_tab1, ml_tab2, ml_tab3 = st.tabs(["📈 Demand Forecasting", "⚠️ Anomaly Detection", "📊 Model Training"])
    
    with ml_tab1:
        st.write("**Predict Delivery Demand for Any Cell**")
        
        col1, col2 = st.columns(2)
        with col1:
            pred_row = st.number_input("Cell Row", 0, 9, 5, key="pred_row")
            pred_col = st.number_input("Cell Col", 0, 9, 5, key="pred_col")
            
            hour = st.slider("Hour of Day", 0, 23, 14, key="demand_hour")
            temp = st.slider("Temperature (°C)", -10, 45, 22, key="temp")
            humidity = st.slider("Humidity (%)", 0, 100, 60, key="humidity")
            
        with col2:
            weather = st.selectbox("Weather Condition", [1, 2, 3, 4], 
                                  format_func=lambda x: {1: "Clear", 2: "Cloudy", 3: "Rainy", 4: "Heavy Rain"}.get(x, "Unknown"),
                                  key="weather")
            season = st.selectbox("Season", [1, 2, 3, 4],
                                 format_func=lambda x: {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}.get(x, "Unknown"),
                                 key="season")
        
        if st.button("🔮 Predict Demand", key="predict_demand_btn"):
            try:
                # Check if model exists
                model_path = Path(APP_DIR) / "data" / "processed" / "demand_model.pkl"
                if model_path.exists():
                    demand = predict_demand(
                        hour=hour,
                        temp=temp,
                        humidity=humidity,
                        weather=weather,
                        season=season,
                        model_path=str(model_path)
                    )
                    cell = grid.get_cell(pred_row, pred_col)
                    if cell:
                        st.metric("Predicted Demand", f"{demand:.0f} units")
                        st.info(f"Cell ({pred_row}, {pred_col}) - {cell.zone} Zone\n"
                               f"• Cell Base Demand: {cell.demand:.2f}\n"
                               f"• Density Factor: {cell.density}/10000\n"
                               f"• Weighted Prediction: {demand * (cell.density/10000):.2f}")
                    else:
                        st.metric("Predicted Demand", f"{demand:.0f} units")
                else:
                    st.warning("Demand model not trained yet. Go to 'Model Training' tab to train models.")
            except Exception as e:
                st.error(f"Prediction failed: {e}")
        
        # Show demand forecast for whole grid
        if st.button("🌍 Show Full Grid Demand Forecast", key="full_forecast"):
            if get_module_5_output:
                try:
                    output = get_module_5_output(grid, simulation_step=hour)
                    forecasts = output['demand_forecast']
                    
                    # Create forecast dataframe
                    forecast_data = []
                    for cell_key, demand_val in forecasts.items():
                        forecast_data.append({"Cell": cell_key, "Forecasted Demand": demand_val})
                    
                    st.dataframe(pd.DataFrame(forecast_data).head(20), use_container_width=True)
                    st.caption(f"Showing first 20 of {len(forecasts)} cells")
                except Exception as e:
                    st.error(f"Failed to get forecast: {e}")
            else:
                st.error("Integration function not available")
    
    with ml_tab2:
        st.write("**Drone Telemetry Anomaly Detection**")
        
        col1, col2 = st.columns(2)
        with col1:
            battery_drop = st.slider("Battery Drop (%)", 0.0, 100.0, 2.0, key="battery_drop")
            speed = st.slider("Speed (m/s)", 0.0, 100.0, 10.0, key="speed")
            route_deviation = st.slider("Route Deviation (m)", 0.0, 500.0, 5.0, key="route_deviation")
        
        with col2:
            if st.button("🔍 Detect Anomaly", key="detect_anomaly_btn"):
                try:
                    model_path = Path(APP_DIR) / "data" / "processed" / "anomaly_model.pkl"
                    if model_path.exists():
                        result = detect_anomaly(
                            battery_drop=battery_drop,
                            speed=speed,
                            route_deviation=route_deviation,
                            model_path=str(model_path)
                        )
                        
                        # Display result with appropriate color
                        if result["class"] == "normal":
                            st.success(f"✅ Status: **{result['class'].upper()}**")
                        elif result["class"] == "battery_anomaly":
                            st.warning(f"⚠️ Alert: **{result['class'].replace('_', ' ').upper()}**")
                        elif result["class"] == "route_anomaly":
                            st.warning(f"⚠️ Alert: **{result['class'].replace('_', ' ').upper()}**")
                        else:
                            st.error(f"🚨 Alert: **{result['class'].replace('_', ' ').upper()}**")
                        
                        st.metric("Confidence", f"{result['confidence']:.2%}")
                        
                        # Provide recommendations
                        if result["class"] == "battery_anomaly":
                            st.info("💡 Recommendation: Land drone at nearest charging pad immediately")
                        elif result["class"] == "route_anomaly":
                            st.info("💡 Recommendation: Reroute drone or request manual intervention")
                        elif result["class"] == "sensor_spike":
                            st.info("💡 Recommendation: Verify sensor calibration, continue mission with caution")
                    else:
                        st.warning("Anomaly detection model not trained yet. Go to 'Model Training' tab to train models.")
                except Exception as e:
                    st.error(f"Detection failed: {e}")
        
        # Show anomaly alerts from integration
        if st.button("📡 Simulate Real-Time Telemetry Alerts", key="simulate_alerts"):
            if get_module_5_output:
                try:
                    output = get_module_5_output(grid, simulation_step=12)
                    alerts = output['anomaly_alerts']
                    
                    if alerts:
                        st.warning(f"🚨 {len(alerts)} Anomaly Alerts Detected!")
                        alert_data = []
                        for alert in alerts:
                            alert_data.append({
                                "Drone ID": alert['drone_id'],
                                "Anomaly Type": alert['type'].replace('_', ' ').upper(),
                                "Confidence": f"{alert['confidence']:.2%}"
                            })
                        st.dataframe(pd.DataFrame(alert_data), use_container_width=True)
                    else:
                        st.success("✅ No anomalies detected in current telemetry data")
                except Exception as e:
                    st.error(f"Failed to simulate alerts: {e}")
            else:
                st.error("Integration function not available")
    
    with ml_tab3:
        st.write("**Train and Manage ML Models**")
        
        st.info("📁 Models are saved to: `data/processed/` directory")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Train Demand Model (requires train.csv)", key="train_demand"):
                if train_demand_model:
                    with st.spinner("Training demand forecasting model..."):
                        try:
                            train_path = Path(APP_DIR) / ".." / "data" / "raw" / "train.csv"
                            model_path = Path(APP_DIR) / "data" / "processed" / "demand_model.pkl"
                            
                            os.makedirs(model_path.parent, exist_ok=True)
                            
                            if train_path.exists():
                                metrics = train_demand_model(
                                    csv_path=str(train_path),
                                    model_path=str(model_path)
                                )
                                st.success(f"✅ Demand model trained successfully!")
                                st.metric("MAE (Mean Absolute Error)", f"{metrics['mae']:.2f}")
                                st.metric("RMSE (Root Mean Square Error)", f"{metrics['rmse']:.2f}")
                                st.info(f"📁 Model saved to: {model_path}")
                            else:
                                st.error(f"❌ train.csv not found at {train_path}")
                                st.markdown("Please download from [Kaggle Bike Sharing Demand](https://www.kaggle.com/c/bike-sharing-demand/data)")
                        except Exception as e:
                            st.error(f"Training failed: {e}")
                else:
                    st.error("Train demand model function not available")
        
        with col2:
            if st.button("🔧 Generate Synthetic Telemetry", key="gen_telemetry"):
                if create_synthetic_telemetry:
                    with st.spinner("Generating synthetic telemetry data..."):
                        try:
                            telemetry_path = Path(APP_DIR) / "data" / "raw" / "synthetic_telemetry.csv"
                            os.makedirs(telemetry_path.parent, exist_ok=True)
                            
                            df = create_synthetic_telemetry(
                                output_path=str(telemetry_path),
                                n_samples=1000
                            )
                            st.success(f"✅ Generated {len(df)} synthetic telemetry samples")
                            
                            # Show distribution
                            dist_data = []
                            for cls, count in df['label'].value_counts().items():
                                dist_data.append({"Class": cls, "Count": count, "Percentage": f"{count/len(df)*100:.1f}%"})
                            st.dataframe(pd.DataFrame(dist_data), use_container_width=True)
                        except Exception as e:
                            st.error(f"Generation failed: {e}")
                else:
                    st.error("Create synthetic telemetry function not available")
        
        if st.button("🎯 Train Anomaly Detection Model", key="train_anomaly"):
            if train_anomaly_model:
                with st.spinner("Training anomaly detection model..."):
                    try:
                        telemetry_path = Path(APP_DIR) / "data" / "raw" / "synthetic_telemetry.csv"
                        model_path = Path(APP_DIR) / "data" / "processed" / "anomaly_model.pkl"
                        
                        if telemetry_path.exists():
                            metrics = train_anomaly_model(
                                csv_path=str(telemetry_path),
                                model_path=str(model_path)
                            )
                            st.success(f"✅ Anomaly detection model trained successfully!")
                            st.metric("Accuracy", f"{metrics['accuracy']*100:.2f}%")
                            
                            # Show confusion matrix
                            st.write("**Confusion Matrix:**")
                            cm = metrics['confusion_matrix']
                            cm_df = pd.DataFrame(cm, 
                                                columns=['normal', 'battery', 'route', 'sensor'],
                                                index=['normal', 'battery', 'route', 'sensor'])
                            st.dataframe(cm_df, use_container_width=True)
                        else:
                            st.warning("No synthetic telemetry found. Generate telemetry data first.")
                    except Exception as e:
                        st.error(f"Training failed: {e}")
            else:
                st.error("Train anomaly model function not available")
        
        # Model status
        st.write("**Model Status:**")
        demand_exists = (Path(APP_DIR) / "data" / "processed" / "demand_model.pkl").exists()
        anomaly_exists = (Path(APP_DIR) / "data" / "processed" / "anomaly_model.pkl").exists()
        
        col1, col2 = st.columns(2)
        with col1:
            if demand_exists:
                st.success("✅ Demand Model: Trained")
            else:
                st.warning("⚠️ Demand Model: Not Trained")
        with col2:
            if anomaly_exists:
                st.success("✅ Anomaly Model: Trained")
            else:
                st.warning("⚠️ Anomaly Model: Not Trained")


def main():
	"""Main Streamlit app."""
	st.set_page_config(page_title="AeroNet Lite - Grid Visualization", layout="wide")
	
	st.title("AeroNet Lite - Grid Visualization")
	st.markdown("Autonomous Drone Delivery Simulation System")

	if "grid_index" not in st.session_state:
		st.session_state.grid_index = 0

	controls_left, controls_right = st.columns([3, 1])

	with controls_left:
		selected_algorithm = st.selectbox(
			"Validation algorithm",
			options=list(ALGORITHM_LABELS.keys()),
			format_func=lambda name: ALGORITHM_LABELS[name],
			index=0,
		)

	with controls_right:
		st.markdown("<div style='height:1.7rem;'></div>", unsafe_allow_html=True)
		if st.button("Change Grid", use_container_width=True):
			st.session_state.grid_index = (st.session_state.grid_index + 1) % len(GRID_PRESETS)

	grid_name, grid = get_grid_preset(st.session_state.grid_index)
	
	# Get validation result safely
	try:
		solver = ALGORITHM_SOLVERS[selected_algorithm]
		result = solver(grid)
		if result is not None and hasattr(result, 'to_dict'):
			validation_result = result.to_dict()
		else:
			validation_result = {"valid": True, "errors": [], "warnings": []}
	except Exception as e:
		st.error(f"Validation error: {e}")
		validation_result = {"valid": False, "errors": [{"rule": "Error", "message": str(e)}], "warnings": []}

	st.subheader(f"Current Grid: {grid_name}")
	render_validation_summary(validation_result)
	
	# Main visualization
	st.subheader("Interactive Grid Visualization")
	fig = create_plotly_grid_visualization(grid)
	st.plotly_chart(fig, config={"responsive": True, "displayModeBar": False})
	
	# Legend section
	st.subheader("Legend")
	col1, col2 = st.columns(2)
	
	with col1:
		st.markdown("**Zone Types:**")
		render_zone_legend()
	
	with col2:
		st.markdown("**Special Markers:**")
		_, marker_legend = create_legend()
		for _, row in marker_legend.iterrows():
			st.write(f"{row['Marker']}: {row['Meaning']}")
	
	# Grid details table
	st.subheader("Grid Details")
	
	# Add filter options
	col1, col2, col3 = st.columns(3)
	
	with col1:
		selected_zone = st.multiselect(
			"Filter by Zone Type",
			options=list(ZONE_COLORS.keys()),
			default=list(ZONE_COLORS.keys()),
			key="zone_filter"
		)
	
	with col2:
		show_hubs = st.checkbox("Show Hubs Only", value=False)
	
	with col3:
		show_no_fly = st.checkbox("Show No-Fly Zones Only", value=False)
	
	# Create filtered dataframe
	df = create_grid_table(grid)
	
	if selected_zone:
		df = df[df["Zone"].isin(selected_zone)]
	
	if show_hubs:
		df = df[df["Hub"] == "✓"]
	
	if show_no_fly:
		df = df[df["No-Fly"] == "✓"]
	
	st.dataframe(df, width="stretch", hide_index=True)
	
	# Summary statistics
	st.subheader("Grid Statistics")
	
	col1, col2, col3, col4 = st.columns(4)
	
	with col1:
		hub_count = sum(1 for cell in grid.iter_cells() if cell.is_hub)
		st.metric("Total Hubs", hub_count)
	
	with col2:
		charging_count = sum(1 for cell in grid.iter_cells() if cell.is_charging)
		st.metric("Charging Pads", charging_count)
	
	with col3:
		medical_count = sum(1 for cell in grid.iter_cells() if cell.is_medical_pickup)
		st.metric("Medical Pickups", medical_count)
	
	with col4:
		no_fly_count = sum(1 for cell in grid.iter_cells() if cell.no_fly)
		st.metric("No-Fly Zones", no_fly_count)
	
	# Zone distribution
	st.subheader("Zone Distribution")
	zone_counts = {}
	for cell in grid.iter_cells():
		zone_counts[cell.zone] = zone_counts.get(cell.zone, 0) + 1
	
	zone_df = pd.DataFrame(list(zone_counts.items()), columns=["Zone", "Count"])
	
	col1, col2 = st.columns(2)
	
	with col1:
		st.plotly_chart(create_zone_distribution_figure(zone_df), config={"responsive": True, "displayModeBar": False})
	
	with col2:
		# Create a simple metric display
		for idx, row in zone_df.iterrows():
			st.write(f"**{row['Zone']}**: {row['Count']} cells")


	st.subheader("A* Path Planning")
	
	with st.expander("Plan Delivery Route", expanded=False):
		col1, col2, col3 = st.columns(3)
		
		with col1:
			hub_r = st.number_input("Hub Row", 0, 9, 0, key="hub_r")
			hub_c = st.number_input("Hub Col", 0, 9, 0, key="hub_c")
		
		with col2:
			pickup_r = st.number_input("Pickup Row", 0, 9, 1, key="pickup_r")
			pickup_c = st.number_input("Pickup Col", 0, 9, 1, key="pickup_c")
		
		with col3:
			dropoff_r = st.number_input("Dropoff Row", 0, 9, 2, key="dropoff_r")
			dropoff_c = st.number_input("Dropoff Col", 0, 9, 2, key="dropoff_c")
		
		if st.button("Compute Route"):
			hub = (hub_r, hub_c)
			pickup = (pickup_r, pickup_c)
			dropoff = (dropoff_r, dropoff_c)
			
			result = plan_delivery_route(hub, pickup, dropoff, grid)
			
			if result:
				st.success(f"Route planned successfully! Total cost: {result['total_cost']:.2f}")
				
				paths = result['segments']
				points = {"Hub": hub, "Pickup": pickup, "Dropoff": dropoff}
				
				fig_astar = create_plotly_grid_visualization(grid, paths, points)
				st.plotly_chart(fig_astar, config={"responsive": True, "displayModeBar": False})
				
				# Show path details
				for i, path in enumerate(paths):
					segment_cost = sum(grid.move_cost(r, c) for r, c in path[1:]) if len(path) > 1 else 0
					st.write(f"**Segment {i+1}**: {len(path)} steps, cost: {segment_cost:.2f}")
					st.write(f"Path: {' -> '.join([f'({r},{c})' for r, c in path])}")
			else:
				st.error("Failed to plan route. Check positions.")
	
	# ========== NEW: Module 4 and Module 5 Sections ==========
	
	# Add separator
	st.markdown("---")
	
	# Module 4: Disruption Handler
	render_disruption_handler(grid)
	
	# Add separator
	st.markdown("---")
	
	# Module 5: ML Pipeline
	render_ml_pipeline(grid)


if __name__ == "__main__":
	main()