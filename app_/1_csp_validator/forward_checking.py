
from __future__ import annotations
try:
    from .constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent
except ImportError:
    from constraint_engine import ValidationResult, CSPProblem, CSPVariable, build_csp_problem, _build_error, _value_is_consistent


# the core forward checking operation
# when we assign a value to a variable, we prune domains of future variables
def _forward_prune(
    problem: CSPProblem,
    variable: CSPVariable,
    candidate: tuple[int, int],
    domains: dict[str, list[tuple[int, int]]],
    next_index: int,
) -> bool:
    # fix the current variable to this candidate value
    domains[variable.name] = [candidate]
    # look ahead at all remaining unassigned variables
    for future_variable in problem.variables[next_index:]:
        future_domain = domains[future_variable.name]
        if not future_domain:
            continue
        # remove values from future variable's domain that are incompatible
        # with the current assignment (even though most constraints are unary in our problem)
        domains[future_variable.name] = [value for value in future_domain if _value_is_consistent(future_variable, value)]
        # if a future variable's domain becomes empty, this path won't work
        if not domains[future_variable.name]:
            return False
    return True


# the forward checking solver uses recursive propagation with domain pruning
def _solve_problem_with_forward_checking(problem: CSPProblem) -> ValidationResult:
    errors: list = []
    # make a working copy of each variable's domain
    domains = {variable.name: list(variable.domain) for variable in problem.variables}

    # recursive function that processes variables one at a time
    def propagate(index: int) -> bool:
        # base case: we've successfully assigned all variables
        if index >= len(problem.variables):
            return True

        variable = problem.variables[index]
        current_domain = domains[variable.name]
        # if this variable has no valid values, record the error
        if not current_domain:
            errors.append(_build_error(variable))
            return False

        # try the first (or only) value in the domain
        for candidate in current_domain[:1]:
            # save the current state of all domains
            snapshot = {name: list(domain) for name, domain in domains.items()}
            # try to assign this candidate and see if we can proceed
            if _forward_prune(problem, variable, candidate, domains, index + 1):
                # recursively try to assign the next variable
                if propagate(index + 1):
                    return True
            # if that didn't work, restore the domain snapshot and try another value
            domains.clear()
            domains.update(snapshot)

        # no candidate for this variable led to a solution
        return False

    # start the propagation from the first variable
    propagate(0)
    return ValidationResult(valid=not errors, errors=errors, warnings=[])


# public entry point for the forward checking solving method
def solve(grid) -> ValidationResult:
    problem = build_csp_problem(grid)
    return _solve_problem_with_forward_checking(problem)