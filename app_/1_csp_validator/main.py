"""CSP validator entry point for AeroNet Lite.

The public API dispatches to one of the available solver modes while keeping a
single validation contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

try:
	from .arc_consistenct import solve as arc_consistency_solve
	from .backtracking import solve as backtracking_solve
	from .constraint_engine import ValidationResult
	from .forward_checking import solve as forward_checking_solve
except ImportError:  # pragma: no cover - allows direct execution
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


SolverName = str


@dataclass(slots=True)
class CSPModuleResult:
	valid: bool
	errors: list[dict]
	warnings: list[str]
	method: str

	def to_dict(self) -> dict:
		return asdict(self)


def check_all_constraints(grid, method: SolverName = "backtracking") -> dict:
	"""Validate the grid with the requested CSP strategy."""

	solver_map = {
		"backtracking": backtracking_solve,
		"forward_checking": forward_checking_solve,
		"arc_consistency": arc_consistency_solve,
	}
	if method not in solver_map:
		raise ValueError(f"Unsupported CSP method: {method}")

	result = solver_map[method](grid)
	if isinstance(result, ValidationResult):
		return {
			"valid": result.valid,
			"errors": [asdict(error) for error in result.errors],
			"warnings": list(result.warnings),
			"method": method,
		}

	return result


def validate(grid, method: SolverName = "backtracking") -> dict:
	"""Alias for check_all_constraints for a more concise call site."""

	return check_all_constraints(grid, method=method)


if __name__ == "__main__":
	from app_.shared_utils.main import create_sample_grid

	sample = create_sample_grid()
	print(check_all_constraints(sample, method="backtracking"))
