"""Predefined grid definitions for CSP validator testing.

This module contains several grid configurations for testing:
- Valid grids that pass all constraints
- Invalid grids that violate specific rules
"""

from __future__ import annotations

try:
    from .main import Grid, GridCell
except ImportError:  # pragma: no cover
    from pathlib import Path
    import sys

    MODULE_DIR = Path(__file__).resolve().parent
    APP_DIR = MODULE_DIR.parent
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    from main import Grid, GridCell


def create_valid_sample_grid() -> Grid:
    """Sample grid from problem statement - all rules satisfied."""
    zone_layout = [
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
    
    hub_positions = {(1, 3), (2, 1), (5, 6)}
    charging_positions = {(2, 3), (2, 4), (5, 7), (6, 1)}
    medical_pickup_positions = {(4, 0), (5, 0), (9, 7)}
    no_fly_positions = {(3, 6)}

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)


def create_grid_r1_violation() -> Grid:
    """Grid with Industrial adjacent to Hospital."""
    zone_layout = [
        ["Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "School", "School", "Open Field", "Open Field"],
        ["Residential", "Residential", "Commercial", "Open Field", "Open Field", "Open Field", "School", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Industrial", "Hospital", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
        ["Industrial", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Open Field", "Commercial", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "School"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Open Field", "Open Field", "School"],
        ["Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Hospital", "Hospital", "Open Field"],
    ]
    
    hub_positions = {(1, 3), (2, 1), (5, 6)}
    charging_positions = {(2, 3), (2, 4), (5, 7), (6, 1)}
    medical_pickup_positions = {(4, 1), (5, 0), (9, 7)}
    no_fly_positions = set()

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)


def create_grid_r2_violation() -> Grid:
    """Grid with Residential too far from all hubs."""
    zone_layout = [
        ["Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Residential", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Hospital", "Hospital", "Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
        ["Hospital", "Open Field", "Open Field", "Open Field", "Open Field", "Commercial", "Open Field", "Commercial", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Residential"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential"],
        ["Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Hospital", "Hospital", "Open Field"],
    ]
    
    hub_positions = {(1, 3)}
    charging_positions = {(2, 3), (2, 4), (5, 7), (6, 1)}
    medical_pickup_positions = {(4, 0), (5, 0), (9, 7)}
    no_fly_positions = set()

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)


def create_grid_r3_violation() -> Grid:
    """Grid with Hub too far from all charging pads."""
    zone_layout = [
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
    
    hub_positions = {(1, 3), (2, 1), (5, 6)}
    charging_positions = {(9, 7), (9, 8)}
    medical_pickup_positions = {(4, 0), (5, 0), (9, 7)}
    no_fly_positions = {(3, 6)}

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)


def create_grid_r4_violation() -> Grid:
    """Grid with Hospital too far from medical pickups."""
    zone_layout = [
        ["Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "School", "School", "Open Field", "Open Field"],
        ["Residential", "Residential", "Commercial", "Open Field", "Open Field", "Open Field", "School", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Commercial", "Commercial", "Open Field", "Industrial", "Open Field", "Open Field", "Open Field", "Industrial", "Industrial"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Industrial", "Industrial"],
        ["Hospital", "Hospital", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
        ["Hospital", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Open Field", "Commercial", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "School"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Open Field", "Open Field", "School"],
        ["Industrial", "Industrial", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Industrial", "Industrial", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
    ]
    
    hub_positions = {(1, 3), (2, 1), (5, 6)}
    charging_positions = {(2, 3), (2, 4), (5, 7), (6, 1)}
    medical_pickup_positions = {(0, 0)}
    no_fly_positions = {(3, 6)}

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)


def create_valid_compact_grid() -> Grid:
    """Compact valid grid with all rules satisfied."""
    zone_layout = [
        ["Residential", "Residential", "Residential", "Residential", "Open Field", "Hospital", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Residential", "Residential", "Residential", "Open Field", "Hospital", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Residential", "Residential", "Residential", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Commercial", "Commercial", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Residential", "Residential", "Residential", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Residential", "Residential", "Residential", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Residential", "Residential", "Residential", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Hospital", "Hospital", "Open Field", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Hospital", "Hospital", "Open Field", "Open Field", "Open Field"],
    ]
    
    hub_positions = {(1, 2), (4, 1), (6, 5), (7, 2)}
    charging_positions = {(0, 2), (2, 2), (4, 2), (5, 1), (5, 5), (5, 6), (7, 2), (6, 2)}
    medical_pickup_positions = {(0, 4), (1, 4), (5, 5), (8, 5), (9, 5)}
    no_fly_positions = set()

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)


def create_grid_multi_violation() -> Grid:
    """Grid with multiple violations."""
    zone_layout = [
        ["Industrial", "Industrial", "Commercial", "Commercial", "Open Field", "Open Field", "School", "School", "Open Field", "Open Field"],
        ["Industrial", "Industrial", "Commercial", "Open Field", "Open Field", "Open Field", "School", "Open Field", "Open Field", "Open Field"],
        ["Residential", "Commercial", "Commercial", "Open Field", "Industrial", "Open Field", "Open Field", "Open Field", "Industrial", "Industrial"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field", "Industrial", "Industrial"],
        ["Hospital", "Hospital", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field"],
        ["Hospital", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Open Field", "Commercial", "Open Field", "Open Field"],
        ["Open Field", "Open Field", "Open Field", "Open Field", "Residential", "Residential", "Commercial", "Commercial", "Open Field", "School"],
        ["Residential", "Residential", "Residential", "Open Field", "Open Field", "Residential", "Residential", "Open Field", "Open Field", "School"],
        ["Industrial", "Industrial", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Open Field", "Open Field", "Open Field"],
        ["Industrial", "Industrial", "Open Field", "Commercial", "Commercial", "Open Field", "Open Field", "Hospital", "Hospital", "Open Field"],
    ]
    
    hub_positions = {(1, 3)}
    charging_positions = set()
    medical_pickup_positions = {(4, 0), (5, 0), (9, 7)}
    no_fly_positions = set()

    cells = []
    for row_index in range(10):
        row = []
        for col_index in range(10):
            zone = zone_layout[row_index][col_index]
            cell = GridCell(
                row=row_index,
                col=col_index,
                zone=zone,
                density=5000 + row_index * 50 + col_index * 30,
                is_hub=(row_index, col_index) in hub_positions,
                is_charging=(row_index, col_index) in charging_positions,
                is_medical_pickup=(row_index, col_index) in medical_pickup_positions,
                no_fly=(row_index, col_index) in no_fly_positions,
                demand=2.5,
            )
            row.append(cell)
        cells.append(row)
    
    return Grid(cells)
