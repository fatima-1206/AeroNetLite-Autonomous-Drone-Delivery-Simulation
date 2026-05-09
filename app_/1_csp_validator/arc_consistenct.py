from __future__ import annotations
from collections import deque

try:
    from .constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent


# helper function to look up a variable by its name in the problem
# we need this because we work with variable names during propagation
def _variable_by_name(problem: CSPProblem, variable_name: str) -> CSPVariable:
    for variable in problem.variables:
        if variable.name == variable_name:
            return variable
    raise KeyError(variable_name)


# find variables that are affected by changes to the given variable
# for arc consistency we need to track which variables share constraints
def _dependent_variables(problem: CSPProblem, variable: CSPVariable) -> list[CSPVariable]:
    """find variables that depend on the given variable in constraint propagation."""
    # r2, r3, and r4 rules interact with other variables of the same rule type
    if variable.rule == "R2":
        return [candidate for candidate in problem.variables if candidate.rule == "R2" and candidate.name != variable.name]
    if variable.rule == "R3":
        return [candidate for candidate in problem.variables if candidate.rule == "R3" and candidate.name != variable.name]
    if variable.rule == "R4":
        return [candidate for candidate in problem.variables if candidate.rule == "R4" and candidate.name != variable.name]
    return []


# the core arc consistency operation that removes inconsistent values from a domain
# if the domain changes we return true so we know to propagate further
def _revise_domain(problem: CSPProblem, variable: CSPVariable, domains: dict[str, list[tuple[int, int]]]) -> bool:
    """revise domain of a variable using arc consistency."""
    old_domain = domains[variable.name]
    # keep only values that satisfy the constraint
    new_domain = [value for value in old_domain if _value_is_consistent(variable, value)]
    if new_domain == old_domain:
        return False
    domains[variable.name] = new_domain
    return True


# the main arc consistency algorithm implementation
# we iteratively prune domains until we reach a fixed point
def _solve_problem_with_arc_consistency(problem: CSPProblem) -> ValidationResult:
    """solve csp using arc consistency algorithm."""
    # make a working copy of each variable's domain
    domains = {variable.name: list(variable.domain) for variable in problem.variables}
    # start with all variables in the queue to process
    queue = deque(variable.name for variable in problem.variables)

    # keep processing until the queue is empty (no more domains changed)
    while queue:
        variable_name = queue.popleft()
        variable = _variable_by_name(problem, variable_name)
        # try to prune this variable's domain
        if _revise_domain(problem, variable, domains):
            # if we removed values, check if the domain became empty
            if not domains[variable.name]:
                break
            # add dependent variables back to queue for reprocessing
            for neighbor in _dependent_variables(problem, variable):
                queue.append(neighbor.name)

    # any variable with an empty domain represents a constraint violation
    errors = [_build_error(variable) for variable in problem.variables if not domains[variable.name]]
    return ValidationResult(valid=not errors, errors=errors, warnings=[])


# public entry point for this solving method
# converts the grid into a csp problem then solves it
def solve(grid) -> ValidationResult:
    """public api for arc consistency solver."""
    problem = build_csp_problem(grid)
    return _solve_problem_with_arc_consistency(problem)