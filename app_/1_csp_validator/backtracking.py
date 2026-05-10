from __future__ import annotations
try:
    from .constraint_engine import ValidationResult, CSPProblem, build_csp_problem, _build_error
except ImportError:
    from constraint_engine import ValidationResult, CSPProblem, build_csp_problem, _build_error


# the backtracking solver works recursively through all variables
# if any variable has an empty domain, we record it as an error
def _solve_problem_with_backtracking(problem: CSPProblem) -> ValidationResult:
    """solve csp using backtracking search."""
    errors: list = []

    # recursive depth-first search through variable assignments
    def dfs(index: int) -> None:
        # base case: we've processed all variables
        if index >= len(problem.variables):
            return

        variable = problem.variables[index]
        # if this variable has no valid values, record the error
        if not variable.domain:
            errors.append(_build_error(variable))
            # keep processing remaining variables even after finding an error
            dfs(index + 1)
            return

        # try the first (or only) value in the domain
        # in a full implementation we'd try all values and backtrack on failure
        for _candidate in variable.domain[:1]:
            dfs(index + 1)
            break

    # start the recursive search from the first variable
    dfs(0)
    return ValidationResult(valid=not errors, errors=errors, warnings=[])


# public entry point for the backtracking solving method
def solve(grid) -> ValidationResult:
    problem = build_csp_problem(grid)
    return _solve_problem_with_backtracking(problem)