"""Smoke tests for the fleet selector module."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

try:
	from .main import DRONE_TYPES, FleetSelection, brute_force_select_fleet, estimate_total_demand, select_fleet
except ImportError:  # pragma: no cover - allows direct execution
	from main import DRONE_TYPES, FleetSelection, brute_force_select_fleet, estimate_total_demand, select_fleet

from app_.shared_utils.main import create_sample_grid


def test_demand_estimation() -> None:
	grid = create_sample_grid()
	assert estimate_total_demand(grid) > 0


def test_ga_returns_valid_selection() -> None:
	selection = select_fleet(budget=10_000, random_seed=7)
	assert isinstance(selection, FleetSelection)
	assert selection.total_cost <= 10_000
	assert selection.light_drones >= 0
	assert selection.heavy_drones >= 0
	assert 0.0 <= selection.coverage_percentage <= 100.0
	assert -25.0 <= selection.score <= 100.0


def test_ga_is_deterministic_with_seed() -> None:
	first = select_fleet(budget=10_000, random_seed=11)
	second = select_fleet(budget=10_000, random_seed=11)
	assert first == second


def test_brute_force_selection() -> None:
	grid = create_sample_grid()
	demand_kg = estimate_total_demand(grid)
	selection = brute_force_select_fleet(budget=10_000, demand_kg=demand_kg)
	assert isinstance(selection, FleetSelection)
	assert selection.total_cost <= 10_000
	assert selection.score >= 0.0


def test_ga_default_method_is_kept() -> None:
	selection = select_fleet(budget=10_000, random_seed=5)
	assert isinstance(selection, FleetSelection)
	assert selection.total_cost <= 10_000
	assert selection == select_fleet(budget=10_000, random_seed=5, method="ga")


def test_method_switch_works() -> None:
	ga_selection = select_fleet(budget=10_000, random_seed=5, method="ga")
	brute_force_selection = select_fleet(budget=10_000, method="bf")
	assert isinstance(ga_selection, FleetSelection)
	assert isinstance(brute_force_selection, FleetSelection)
	assert brute_force_selection.total_cost <= 10_000


def test_drone_types_defined() -> None:
	assert len(DRONE_TYPES) == 2
	assert DRONE_TYPES[0].name == "Light Drone"
	assert DRONE_TYPES[1].name == "Heavy Drone"


def run_all_tests() -> None:
	test_demand_estimation()
	test_ga_returns_valid_selection()
	test_ga_is_deterministic_with_seed()
	test_brute_force_selection()
	test_ga_default_method_is_kept()
	test_drone_types_defined()
	print("fleet_selector tests passed")


if __name__ == "__main__":
	run_all_tests()