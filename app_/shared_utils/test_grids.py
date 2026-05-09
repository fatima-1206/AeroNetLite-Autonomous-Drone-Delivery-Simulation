
from __future__ import annotations

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
ROOT_DIR = APP_DIR.parent
for path in (str(ROOT_DIR), str(APP_DIR)):
	if path not in sys.path:
		sys.path.insert(0, path)

sys.path.insert(0, str(APP_DIR / "1_csp_validator"))

from shared_utils.grid_defs import (
	create_valid_sample_grid,
	create_valid_compact_grid,
	create_grid_r1_violation,
	create_grid_r2_violation,
	create_grid_r3_violation,
	create_grid_r4_violation,
	create_grid_multi_violation,
)

from main import check_all_constraints


def test_valid_sample_grid() -> None:
	"""Test the sample grid from problem statement - should be valid."""
	grid = create_valid_sample_grid()
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is True, f"Sample grid should be valid. Errors: {result['errors']}"
	assert len(result["errors"]) == 0, f"No errors expected but got {len(result['errors'])}"
	print("✓ Valid Sample Grid: PASSED")


def test_valid_compact_grid() -> None:
	"""Test compact valid grid - should be valid."""
	grid = create_valid_compact_grid()
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is True, f"Compact grid should be valid. Errors: {result['errors']}"
	print("✓ Valid Compact Grid: PASSED")


def test_r1_violation() -> None:
	"""Test grid with R1 violation (Industrial adjacent to Hospital)."""
	grid = create_grid_r1_violation()
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is False, "Should detect R1 violation"
	assert any(error["rule"] == "R1" for error in result["errors"]), "Expected R1 error"
	print(f"✓ R1 Violation: PASSED (found {len(result['errors'])} error(s))")


def test_r2_violation() -> None:
	"""Test grid with R2 violation (Residential too far from Hubs)."""
	grid = create_grid_r2_violation()
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is False, "Should detect R2 violation"
	assert any(error["rule"] == "R2" for error in result["errors"]), "Expected R2 error"
	print(f"✓ R2 Violation: PASSED (found {len(result['errors'])} error(s))")


def test_r3_violation() -> None:
	"""Test grid with R3 violation (Hub too far from Charging)."""
	grid = create_grid_r3_violation()
	result = check_all_constraints(grid, method="arc_consistency")
	assert result["valid"] is False, "Should detect R3 violation"
	assert any(error["rule"] == "R3" for error in result["errors"]), "Expected R3 error"
	print(f"✓ R3 Violation: PASSED (found {len(result['errors'])} error(s))")


def test_r4_violation() -> None:
	"""Test grid with R4 violation (Hospital far from Medical pickup)."""
	grid = create_grid_r4_violation()
	result = check_all_constraints(grid, method="backtracking")
	assert result["valid"] is False, "Should detect R4 violation"
	assert any(error["rule"] == "R4" for error in result["errors"]), "Expected R4 error"
	print(f"✓ R4 Violation: PASSED (found {len(result['errors'])} error(s))")


def test_multi_violation() -> None:
	"""Test grid with multiple violations (R1 and R2+R3)."""
	grid = create_grid_multi_violation()
	result = check_all_constraints(grid, method="forward_checking")
	assert result["valid"] is False, "Should detect violations"
	# This grid has R1, R2, and R3 violations
	error_rules = {error["rule"] for error in result["errors"]}
	print(f"✓ Multi Violation: PASSED (found {len(result['errors'])} errors in rules: {error_rules})")


def test_all_methods() -> None:
	"""Test that all solver methods work correctly on the same grid."""
	grid = create_valid_sample_grid()
	
	results = {
		"backtracking": check_all_constraints(grid, method="backtracking"),
		"forward_checking": check_all_constraints(grid, method="forward_checking"),
		"arc_consistency": check_all_constraints(grid, method="arc_consistency"),
	}
	
	# All should agree on validity
	for method, result in results.items():
		assert result["valid"] is True, f"{method} should find grid valid"
		assert result["method"] == method, f"Method name should be {method}"
	
	print("✓ All Solver Methods: PASSED (all methods agree on validity)")


def test_violation_consistency_across_methods() -> None:
	"""Test that all methods detect the same violations."""
	grid = create_grid_r1_violation()
	
	results = {
		"backtracking": check_all_constraints(grid, method="backtracking"),
		"forward_checking": check_all_constraints(grid, method="forward_checking"),
		"arc_consistency": check_all_constraints(grid, method="arc_consistency"),
	}
	
	# All should find violation
	for method, result in results.items():
		assert result["valid"] is False, f"{method} should find violation"
		assert any(e["rule"] == "R1" for e in result["errors"]), f"{method} should detect R1 violation"
	
	print("✓ Violation Consistency: PASSED (all methods detect R1 violation)")


def run_all_tests() -> None:
	"""Run complete test suite."""
	print("\n" + "="*60)
	print("CSP VALIDATOR TEST SUITE - Multiple Grid Configurations")
	print("="*60 + "\n")
	
	# Valid grids
	print("Testing VALID grids:")
	test_valid_sample_grid()
	test_valid_compact_grid()
	
	# Invalid grids (single violations)
	print("\nTesting INVALID grids (single violations):")
	test_r1_violation()
	test_r2_violation()
	test_r3_violation()
	test_r4_violation()
	
	# Multiple violations
	print("\nTesting INVALID grids (multiple violations):")
	test_multi_violation()
	
	# Cross-method validation
	print("\nTesting CROSS-METHOD consistency:")
	test_all_methods()
	test_violation_consistency_across_methods()
	


if __name__ == "__main__":
	run_all_tests()
