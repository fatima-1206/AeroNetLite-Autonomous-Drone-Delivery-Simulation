"""Streamlit UI for AeroNet Lite Grid Visualization.

This module provides an interactive visualization of the 10x10 city grid
used in the autonomous drone delivery simulation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import time
from pathlib import Path
import importlib.util
from typing import List, Tuple, Dict, Optional

MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
VALIDATOR_DIR = APP_DIR / "1_csp_validator"
ASTAR_DIR = APP_DIR / "3_astar_planner"

# Add parent directory to path for imports
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(VALIDATOR_DIR))

from shared_utils.main import Grid, GridCell, manhattan
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

# Import disruption handler from Module 4 dynamically because pathname starts with a digit
DISRUPTION_DIR = APP_DIR / "4_disruption_handler"
disruption_spec = importlib.util.spec_from_file_location("disruption_handler", str(DISRUPTION_DIR / "main.py"))
disruption_module = importlib.util.module_from_spec(disruption_spec)
# Register the loaded module so dataclasses and decorators resolve correctly
sys.modules[disruption_spec.name] = disruption_module
disruption_spec.loader.exec_module(disruption_module)
Drone = disruption_module.Drone
activate_no_fly = disruption_module.activate_no_fly
route_contains_blocked_cell = disruption_module.route_contains_blocked_cell
reroute_drone = disruption_module.reroute_drone
force_return_to_hub = disruption_module.force_return_to_hub
DisruptionManager = disruption_module.DisruptionManager
create_sample_drones = disruption_module.create_sample_drones


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
	"medical_pickup": "🏥",
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
		text = "🏥"
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


def get_grid_zone_cells(grid: Grid, zone_name: str) -> list[GridCell]:
	"""Return all cells belonging to a specific zone."""
	return [cell for row in grid.cells for cell in row if cell.zone == zone_name]


def validate_csp_rules(grid: Grid) -> dict:
	"""Validate the grid against CSP-style rules and return the results."""
	results = []
	for cell in [c for row in grid.cells for c in row if c.is_hub]:
		nearby_charging = any(
			manhattan((cell.row, cell.col), (neighbor.row, neighbor.col)) <= 2 and neighbor.is_charging
			for row in grid.cells for neighbor in row
		)
		results.append({
			"rule": "Hub charging coverage",
			"passed": nearby_charging,
			"message": f"Hub at ({cell.row},{cell.col}) has charging within distance 2." if nearby_charging else f"Hub at ({cell.row},{cell.col}) has no charging station within distance 2.",
			"suggestion": "Place a charging station within Manhattan distance 2 of the hub." if not nearby_charging else "",
		})
	for cell in [c for row in grid.cells for c in row if c.is_medical_pickup]:
		adjacent_no_fly = any(
			manhattan((cell.row, cell.col), (neighbor.row, neighbor.col)) == 1 and neighbor.no_fly
			for row in grid.cells for neighbor in row
		)
		results.append({
			"rule": "Medical pickup safety",
			"passed": not adjacent_no_fly,
			"message": f"Medical pickup at ({cell.row},{cell.col}) is not next to a no-fly zone." if not adjacent_no_fly else f"Medical pickup at ({cell.row},{cell.col}) borders a no-fly zone.",
			"suggestion": "Move the no-fly zone one cell away from the medical pickup or relocate the pickup." if adjacent_no_fly else "",
		})
	for cell in [c for row in grid.cells for c in row if c.is_charging]:
		reachable_hub = any(
			manhattan((cell.row, cell.col), (neighbor.row, neighbor.col)) <= 4 and neighbor.is_hub
			for row in grid.cells for neighbor in row
		)
		results.append({
			"rule": "Charging station access",
			"passed": reachable_hub,
			"message": f"Charging at ({cell.row},{cell.col}) is within distance 4 of a hub." if reachable_hub else f"Charging at ({cell.row},{cell.col}) is not within distance 4 of any hub.",
			"suggestion": "Add a hub closer to the charging station or reposition the charger." if not reachable_hub else "",
		})
	for cell in [c for row in grid.cells for c in row if c.demand > 0]:
		nearby_service = any(
			manhattan((cell.row, cell.col), (neighbor.row, neighbor.col)) <= 3 and (neighbor.is_hub or neighbor.is_charging)
			for row in grid.cells for neighbor in row
		)
		results.append({
			"rule": "Demand service coverage",
			"passed": nearby_service,
			"message": f"Demand cell at ({cell.row},{cell.col}) has service coverage." if nearby_service else f"Demand cell at ({cell.row},{cell.col}) lacks hub/charging coverage within distance 3.",
			"suggestion": "Place a hub or charging station closer to this demand cell." if not nearby_service else "",
		})
	return {
		"summary": {
			"passed": sum(1 for r in results if r["passed"]),
			"failed": sum(1 for r in results if not r["passed"]),
			"total": len(results),
		},
		"details": results,
	}


def compute_fleet_selection(budget: int) -> dict:
	"""Compute a practical fleet mix given a budget."""
	LIGHT_COST, HEAVY_COST = 1200, 2200
	LIGHT_COVERAGE, HEAVY_COVERAGE = 18, 35
	best = {"light": 0, "heavy": 0, "cost": 0, "coverage": 0}
	for heavy in range(budget // HEAVY_COST + 1):
		remaining = budget - heavy * HEAVY_COST
		light = remaining // LIGHT_COST
		cost = heavy * HEAVY_COST + light * LIGHT_COST
		coverage = heavy * HEAVY_COVERAGE + light * LIGHT_COVERAGE
		if coverage > best["coverage"] or (coverage == best["coverage"] and cost > best["cost"]):
			best = {"light": light, "heavy": heavy, "cost": cost, "coverage": min(100, coverage)}
	return best


def create_plotly_grid_visualization(grid: Grid, paths: list[list[tuple[int, int]]] = None, points: dict = None, show_drones: bool = False, visible_zones: list[str] | None = None) -> go.Figure:
	"""Create an interactive Plotly visualization of the grid with drone positions and paths."""
	fig = go.Figure()
	
	grid_size = 10
	drone_positions = get_current_drone_positions() if show_drones else {}
	visible_zones = visible_zones if visible_zones is not None else list(ZONE_COLORS.keys())
	
	# Create the main grid visualization using rectangles
	for row_idx in range(grid_size):
		for col_idx in range(grid_size):
			cell = grid.get_cell(row_idx, col_idx)
			if cell:
				# Determine the base cell color and display options
				base_color = ZONE_COLORS.get(cell.zone, "#FFFFFF")
				is_visible_zone = cell.zone in visible_zones
				fill_color = base_color if is_visible_zone else "#F2F2F2"
				opacity = 1.0 if is_visible_zone else 0.35
				font_color = "#000000" if is_visible_zone else "#888888"
				
				# Check if this cell has a drone
				drone_here = None
				for drone_id, pos in drone_positions.items():
					if pos == (row_idx, col_idx):
						drone_here = drone_id
						fill_color = "#FF6B6B"
						opacity = 1.0
						break
				
				# Check if this cell is on a path
				is_on_path = False
				if paths:
					for path in paths:
						if (row_idx, col_idx) in path:
							is_on_path = True
							break
				
				if is_on_path and not drone_here:
					fill_color = "#4ECDC4"
					opacity = 0.65
				
				# Create cell display text
				display_text = f"({row_idx}, {col_idx})<br>{cell.zone}<br>Density: {cell.density}"
				markers = []
				if cell.is_hub:
					markers.append("★ HUB")
				if cell.is_charging:
					markers.append("⚡ CHG")
				if cell.is_medical_pickup:
					markers.append("🏥 MED")
				if cell.no_fly:
					markers.append("❌ NO-FLY")
				if markers:
					display_text += "<br>" + " | ".join(markers)
				display_text += f"<br>Demand: {cell.demand:.1f}"
				if drone_here:
					display_text += f"<br><b>🚁 {drone_here}</b>"
				
				fig.add_trace(go.Scatter(
					x=[col_idx, col_idx + 1, col_idx + 1, col_idx, col_idx],
					y=[grid_size - row_idx, grid_size - row_idx, grid_size - row_idx - 1, grid_size - row_idx - 1, grid_size - row_idx],
					fill="toself",
					fillcolor=fill_color,
					opacity=opacity,
					line=dict(color="#000000", width=1),
					hovertext=display_text,
					hoverinfo="text",
					mode="lines",
					showlegend=False,
					name="",
				))
				
				cell_label = get_cell_display_text(cell)
				if drone_here:
					cell_label = f"🚁{drone_here}"
				
				fig.add_annotation(
					x=col_idx + 0.5,
					y=grid_size - row_idx - 0.5,
					text=cell_label,
					showarrow=False,
					font=dict(size=10, color=font_color),
					xanchor="center",
					yanchor="middle",
				)
	
	# Add paths if provided (for A* visualization)
	if paths:
		path_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
		for i, path in enumerate(paths):
			if path and len(path) > 1:
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
	
	title_text = "<b>AeroNet Lite - Live Drone Simulation</b>"
	if show_drones and drone_positions:
		drone_list = ", ".join([f"{id}@({r},{c})" for id, (r, c) in drone_positions.items()])
		title_text += f"<br><sub>Active Drones: {drone_list}</sub>"
	
	fig.update_layout(
		title=title_text,
		xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, grid_size], constrain="domain"),
		yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, grid_size], scaleanchor="x", scaleratio=1),
		hovermode="closest",
		plot_bgcolor="white",
		paper_bgcolor="white",
		autosize=True,
		height=700,
		margin=dict(l=50, r=50, t=100, b=50),
	)
	
	return fig


def create_legend():
	"""Create a legend for zone types and markers."""
	legend_data = {
		"Zone Type": list(ZONE_COLORS.keys()),
		"Color": ["█ " + color for color in ZONE_COLORS.values()],
	}
	
	marker_data = {
		"Marker": ["HUB", "CHG", "🏥", "NO-FLY"],
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


def find_nearest_hub(position: tuple[int, int], grid: Grid) -> tuple[int, int] | None:
	"""Return the nearest hub coordinates from a given position."""
	nearest_hub = None
	min_distance = float("inf")
	for cell in grid.iter_cells():
		if cell.is_hub:
			distance = grid.manhattan(position, (cell.row, cell.col))
			if distance < min_distance:
				min_distance = distance
				nearest_hub = (cell.row, cell.col)
	return nearest_hub


def create_sample_drones(grid: Grid) -> list[Drone]:
	"""Create sample drones with initial routes based on current grid."""
	sample_specs = [
		("D1", (1, 1), (8, 8)),
		("D2", (0, 0), (9, 9)),
		("D3", (5, 0), (5, 9)),
	]
	drones: list[Drone] = []
	for drone_id, current_position, target in sample_specs:
		route, _, success = astar(current_position, target, grid)
		if not success:
			route = [current_position, target]
		status = "ACTIVE" if success else "DELAYED"
		drones.append(
			Drone(
				id=drone_id,
				current_position=current_position,
				target=target,
				route=route,
				status=status,
			)
		)
	return drones


def initialize_disruption_state(grid_name: str, grid: Grid) -> None:
	"""Initialize or reset disruption state for the selected grid."""
	st.session_state.disruption_grid_name = grid_name
	st.session_state.disruption_manager = DisruptionManager()
	st.session_state.disruption_drones = create_sample_drones(grid)


def render_disruption_drone_summary(drones: list[Drone], grid: Grid) -> pd.DataFrame:
	"""Return a DataFrame summarizing current drone route and status."""
	rows = []
	for drone in drones:
		rows.append({
			"Drone": drone.id,
			"Position": f"{drone.current_position}",
			"Target": f"{drone.target}",
			"Status": drone.status,
			"Route Length": len(drone.route),
			"Blocked Route": "Yes" if route_contains_blocked_cell(drone.route, grid) else "No",
		})
	return pd.DataFrame(rows)


def get_drone_paths(drones: list[Drone]) -> list[list[tuple[int, int]]]:
	"""Build a list of current drone paths for the grid visualization."""
	return [drone.route for drone in drones]


def initialize_simulation_state(grid_name: str, grid: Grid) -> None:
	"""Initialize or reset simulation state for the selected grid."""
	st.session_state.simulation_grid_name = grid_name
	st.session_state.simulation_grid = grid
	st.session_state.simulation_drones = create_sample_drones(grid)
	st.session_state.simulation_disruption_manager = DisruptionManager()
	st.session_state.simulation_animation_running = False
	st.session_state.simulation_current_step = 0
	st.session_state.simulation_drone_positions = {drone.id: drone.current_position for drone in st.session_state.simulation_drones}
	st.session_state.simulation_event_log = []
	st.session_state.zone_filter = list(ZONE_COLORS.keys())
	st.session_state.csp_result = None
	st.session_state.fleet_budget = 5000
	initialize_delivery_state(grid_name, grid)


def initialize_delivery_state(grid_name: str, grid: Grid) -> None:
	"""Initialize or reset delivery route planning state."""
	st.session_state.delivery_grid_name = grid_name
	st.session_state.delivery_route_segments = []
	st.session_state.delivery_route_points = {}
	st.session_state.delivery_route_cost = 0.0
	st.session_state.delivery_route_planned = False
	st.session_state.delivery_route_status = "Not planned"
	st.session_state.delivery_drone_position = None


def plan_and_store_delivery_route(hub: tuple[int, int], pickup: tuple[int, int], dropoff: tuple[int, int], grid: Grid) -> None:
	"""Calculate delivery segments and store them in session state."""
	result = plan_delivery_route(hub, pickup, dropoff, grid)
	if result is None:
		st.session_state.delivery_route_segments = []
		st.session_state.delivery_route_points = {}
		st.session_state.delivery_route_cost = 0.0
		st.session_state.delivery_route_planned = False
		st.session_state.delivery_route_status = "Failed to plan route"
		return

	st.session_state.delivery_route_segments = result["segments"]
	st.session_state.delivery_route_points = {"Hub": hub, "Pickup": pickup, "Dropoff": dropoff}
	st.session_state.delivery_route_cost = result["total_cost"]
	st.session_state.delivery_route_planned = True
	st.session_state.delivery_route_status = "Route planned"
	st.session_state.delivery_drone_position = hub


def flatten_route_segments(segments: list[list[tuple[int, int]]]) -> list[tuple[int, int]]:
	"""Flatten route segments into a single waypoint list without duplicate endpoints."""
	if not segments:
		return []
	flat_route = []
	for segment in segments:
		if not flat_route:
			flat_route.extend(segment)
		else:
			flat_route.extend(segment[1:])
	return flat_route


def simulate_delivery_route(grid: Grid, animation_speed: float = 0.5) -> None:
	"""Animate the planned delivery route as a separate delivery drone."""
	if not st.session_state.delivery_route_planned:
		st.warning("Please plan a delivery route first.")
		return

	route = flatten_route_segments(st.session_state.delivery_route_segments)
	if not route:
		st.warning("The delivery route is invalid or empty.")
		return

	drone_id = "DELIVERY"
	st.session_state.simulation_drone_positions[drone_id] = route[0]
	st.session_state.delivery_route_status = "Simulating"

	for i, position in enumerate(route):
		update_drone_position(drone_id, position)
		st.session_state.delivery_drone_position = position
		if i == 0:
			add_simulation_event(f"🚁 Delivery route started at {position}")
		elif i == len(route) - 1:
			add_simulation_event(f"🎯 Delivery completed at {position}")
		else:
			add_simulation_event(f"➡️ Delivery moving through {position}")
		time.sleep(animation_speed)

	st.session_state.delivery_route_status = "Completed"
	st.session_state.simulation_animation_running = False


def get_current_drone_positions() -> Dict[str, Tuple[int, int]]:
	"""Get current positions of all drones for visualization."""
	return st.session_state.get("simulation_drone_positions", {})


def update_drone_position(drone_id: str, new_position: Tuple[int, int]) -> None:
	"""Update a drone's position in the simulation state."""
	if "simulation_drone_positions" not in st.session_state:
		st.session_state.simulation_drone_positions = {}
	st.session_state.simulation_drone_positions[drone_id] = new_position


def add_simulation_event(event: str) -> None:
	"""Add an event to the simulation event log."""
	if "simulation_event_log" not in st.session_state:
		st.session_state.simulation_event_log = []
	st.session_state.simulation_event_log.append(event)
	# Keep only last 20 events
	st.session_state.simulation_event_log = st.session_state.simulation_event_log[-20:]


def animate_drone_movement(drone: Drone, grid: Grid, animation_speed: float = 0.5) -> None:
	"""Animate a drone moving along its route step by step."""
	if not drone.route or len(drone.route) <= 1:
		return

	add_simulation_event(f"🚁 Starting animation for {drone.id}: {drone.route[0]} → {drone.route[-1]}")

	for i, position in enumerate(drone.route):
		# Update drone position
		update_drone_position(drone.id, position)
		drone.current_position = position

		# Add event for each step
		if i == 0:
			add_simulation_event(f"📍 {drone.id} at start position {position}")
		elif i == len(drone.route) - 1:
			add_simulation_event(f"🎯 {drone.id} reached destination {position}")
		else:
			add_simulation_event(f"➡️ {drone.id} moving to {position}")

		# Force UI update
		time.sleep(animation_speed)

	add_simulation_event(f"✅ {drone.id} completed route")


def start_drone_animation(grid: Grid, selected_drone_ids: List[str], animation_speed: float = 0.5) -> None:
	"""Start animation for selected drones."""
	drones = st.session_state.simulation_drones

	for drone in drones:
		if drone.id in selected_drone_ids and drone.route:
			animate_drone_movement(drone, grid, animation_speed)


def handle_disruption_and_reroute(grid: Grid, row: int, col: int, selected_drone_id: str | None = None) -> None:
	"""Handle no-fly zone activation and automatic rerouting."""
	# Activate no-fly zone
	event = activate_no_fly(grid, row, col)
	add_simulation_event(f"🚫 {event}")

	# Check all drones for affected routes
	drones = st.session_state.simulation_drones
	affected_drones = []

	for drone in drones:
		if route_contains_blocked_cell(drone.route, grid):
			affected_drones.append(drone.id)
			add_simulation_event(f"⚠️ {drone.id} route affected by no-fly zone")

	# Reroute affected drones
	for drone in drones:
		if drone.id in affected_drones:
			if selected_drone_id and drone.id == selected_drone_id:
				add_simulation_event(f"🔎 Selected drone {drone.id} is impacted and will be rerouted.")
			add_simulation_event(f"🔄 Rerouting {drone.id}...")
			reroute_event = reroute_drone(drone, grid)
			add_simulation_event(f"📋 {reroute_event}")

			# Update position tracking
			update_drone_position(drone.id, drone.current_position)

	# Re-evaluate delivery route if it was planned and is impacted
	if st.session_state.delivery_route_planned:
		delivery_route = flatten_route_segments(st.session_state.delivery_route_segments)
		if route_contains_blocked_cell(delivery_route, grid):
			add_simulation_event("⚠️ Delivery route impacted by the new no-fly zone.")
			points = st.session_state.delivery_route_points
			plan_and_store_delivery_route(points["Hub"], points["Pickup"], points["Dropoff"], grid)
			if st.session_state.delivery_route_planned:
				add_simulation_event("✅ Delivery route recomputed successfully after disruption.")
			else:
				add_simulation_event("❌ Delivery route could not be recomputed after disruption.")


def get_grid_preset(index: int) -> tuple[str, Grid]:
	"""Return the selected grid preset name and a freshly built grid."""
	name, factory = GRID_PRESETS[index]
	return name, factory()


def render_validation_summary(validation_result: dict) -> None:
	"""Render the CSP validation result and any rule violations."""
	if validation_result["valid"]:
		st.success("This grid is valid for the selected CSP algorithm.")
		return

	st.error("This grid is invalid. The validator found the following issue(s):")
	for error in validation_result.get("errors", []):
		cell = error.get("cell", ("?", "?"))
		st.write(f"- {error.get('rule', 'Unknown rule')} at {cell}: {error.get('message', 'No details available')}")

	warnings = validation_result.get("warnings", [])
	if warnings:
		st.caption("Warnings: " + " | ".join(warnings))


def load_module(module_name: str, file_name: str):
	"""Load a module dynamically from the app directory."""
	try:
		if module_name.startswith("4_"):  # Handle digit-prefixed module names
			module_dir = APP_DIR / module_name
			spec = importlib.util.spec_from_file_location(module_name.replace("4_", "disruption_"), str(module_dir / f"{file_name}.py"))
		else:
			module_dir = APP_DIR / module_name
			spec = importlib.util.spec_from_file_location(module_name, str(module_dir / f"{file_name}.py"))
		
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		
		# Register the module so dataclasses and decorators work
		if module_name.startswith("4_"):
			sys.modules[module_name.replace("4_", "disruption_")] = module
		else:
			sys.modules[module_name] = module
		
		return module
	except Exception as e:
		st.error(f"Failed to load module {module_name}: {e}")
		return None


def get_drone_paths(drones: list[Drone]) -> list[list[tuple[int, int]]]:
	"""Build a list of current drone paths for the grid visualization."""
	return [drone.route for drone in drones]


def initialize_simulation_state(grid_name: str, grid: Grid) -> None:
	"""Initialize or reset simulation state for the selected grid."""
	st.session_state.simulation_grid_name = grid_name
	st.session_state.simulation_grid = grid
	st.session_state.simulation_drones = create_sample_drones(grid)
	st.session_state.simulation_disruption_manager = DisruptionManager()
	st.session_state.simulation_animation_running = False
	st.session_state.simulation_current_step = 0
	st.session_state.simulation_drone_positions = {drone.id: drone.current_position for drone in st.session_state.simulation_drones}
	st.session_state.simulation_event_log = []


def main():
	"""Main Streamlit application."""
	st.set_page_config(page_title="AeroNet Lite - Live Drone Simulation", page_icon="🚁", layout="wide")
	
	st.title("🚁 AeroNet Lite - Live Drone Simulation")
	st.markdown("Real-time autonomous drone delivery simulation with disruption handling")
	
	# Use already imported modules - no need for dynamic loading
	# All components are already imported at the top of the file
	
	# Sidebar controls
	st.sidebar.header("🎮 Simulation Controls")
	
	# Grid selection
	grid_options = ["Grid 1", "Grid 2", "Grid 3", "Grid 4", "Grid 5"]
	selected_grid = st.sidebar.selectbox("Select Grid Preset", grid_options, index=0)
	
	# Load selected grid
	grid_name, grid = get_grid_preset(grid_options.index(selected_grid))
	
	# Initialize simulation state if needed
	if "simulation_grid_name" not in st.session_state or st.session_state.simulation_grid_name != grid_name:
		initialize_simulation_state(grid_name, grid)

	# Filter visible zone types in the grid visualization
	zone_filter = st.sidebar.multiselect(
		"Show Zone Types",
		list(ZONE_COLORS.keys()),
		default=st.session_state.get("zone_filter", list(ZONE_COLORS.keys())),
		key="zone_filter",
	)
	
	# Animation controls
	st.sidebar.subheader("🎬 Animation Controls")
	animation_speed = st.sidebar.slider("Animation Speed (seconds per step)", 0.1, 2.0, 0.5, 0.1)
	selected_drones = st.sidebar.multiselect(
		"Select Drones to Animate",
		[drone.id for drone in st.session_state.simulation_drones],
		default=[drone.id for drone in st.session_state.simulation_drones][:2]  # Default to first 2 drones
	)
	
	if st.sidebar.button("▶️ Start Animation", type="primary"):
		if selected_drones:
			st.session_state.simulation_animation_running = True
			start_drone_animation(grid, selected_drones, animation_speed)
			st.session_state.simulation_animation_running = False
			st.rerun()
		else:
			st.sidebar.warning("Please select at least one drone to animate.")
	
	if st.sidebar.button("⏹️ Stop Animation"):
		st.session_state.simulation_animation_running = False
		st.sidebar.success("Animation stopped.")
	
	# Disruption controls
	st.sidebar.subheader("🚫 Disruption Controls")
	
	selected_disruption_drone = st.sidebar.selectbox(
		"Selected Drone for Disruption",
		[drone.id for drone in st.session_state.simulation_drones],
		index=0,
		key="selected_disruption_drone",
	)
	col1, col2 = st.sidebar.columns(2)
	with col1:
		disruption_row = st.number_input("Row", min_value=0, max_value=9, value=5, step=1)
	with col2:
		disruption_col = st.number_input("Column", min_value=0, max_value=9, value=5, step=1)
	
	if st.sidebar.button("🚫 Activate No-Fly Zone", type="secondary"):
		handle_disruption_and_reroute(grid, disruption_row, disruption_col, selected_disruption_drone)
		st.rerun()
	
	# Delivery route planner
	st.sidebar.subheader("🗺️ Delivery Route Planner")
	col1, col2 = st.sidebar.columns(2)
	with col1:
		hub_row = st.number_input("Hub Row", min_value=0, max_value=9, value=0, step=1, key="hub_row")
		hub_col = st.number_input("Hub Col", min_value=0, max_value=9, value=0, step=1, key="hub_col")
	with col2:
		pickup_row = st.number_input("Pickup Row", min_value=0, max_value=9, value=1, step=1, key="pickup_row")
		pickup_col = st.number_input("Pickup Col", min_value=0, max_value=9, value=1, step=1, key="pickup_col")

	col3, col4 = st.sidebar.columns(2)
	with col3:
		dropoff_row = st.number_input("Dropoff Row", min_value=0, max_value=9, value=2, step=1, key="dropoff_row")
	with col4:
		dropoff_col = st.number_input("Dropoff Col", min_value=0, max_value=9, value=2, step=1, key="dropoff_col")

	if st.sidebar.button("📍 Plan Delivery Route", use_container_width=True):
		plan_and_store_delivery_route(
			(hub_row, hub_col),
			(pickup_row, pickup_col),
			(dropoff_row, dropoff_col),
			grid,
		)
		if st.session_state.delivery_route_planned:
			st.sidebar.success(f"Route planned: cost {st.session_state.delivery_route_cost:.2f}")
		else:
			st.sidebar.error("Route planning failed. Check coordinates.")

	if st.sidebar.button("🚀 Simulate Delivery Path", use_container_width=True):
		if not st.session_state.delivery_route_planned:
			st.sidebar.warning("Plan a delivery route first.")
		else:
			st.session_state.simulation_animation_running = True
			simulate_delivery_route(grid, animation_speed)
			st.session_state.simulation_animation_running = False
			st.rerun()

	# Main content area
	col1, col2 = st.columns([3, 1])

	with col1:
		st.subheader("📊 Live Grid Visualization")
	
		# Get current drone paths for visualization
		drone_paths = get_drone_paths(st.session_state.simulation_drones)
		paths = drone_paths
		points = None
		if st.session_state.get("delivery_route_planned", False):
			paths = drone_paths + st.session_state.delivery_route_segments
			points = st.session_state.delivery_route_points
		
		# Create and display the grid visualization
		fig = create_plotly_grid_visualization(
			grid,
			paths=paths,
			points=points,
			show_drones=True,
			visible_zones=st.session_state.zone_filter,
		)
		st.plotly_chart(fig, use_container_width=True)

	with col2:
		st.subheader("📋 Simulation Status")
		
		# Drone status
		st.markdown("**🚁 Active Drones:**")
		for drone in st.session_state.simulation_drones:
			current_pos = st.session_state.simulation_drone_positions.get(drone.id, drone.current_position)
			status = "🟢 Active" if drone.route else "🔴 Idle"
			st.markdown(f"- **{drone.id}**: {status} @ {current_pos}")
		
		# Event log
		st.markdown("**📝 Recent Events:**")
		if st.session_state.simulation_event_log:
			for event in reversed(st.session_state.simulation_event_log[-10:]):  # Show last 10 events
				st.markdown(f"• {event}")
		else:
			st.markdown("*No events yet*")
		
		# Grid info
		st.markdown("**🏙️ Grid Info:**")
		st.markdown(f"- **Preset:** {grid_name}")
		st.markdown(f"- **Visible Zone Types:** {', '.join(st.session_state.zone_filter)}")
		no_fly_count = sum(1 for r in range(10) for c in range(10) if grid.get_cell(r, c) and grid.get_cell(r, c).no_fly)
		st.markdown(f"- **No-Fly Zones:** {no_fly_count}")
		hub_count = sum(1 for r in range(10) for c in range(10) if grid.get_cell(r, c) and grid.get_cell(r, c).is_hub)
		st.markdown(f"- **Hubs:** {hub_count}")

		st.markdown("**🗺️ Delivery Route Status:**")
		if st.session_state.get("delivery_route_planned", False):
			st.markdown(f"- **Status:** {st.session_state.delivery_route_status}")
			st.markdown(f"- **Route cost:** {st.session_state.delivery_route_cost:.2f}")
			st.markdown(f"- **Start:** {st.session_state.delivery_route_points.get('Hub')}")
			st.markdown(f"- **Pickup:** {st.session_state.delivery_route_points.get('Pickup')}")
			st.markdown(f"- **Dropoff:** {st.session_state.delivery_route_points.get('Dropoff')}")
			full_route = flatten_route_segments(st.session_state.delivery_route_segments)
			st.markdown(f"- **Total delivery steps:** {len(full_route)}")
			if st.session_state.get("delivery_drone_position"):
				st.markdown(f"- **Drone position:** {st.session_state.delivery_drone_position}")
		else:
			st.markdown("*No route planned yet*")

		st.markdown("**🧩 CSP Validation:**")
		if st.button("Run CSP Validation", key="run_csp_validation"):
			st.session_state.csp_result = validate_csp_rules(grid)
		
		if st.session_state.get("csp_result"):
			csp_summary = st.session_state.csp_result["summary"]
			if csp_summary["failed"] == 0:
				st.success(f"All CSP checks passed ({csp_summary['passed']}/{csp_summary['total']})")
			else:
				st.warning(f"CSP checks detected {csp_summary['failed']} issue(s) out of {csp_summary['total']}")
			for detail in st.session_state.csp_result["details"]:
				if not detail["passed"]:
					st.markdown(f"- **{detail['rule']}:** {detail['message']}  \n  _Suggestion: {detail['suggestion']}_")

		st.markdown("**🛠️ Fleet Selection:**")
		fleet_budget = st.slider(
			"Available Fleet Budget",
			1000,
			10000,
			st.session_state.get("fleet_budget", 5000),
			step=500,
			key="fleet_budget",
		)
		fleet_plan = compute_fleet_selection(fleet_budget)
		st.metric("Estimated Fleet Coverage", f"{fleet_plan['coverage']}%")
		st.metric("Fleet Cost", f"${fleet_plan['cost']}")
		st.markdown(f"- **Light drones:** {fleet_plan['light']}")
		st.markdown(f"- **Heavy drones:** {fleet_plan['heavy']}")
		if fleet_plan['coverage'] < 100:
			st.info("Add more budget to improve coverage.")

	# Auto-refresh for animation
	if st.session_state.get("simulation_animation_running", False):
		time.sleep(0.1)  # Small delay to prevent excessive reruns
		st.rerun()



if __name__ == "__main__":
	main()
