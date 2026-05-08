"""Shared grid model and helpers for AeroNet Lite.

This module is the source of truth for the 10x10 simulation grid used by all
other modules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Iterable, Literal, Sequence


GRID_SIZE = 10
ZoneType = Literal["Residential", "Industrial", "Hospital", "School", "Commercial", "Open Field"]


@dataclass(slots=True)
class GridCell:
	row: int
	col: int
	zone: ZoneType
	density: int
	is_hub: bool = False
	is_charging: bool = False
	is_medical_pickup: bool = False
	no_fly: bool = False
	demand: float = 0.0

	def to_dict(self) -> dict:
		return asdict(self)


@dataclass(slots=True)
class Grid:
	cells: list[list[GridCell]]

	def __post_init__(self) -> None:
		if len(self.cells) != GRID_SIZE:
			raise ValueError(f"Grid must have exactly {GRID_SIZE} rows")
		for row_index, row in enumerate(self.cells):
			if len(row) != GRID_SIZE:
				raise ValueError(f"Grid row {row_index} must have exactly {GRID_SIZE} cells")
			for col_index, cell in enumerate(row):
				if cell.row != row_index or cell.col != col_index:
					raise ValueError("GridCell coordinates must match their position in the grid")

	def get_cell(self, row: int, col: int) -> GridCell | None:
		if not is_within_bounds(row, col):
			return None
		return self.cells[row][col]

	def get_neighbors(self, row: int, col: int) -> list[GridCell]:
		return get_neighbors(self.cells, row, col)

	def manhattan(self, a: tuple[int, int], b: tuple[int, int]) -> int:
		return manhattan(a, b)

	def copy(self) -> Grid:
		return Grid([[replace(cell) for cell in row] for row in self.cells])

	def update_cell(self, row: int, col: int, **changes) -> GridCell:
		cell = self.get_cell(row, col)
		if cell is None:
			raise IndexError("Grid coordinates are out of bounds")
		updated = replace(cell, **changes)
		self.cells[row][col] = updated
		return updated

	def iter_cells(self) -> Iterable[GridCell]:
		for row in self.cells:
			yield from row


def is_within_bounds(row: int, col: int) -> bool:
	return 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
	return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(cells: Sequence[Sequence[GridCell]], row: int, col: int) -> list[GridCell]:
	neighbors: list[GridCell] = []
	for next_row, next_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
		if is_within_bounds(next_row, next_col):
			neighbors.append(cells[next_row][next_col])
	return neighbors


def _build_base_zone_layout() -> list[list[ZoneType]]:
	return [
		["Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "School", "School", "Open Field", "Open Field"],
		["Residential", "Residential", "Commercial", "Open Field", "Open Field", "Open Field", "School", "Open Field", "Open Field", "Open Field"],
		["Residential", "Commercial", "Commercial", "Open Field", "Industrial", "Open Field", "Open Field", "Open Field", "Industrial", "Industrial"],
		["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Industrial", "Industrial"],
		["Hospital", "Hospital", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
		["Hospital", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Open Field", "Commercial", "Open Field", "Open Field"],
		["Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "School"],
		["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Open Field", "Open Field", "School"],
		["Industrial", "Industrial", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
		["Industrial", "Industrial", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Hospital", "Hospital", "Open Field"],
	]


def create_sample_grid() -> Grid:
	zone_layout = _build_base_zone_layout()
	hub_positions = {(1, 3), (2, 1), (5, 6)}
	charging_positions = {(2, 3), (2, 4), (5, 7), (6, 1)}
	medical_pickup_positions = {(4, 0), (5, 0), (9, 7)}
	no_fly_positions = {(3, 6)}

	cells: list[list[GridCell]] = []
	for row_index in range(GRID_SIZE):
		row: list[GridCell] = []
		for col_index in range(GRID_SIZE):
			zone = zone_layout[row_index][col_index]
			density = _default_density(zone, row_index, col_index)
			demand = _default_demand(zone, density)
			row.append(
				GridCell(
					row=row_index,
					col=col_index,
					zone=zone,
					density=density,
					is_hub=(row_index, col_index) in hub_positions,
					is_charging=(row_index, col_index) in charging_positions,
					is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
					no_fly=(row_index, col_index) in no_fly_positions,
					demand=demand,
				)
			)
		cells.append(row)
	return Grid(cells)


def _default_density(zone: ZoneType, row: int, col: int) -> int:
	base_density = {
		"Residential": 6200,
		"Commercial": 5400,
		"Hospital": 4600,
		"School": 4200,
		"Industrial": 3100,
		"Open Field": 1800,
	}[zone]
	return base_density + (row * 40) + (col * 15)


def _default_demand(zone: ZoneType, density: int) -> float:
	zone_factor = {
		"Residential": 1.0,
		"Commercial": 0.9,
		"Hospital": 1.2,
		"School": 0.7,
		"Industrial": 0.5,
		"Open Field": 0.2,
	}[zone]
	return round((density / 1000.0) * zone_factor, 2)


def grid_to_dict(grid: Grid) -> list[list[dict]]:
	return [[cell.to_dict() for cell in row] for row in grid.cells]


# Import and expose all predefined grids from grid_defs
try:
	from .grid_defs import (
		create_valid_sample_grid,
		create_valid_compact_grid,
		create_grid_r1_violation,
		create_grid_r2_violation,
		create_grid_r3_violation,
		create_grid_r4_violation,
		create_grid_multi_violation,
	)
except ImportError:  # pragma: no cover
	pass
