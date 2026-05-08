"""Smoke tests for the CSP validator module."""

from __future__ import annotations

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
ROOT_DIR = APP_DIR.parent
for path in (str(ROOT_DIR), str(APP_DIR)):
	if path not in sys.path:
		sys.path.insert(0, path)

from shared_utils.main import GridCell, create_sample_grid

from main import check_all_constraints


def _with_cell(grid, row, col, **changes):
	updated = grid.copy()
	updated.update_cell(row, col, **changes)
	return updated


def test_valid_sample_grid() -> None:
	grid = create_sample_grid()
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is True
	assert result["errors"] == []


def test_r1_violation() -> None:
	grid = create_sample_grid()
	grid = _with_cell(grid, 2, 4, zone="Industrial")
	grid = _with_cell(grid, 2, 5, zone="School")
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is False
	assert any(error["rule"] == "R1" for error in result["errors"])


def test_r2_violation() -> None:
	grid = create_sample_grid()
	for row in range(10):
		for col in range(10):
			if grid.cells[row][col].is_hub:
				grid.update_cell(row, col, is_hub=False)
	result = check_all_constraints(grid, method="arc_consistency")
	assert result["valid"] is False
	assert any(error["rule"] == "R2" for error in result["errors"])


def test_r3_violation() -> None:
	grid = create_sample_grid()
	for row in range(10):
		for col in range(10):
			if grid.cells[row][col].is_charging:
				grid.update_cell(row, col, is_charging=False)
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is False
	assert any(error["rule"] == "R3" for error in result["errors"])


def test_r4_violation() -> None:
	grid = create_sample_grid()
	for row in range(10):
		for col in range(10):
			if grid.cells[row][col].is_medical_pickup:
				grid.update_cell(row, col, is_medical_pickup=False)
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is False
	assert any(error["rule"] == "R4" for error in result["errors"])


def test_method_switching() -> None:
	grid = create_sample_grid()
	results = {
		method: check_all_constraints(grid, method=method)
		for method in ("backtracking", "forward_checking", "arc_consistency")
	}
	assert all(result["valid"] for result in results.values())
	assert {result["method"] for result in results.values()} == {"backtracking", "forward_checking", "arc_consistency"}


def run_all_tests() -> None:
	test_valid_sample_grid()
	test_r1_violation()
	test_r2_violation()
	test_r3_violation()
	test_r4_violation()
	test_method_switching()
	print("csp_validator tests passed")


if __name__ == "__main__":
	run_all_tests()