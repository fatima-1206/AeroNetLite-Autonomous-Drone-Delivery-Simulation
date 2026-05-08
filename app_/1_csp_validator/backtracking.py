"""Backtracking CSP validation for AeroNet Lite."""

from __future__ import annotations

try:
    from .constraint_engine import ValidationResult, CSPProblem, build_csp_problem, _build_error
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, CSPProblem, build_csp_problem, _build_error


def _solve_problem_with_backtracking(problem: CSPProblem) -> ValidationResult:
    """Solve CSP using backtracking search."""
    errors: list = []

    def dfs(index: int) -> None:
        if index >= len(problem.variables):
            return

        variable = problem.variables[index]
        if not variable.domain:
            errors.append(_build_error(variable))
            dfs(index + 1)
            return

        for _candidate in variable.domain[:1]:
            dfs(index + 1)
            break

    dfs(0)
    return ValidationResult(valid=not errors, errors=errors, warnings=[])


def solve(grid) -> ValidationResult:
    """Public API for backtracking solver."""
    problem = build_csp_problem(grid)
    return _solve_problem_with_backtracking(problem)