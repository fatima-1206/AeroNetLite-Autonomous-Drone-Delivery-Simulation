"""Fleet Selector UI components for Module 2.

Provides visualization and interaction for drone fleet selection using
genetic algorithm or brute force optimization.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional
import sys
import importlib.util
from pathlib import Path

from app_.shared_utils.main import Grid


def display_fleet_selection_summary(fleet_result: dict) -> None:
	"""
	Display fleet selection results in a clear summary format.
	
	Args:
		fleet_result: dict with fleet selection details (from select_fleet)
	"""
	col1, col2, col3, col4 = st.columns(4)
	
	with col1:
		st.metric("Light Drones", int(fleet_result.get("light_drones", 0)))
	
	with col2:
		st.metric("Heavy Drones", int(fleet_result.get("heavy_drones", 0)))
	
	with col3:
		st.metric("Total Cost", f"${int(fleet_result.get('total_cost', 0)):,}")
	
	with col4:
		st.metric("Coverage", f"{fleet_result.get('coverage_percentage', 0):.1f}%")
	
	# Additional details
	st.write("**Fleet Details:**")
	details_col1, details_col2 = st.columns(2)
	
	with details_col1:
		st.write(f"• Total Payload: {fleet_result.get('total_payload_kg', 0):.1f} kg")
		st.write(f"• Demand: {fleet_result.get('demand_kg', 0):.1f} kg")
	
	with details_col2:
		st.write(f"• Budget Used: {fleet_result.get('budget_used_percentage', 0):.1f}%")
		st.write(f"• Optimization Score: {fleet_result.get('score', 0):.2f}")


def create_fleet_comparison_chart(fleets_to_compare: list[dict]) -> go.Figure:
	"""
	Create a comparison chart for multiple fleet configurations.
	
	Args:
		fleets_to_compare: list of fleet result dicts
	
	Returns:
		Plotly figure with fleet comparison
	"""
	fig = go.Figure()
	
	fleet_names = [f"Fleet {i+1}" for i in range(len(fleets_to_compare))]
	
	light_counts = [f.get("light_drones", 0) for f in fleets_to_compare]
	heavy_counts = [f.get("heavy_drones", 0) for f in fleets_to_compare]
	costs = [f.get("total_cost", 0) for f in fleets_to_compare]
	coverage = [f.get("coverage_percentage", 0) for f in fleets_to_compare]
	
	# Add traces
	fig.add_trace(go.Bar(
		x=fleet_names,
		y=light_counts,
		name="Light Drones",
		marker_color="lightblue",
	))
	
	fig.add_trace(go.Bar(
		x=fleet_names,
		y=heavy_counts,
		name="Heavy Drones",
		marker_color="darkblue",
	))
	
	fig.update_layout(
		title="Fleet Composition Comparison",
		barmode="stack",
		xaxis_title="Fleet Configuration",
		yaxis_title="Number of Drones",
		hovermode="x unified",
		height=400,
	)
	
	return fig


def render_fleet_selector_ui(grid: Grid) -> None:
	"""
	Main Fleet Selector UI component.
	
	Provides controls for fleet optimization using Module 2 (Fleet Selector).
	
	Args:
		grid: 10x10 Grid object from shared_utils
	"""
	st.subheader("Module 2: Fleet Selector - Optimize Drone Fleet")
	
	# Import fleet selector functions (using importlib for digit-prefixed module)
	select_fleet = None
	estimate_total_demand = None
	evaluate_fleet = None
	LIGHT_DRONE = None
	HEAVY_DRONE = None
	
	try:
		FLEET_DIR = Path(__file__).resolve().parent.parent / "2_fleet_selector"
		fleet_spec = importlib.util.spec_from_file_location("fleet_selector", str(FLEET_DIR / "main.py"))
		if fleet_spec:
			fleet_module = importlib.util.module_from_spec(fleet_spec)
			fleet_spec.loader.exec_module(fleet_module)
			select_fleet = fleet_module.select_fleet
			estimate_total_demand = fleet_module.estimate_total_demand
			evaluate_fleet = fleet_module.evaluate_fleet
			LIGHT_DRONE = fleet_module.LIGHT_DRONE
			HEAVY_DRONE = fleet_module.HEAVY_DRONE
	except Exception as e:
		st.error(f"Fleet Selector module not available: {e}")
		return
	
	if select_fleet is None:
		st.error("Fleet Selector module not available")
		return
	
	# Sidebar controls
	st.write("**Fleet Optimization Parameters:**")
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		budget = st.number_input(
			"Budget ($)",
			min_value=1000,
			max_value=100000,
			value=10000,
			step=1000,
			key="fleet_budget"
		)
	
	with col2:
		method = st.radio(
			"Optimization Method",
			options=["ga", "bf"],
			format_func=lambda x: "Genetic Algorithm" if x == "ga" else "Brute Force",
			key="fleet_method",
			horizontal=True
		)
	
	with col3:
		random_seed = st.number_input(
			"Random Seed",
			min_value=0,
			max_value=1000,
			value=42,
			key="fleet_seed"
		)
	
	# Genetic Algorithm parameters (if GA selected)
	if method == "ga":
		st.write("**Genetic Algorithm Settings:**")
		ga_col1, ga_col2, ga_col3 = st.columns(3)
		
		with ga_col1:
			pop_size = st.slider(
				"Population Size",
				min_value=10,
				max_value=100,
				value=30,
				key="fleet_pop_size"
			)
		
		with ga_col2:
			generations = st.slider(
				"Generations",
				min_value=10,
				max_value=100,
				value=40,
				key="fleet_generations"
			)
		
		with ga_col3:
			mutation_rate = st.slider(
				"Mutation Rate",
				min_value=0.0,
				max_value=1.0,
				value=0.2,
				key="fleet_mutation"
			)
	else:
		pop_size = 30
		generations = 40
		mutation_rate = 0.2
	
	# Estimate current demand
	try:
		estimated_demand = estimate_total_demand(grid)
		st.info(f"📊 Estimated Total Demand: {estimated_demand:.2f} kg")
	except Exception as e:
		st.warning(f"Could not estimate demand: {e}")
		estimated_demand = 0.0
	
	# Run optimization
	if st.button("🚀 Optimize Fleet", key="optimize_fleet_btn"):
		with st.spinner("Optimizing fleet configuration..."):
			try:
				fleet_result = select_fleet(
					grid=grid,
					budget=budget,
					population_size=pop_size,
					generations=generations,
					mutation_rate=mutation_rate,
					random_seed=random_seed,
					method=method,
				)
				
				# Display result
				st.success(f"✅ Fleet optimized using {method.upper() if method == 'bf' else 'GA'}!")
				display_fleet_selection_summary(fleet_result.to_dict())
				
				# Store in session for comparison
				if "fleet_results" not in st.session_state:
					st.session_state.fleet_results = []
				st.session_state.fleet_results.append(fleet_result.to_dict())
				
			except Exception as e:
				st.error(f"Fleet optimization failed: {e}")
	
	# Display drone specifications
	st.write("**Drone Specifications:**")
	drone_specs = [
		{
			"Type": LIGHT_DRONE.name,
			"Cost": f"${LIGHT_DRONE.cost:,}",
			"Payload": f"{LIGHT_DRONE.payload_kg} kg",
			"Max Range": f"{LIGHT_DRONE.max_range_cells} cells",
		},
		{
			"Type": HEAVY_DRONE.name,
			"Cost": f"${HEAVY_DRONE.cost:,}",
			"Payload": f"{HEAVY_DRONE.payload_kg} kg",
			"Max Range": f"{HEAVY_DRONE.max_range_cells} cells",
		},
	]
	st.dataframe(pd.DataFrame(drone_specs), use_container_width=True, hide_index=True)
	
	# Manual evaluation
	st.write("**Manual Fleet Evaluation:**")
	
	eval_col1, eval_col2, eval_col3 = st.columns(3)
	
	with eval_col1:
		manual_light = st.number_input(
			"Light Drones (Manual)",
			min_value=0,
			max_value=50,
			value=5,
			key="manual_light"
		)
	
	with eval_col2:
		manual_heavy = st.number_input(
			"Heavy Drones (Manual)",
			min_value=0,
			max_value=50,
			value=2,
			key="manual_heavy"
		)
	
	with eval_col3:
		st.write("")  # Spacer
		if st.button("📋 Evaluate Configuration", key="eval_fleet_btn"):
			try:
				eval_result = evaluate_fleet(
					manual_light,
					manual_heavy,
					budget=budget,
					demand_kg=estimated_demand,
				)
				st.success("✅ Configuration evaluated!")
				display_fleet_selection_summary(eval_result.to_dict())
			except Exception as e:
				st.error(f"Evaluation failed: {e}")
	
	# Compare fleets if multiple results
	if hasattr(st.session_state, "fleet_results") and len(st.session_state.fleet_results) > 1:
		st.write("**Fleet Comparison:**")
		
		if st.button("📊 Show Comparison Chart", key="show_comparison"):
			fig = create_fleet_comparison_chart(st.session_state.fleet_results)
			st.plotly_chart(fig, use_container_width=True)
		
		# Show results table
		comparison_df = pd.DataFrame(st.session_state.fleet_results)
		st.dataframe(comparison_df, use_container_width=True)
		
		if st.button("🗑️ Clear Results", key="clear_results"):
			st.session_state.fleet_results = []
			st.rerun()
