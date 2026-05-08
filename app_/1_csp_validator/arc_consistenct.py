"""Arc-consistency CSP validation for AeroNet Lite."""

from __future__ import annotations

try:
    from .constraint_engine import ValidationResult, build_csp_problem, solve_problem_with_arc_consistency
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, build_csp_problem, solve_problem_with_arc_consistency


def solve(grid) -> ValidationResult:
    problem = build_csp_problem(grid)
    return solve_problem_with_arc_consistency(problem)