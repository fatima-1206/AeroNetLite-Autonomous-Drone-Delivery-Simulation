"""Streamlit UI for AeroNet Lite Grid Visualization.

This module provides an interactive visualization of the 10x10 city grid
used in the autonomous drone delivery simulation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path
import importlib.util

MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
VALIDATOR_DIR = APP_DIR / "1_csp_validator"
ASTAR_DIR = APP_DIR / "3_astar_planner"

# Add parent directory to path for imports
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(VALIDATOR_DIR))

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
					markers.append("🏥")
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
					markers.append("🏥")
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


def main():
	"""Main Streamlit app."""
	st.set_page_config(page_title="AeroNet Lite - Grid Visualization", layout="wide")
	
	st.title("🚁 AeroNet Lite - Grid Visualization")
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
	validation_result = ALGORITHM_SOLVERS[selected_algorithm](grid).to_dict()

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


	st.subheader("🚁 A* Path Planning")
	
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


if __name__ == "__main__":
	main()
