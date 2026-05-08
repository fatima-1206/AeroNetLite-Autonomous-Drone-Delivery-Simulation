"""Streamlit UI for AeroNet Lite Grid Visualization.

This module provides an interactive visualization of the 10x10 city grid
used in the autonomous drone delivery simulation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_utils.main import Grid, GridCell, create_sample_grid, ZoneType


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


def create_plotly_grid_visualization(grid: Grid) -> go.Figure:
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
	
	# Update layout
	fig.update_layout(
		title="<b>Sample 10x10 Region Grid</b>",
		xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, grid_size]),
		yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, grid_size]),
		hovermode="closest",
		plot_bgcolor="white",
		paper_bgcolor="white",
		width=900,
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


def main():
	"""Main Streamlit app."""
	st.set_page_config(page_title="AeroNet Lite - Grid Visualization", layout="wide")
	
	st.title("🚁 AeroNet Lite - Grid Visualization")
	st.markdown("Autonomous Drone Delivery Simulation System")
	
	# Create or load grid
	if "grid" not in st.session_state:
		st.session_state.grid = create_sample_grid()
	
	grid = st.session_state.grid
	
	# Main visualization
	st.subheader("Interactive Grid Visualization")
	fig = create_plotly_grid_visualization(grid)
	st.plotly_chart(fig, width="stretch")
	
	# Legend section
	st.subheader("Legend")
	col1, col2 = st.columns(2)
	
	with col1:
		st.markdown("**Zone Types:**")
		zone_legend, _ = create_legend()
		st.dataframe(zone_legend, width="stretch", hide_index=True)
	
	with col2:
		st.markdown("**Special Markers:**")
		_, marker_legend = create_legend()
		st.dataframe(marker_legend, width="stretch", hide_index=True)
	
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
		st.bar_chart(zone_df.set_index("Zone"))
	
	with col2:
		# Create a simple metric display
		for idx, row in zone_df.iterrows():
			st.write(f"**{row['Zone']}**: {row['Count']} cells")


if __name__ == "__main__":
	main()
