"""smoke tests for the csp validator module that check all the constraint satisfaction problem logic."""

from __future__ import annotations

from pathlib import Path
import sys

# figure out where we are in the directory structure so we can import stuff correctly
# we go up from the current test file to find the app and root directories
MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
ROOT_DIR = APP_DIR.parent
# add these directories to python's import path so we can import from sibling modules
for path in (str(ROOT_DIR), str(APP_DIR)):
	if path not in sys.path:
		sys.path.insert(0, path)
# import the grid utilities from shared_utils to work with grid structures
from shared_utils.main import GridCell, create_sample_grid

# import the main constraint checking function that we're testing
from main import check_all_constraints


# helper function to make it easier to create modified versions of a grid
# we copy the grid and then update a specific cell with the changes we pass in
def _with_cell(grid, row, col, **changes):
	updated = grid.copy()
	updated.update_cell(row, col, **changes)
	return updated


# test that a properly created sample grid passes all constraint checks
# we use backtracking method here to verify the solution is valid
def test_valid_sample_grid() -> None:
	grid = create_sample_grid()
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is True
	assert result["errors"] == []


# test that constraint r1 (probably about industrial and school zone separation) actually gets caught
# we create a violation by placing industrial and school zones adjacent to each other
# then verify the constraint checker catches it using forward checking method
def test_r1_violation() -> None:
	grid = create_sample_grid()
	grid = _with_cell(grid, 2, 4, zone="Industrial")
	grid = _with_cell(grid, 2, 5, zone="School")
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is False
	assert any(error["rule"] == "R1" for error in result["errors"])


# test that constraint r2 (likely checking that we have enough hubs) gets detected
# we remove all hub locations from the grid to intentionally violate the constraint
# then check that the constraint checker catches this problem using arc consistency
def test_r2_violation() -> None:
	grid = create_sample_grid()
	for row in range(10):
		for col in range(10):
			if grid.cells[row][col].is_hub:
				grid.update_cell(row, col, is_hub=False)
	result = check_all_constraints(grid, method="arc_consistency")
	assert result["valid"] is False
	assert any(error["rule"] == "R2" for error in result["errors"])


# test that constraint r3 (checking charging stations exist) is properly enforced
# we disable all charging stations in the grid to create a violation
# then verify backtracking method catches it
def test_r3_violation() -> None:
	grid = create_sample_grid()
	for row in range(10):
		for col in range(10):
			if grid.cells[row][col].is_charging:
				grid.update_cell(row, col, is_charging=False)
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is False
	assert any(error["rule"] == "R3" for error in result["errors"])


# test that constraint r4 (likely checking for medical pickup points) is caught
# we remove all medical pickup locations to create an invalid configuration
# then verify forward checking method detects this violation
def test_r4_violation() -> None:
	grid = create_sample_grid()
	for row in range(10):
		for col in range(10):
			if grid.cells[row][col].is_medical_pickup:
				grid.update_cell(row, col, is_medical_pickup=False)
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is False
	assert any(error["rule"] == "R4" for error in result["errors"])


# test that all three different solving methods work and produce consistent results
# we check the same valid grid with backtracking, forward checking, and arc consistency
# all three should return valid=true, proving they all work correctly
def test_method_switching() -> None:
	grid = create_sample_grid()
	results = {
		method: check_all_constraints(grid, method=method)
		for method in ("backtracking", "forward_checking", "arc_consistency")
	}
	assert all(result["valid"] for result in results.values())
	assert {result["method"] for result in results.values()} == {"backtracking", "forward_checking", "arc_consistency"}


# main test runner that executes all the tests in sequence
# if any assertion fails the script will stop and show us what went wrong
# if all pass we get a nice success message at the end
def run_all_tests() -> None:
	test_valid_sample_grid()
	test_r1_violation()
	test_r2_violation()
	test_r3_violation()
	test_r4_violation()
	test_method_switching()
	print("csp_validator tests passed")


# only run tests if this file is executed directly, not if it's imported elsewhere
if __name__ == "__main__":
	run_all_tests()