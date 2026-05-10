from __future__ import annotations

from dataclasses import asdict, dataclass

try:
	from .arc_consistenct import solve as arc_consistency_solve
	from .backtracking import solve as backtracking_solve
	from .constraint_engine import ValidationResult
	from .forward_checking import solve as forward_checking_solve
except ImportError:  
	from pathlib import Path
	import sys

	MODULE_DIR = Path(__file__).resolve().parent
	APP_DIR = MODULE_DIR.parent
	if str(APP_DIR) not in sys.path:
		sys.path.insert(0, str(APP_DIR))

	from arc_consistenct import solve as arc_consistency_solve
	from backtracking import solve as backtracking_solve
	from constraint_engine import ValidationResult
	from forward_checking import solve as forward_checking_solve


# type alias for the solver method name
SolverName = str


# wraps the validation result with metadata about which method was used
@dataclass(slots=True)
class CSPModuleResult:
	# whether the grid is valid or not
	valid: bool
	# list of constraint violations found
	errors: list[dict]
	# non-critical warnings
	warnings: list[str]
	# which solving algorithm was used
	method: str

	# convert to a dictionary for easier serialization
	def to_dict(self) -> dict:
		return asdict(self)


# the main public api function for grid validation
# users call this to check if a grid is valid
def check_all_constraints(grid, method: SolverName = "backtracking") -> dict:
	# map method names to their solver functions
	solver_map = {
		"backtracking": backtracking_solve,
		"forward_checking": forward_checking_solve,
		"arc_consistency": arc_consistency_solve,
	}
	if method not in solver_map:
		raise ValueError(f"Unsupported CSP method: {method}")

	# call the appropriate solver
	result = solver_map[method](grid)
	# convert the result to a dictionary with metadata
	if isinstance(result, ValidationResult):
		return {
			"valid": result.valid,
			"errors": [asdict(error) for error in result.errors],
			"warnings": list(result.warnings),
			"method": method,
		}

	return result


# alias for check_all_constraints to make it fit into the senario description
def validate(grid, method: SolverName = "backtracking") -> dict:
	return check_all_constraints(grid, method=method)


# if this file is run directly (not imported), test it with a sample grid
if __name__ == "__main__":
	from app_.shared_utils.main import create_sample_grid

	# create a test grid and validate it
	sample = create_sample_grid()
	print(check_all_constraints(sample, method="backtracking"))
