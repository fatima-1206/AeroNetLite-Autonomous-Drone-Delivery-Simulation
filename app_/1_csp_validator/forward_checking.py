"""Forward-checking CSP validation for AeroNet Lite."""

from __future__ import annotations

try:
    from .constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent


def _forward_prune(
    problem: CSPProblem,
    variable: CSPVariable,
    candidate: tuple[int, int],
    domains: dict[str, list[tuple[int, int]]],
    next_index: int,
) -> bool:
    """Prune domains of future variables based on current assignment."""
    domains[variable.name] = [candidate]
    for future_variable in problem.variables[next_index:]:
        future_domain = domains[future_variable.name]
        if not future_domain:
            continue
        # The problem is mostly unary, but we still prune by keeping only legal
        # support values for each future variable after the current assignment.
        domains[future_variable.name] = [value for value in future_domain if _value_is_consistent(future_variable, value)]
        if not domains[future_variable.name]:
            return False
    return True


def _solve_problem_with_forward_checking(problem: CSPProblem) -> ValidationResult:
    """Solve CSP using forward checking."""
    errors: list = []
    domains = {variable.name: list(variable.domain) for variable in problem.variables}

    def propagate(index: int) -> bool:
        if index >= len(problem.variables):
            return True

        variable = problem.variables[index]
        current_domain = domains[variable.name]
        if not current_domain:
            errors.append(_build_error(variable))
            return False

        for candidate in current_domain[:1]:
            snapshot = {name: list(domain) for name, domain in domains.items()}
            if _forward_prune(problem, variable, candidate, domains, index + 1):
                if propagate(index + 1):
                    return True
            domains.clear()
            domains.update(snapshot)

        return False

    propagate(0)
    return ValidationResult(valid=not errors, errors=errors, warnings=[])


def solve(grid) -> ValidationResult:
    """Public API for forward checking solver."""
    problem = build_csp_problem(grid)
    return _solve_problem_with_forward_checking(problem)