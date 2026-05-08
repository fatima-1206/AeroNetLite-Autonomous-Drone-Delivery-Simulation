"""Arc-consistency CSP validation for AeroNet Lite."""

from __future__ import annotations

from collections import deque

try:
    from .constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent


def _variable_by_name(problem: CSPProblem, variable_name: str) -> CSPVariable:
    """Find a variable in the CSP problem by name."""
    for variable in problem.variables:
        if variable.name == variable_name:
            return variable
    raise KeyError(variable_name)


def _dependent_variables(problem: CSPProblem, variable: CSPVariable) -> list[CSPVariable]:
    """Find variables that depend on the given variable in constraint propagation."""
    if variable.rule == "R2":
        return [candidate for candidate in problem.variables if candidate.rule == "R2" and candidate.name != variable.name]
    if variable.rule == "R3":
        return [candidate for candidate in problem.variables if candidate.rule == "R3" and candidate.name != variable.name]
    if variable.rule == "R4":
        return [candidate for candidate in problem.variables if candidate.rule == "R4" and candidate.name != variable.name]
    return []


def _revise_domain(problem: CSPProblem, variable: CSPVariable, domains: dict[str, list[tuple[int, int]]]) -> bool:
    """Revise domain of a variable using arc consistency."""
    old_domain = domains[variable.name]
    new_domain = [value for value in old_domain if _value_is_consistent(variable, value)]
    if new_domain == old_domain:
        return False
    domains[variable.name] = new_domain
    return True


def _solve_problem_with_arc_consistency(problem: CSPProblem) -> ValidationResult:
    """Solve CSP using arc consistency algorithm."""
    domains = {variable.name: list(variable.domain) for variable in problem.variables}
    queue = deque(variable.name for variable in problem.variables)

    while queue:
        variable_name = queue.popleft()
        variable = _variable_by_name(problem, variable_name)
        if _revise_domain(problem, variable, domains):
            if not domains[variable.name]:
                break
            for neighbor in _dependent_variables(problem, variable):
                queue.append(neighbor.name)

    errors = [_build_error(variable) for variable in problem.variables if not domains[variable.name]]
    return ValidationResult(valid=not errors, errors=errors, warnings=[])


def solve(grid) -> ValidationResult:
    """Public API for arc consistency solver."""
    problem = build_csp_problem(grid)
    return _solve_problem_with_arc_consistency(problem)