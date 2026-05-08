"""Shared constraint rules and CSP problem construction for the validator."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Literal

try:
    from ..shared_utils.main import Grid, GridCell, manhattan
except ImportError:  # pragma: no cover - allows direct execution
    from pathlib import Path
    import sys

    MODULE_DIR = Path(__file__).resolve().parent
    APP_DIR = MODULE_DIR.parent
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    from shared_utils.main import Grid, GridCell, manhattan


@dataclass(slots=True)
class ValidationError:
    rule: str
    cell: tuple[int, int]
    message: str


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[ValidationError]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": [asdict(error) for error in self.errors],
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class CSPVariable:
    name: str
    rule: str
    cell: tuple[int, int]
    domain: list[tuple[int, int]]


@dataclass(slots=True)
class CSPProblem:
    grid: Grid
    variables: list[CSPVariable]


SolverMode = Literal["backtracking", "forward_checking", "arc_consistency"]


def build_csp_problem(grid: Grid) -> CSPProblem:
    variables: list[CSPVariable] = []

    hub_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_hub]
    charging_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_charging]
    pickup_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_medical_pickup]

    for cell in grid.iter_cells():
        if cell.zone == "Industrial":
            variables.append(
                CSPVariable(
                    name=f"R1:{cell.row},{cell.col}",
                    rule="R1",
                    cell=(cell.row, cell.col),
                    domain=[(cell.row, cell.col)] if not _has_forbidden_neighbor(grid, cell) else [],
                )
            )
        elif cell.zone == "Residential":
            variables.append(
                CSPVariable(
                    name=f"R2:{cell.row},{cell.col}",
                    rule="R2",
                    cell=(cell.row, cell.col),
                    domain=[hub for hub in hub_positions if manhattan((cell.row, cell.col), hub) <= 3],
                )
            )
        elif cell.is_hub:
            variables.append(
                CSPVariable(
                    name=f"R3:{cell.row},{cell.col}",
                    rule="R3",
                    cell=(cell.row, cell.col),
                    domain=[charging for charging in charging_positions if manhattan((cell.row, cell.col), charging) <= 2],
                )
            )
        elif cell.zone == "Hospital":
            variables.append(
                CSPVariable(
                    name=f"R4:{cell.row},{cell.col}",
                    rule="R4",
                    cell=(cell.row, cell.col),
                    domain=[pickup for pickup in pickup_positions if manhattan((cell.row, cell.col), pickup) <= 1],
                )
            )

    rule_order = {"R1": 0, "R2": 1, "R3": 2, "R4": 3}
    variables.sort(key=lambda variable: (rule_order[variable.rule], variable.cell[0], variable.cell[1]))
    return CSPProblem(grid=grid, variables=variables)


def _has_forbidden_neighbor(grid: Grid, cell: GridCell) -> bool:
    return any(neighbor.zone in {"School", "Hospital"} for neighbor in grid.get_neighbors(cell.row, cell.col))


def solve_problem_with_backtracking(problem: CSPProblem) -> ValidationResult:
    errors: list[ValidationError] = []

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


def solve_problem_with_forward_checking(problem: CSPProblem) -> ValidationResult:
    errors: list[ValidationError] = []
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


def solve_problem_with_arc_consistency(problem: CSPProblem) -> ValidationResult:
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


def _build_error(variable: CSPVariable) -> ValidationError:
    messages = {
        "R1": f"Industrial cell {variable.cell} is directly adjacent to a School or Hospital",
        "R2": f"Residential cell {variable.cell} is more than 3 cells away from every hub",
        "R3": f"Drone hub {variable.cell} has no charging pad within 2 cells",
        "R4": f"Hospital cell {variable.cell} has no medical pickup within 1 cell",
    }
    return ValidationError(rule=variable.rule, cell=variable.cell, message=messages[variable.rule])


def _variable_by_name(problem: CSPProblem, variable_name: str) -> CSPVariable:
    for variable in problem.variables:
        if variable.name == variable_name:
            return variable
    raise KeyError(variable_name)


def _dependent_variables(problem: CSPProblem, variable: CSPVariable) -> list[CSPVariable]:
    if variable.rule == "R2":
        return [candidate for candidate in problem.variables if candidate.rule == "R2" and candidate.name != variable.name]
    if variable.rule == "R3":
        return [candidate for candidate in problem.variables if candidate.rule == "R3" and candidate.name != variable.name]
    if variable.rule == "R4":
        return [candidate for candidate in problem.variables if candidate.rule == "R4" and candidate.name != variable.name]
    return []


def _forward_prune(
    problem: CSPProblem,
    variable: CSPVariable,
    candidate: tuple[int, int],
    domains: dict[str, list[tuple[int, int]]],
    next_index: int,
) -> bool:
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


def _value_is_consistent(variable: CSPVariable, value: tuple[int, int]) -> bool:
    if variable.rule == "R1":
        return True
    if variable.rule in {"R2", "R3", "R4"}:
        return value in variable.domain
    return False


def _revise_domain(problem: CSPProblem, variable: CSPVariable, domains: dict[str, list[tuple[int, int]]]) -> bool:
    old_domain = domains[variable.name]
    new_domain = [value for value in old_domain if _value_is_consistent(variable, value)]
    if new_domain == old_domain:
        return False
    domains[variable.name] = new_domain
    return True


def validate_grid(grid: Grid) -> ValidationResult:
    return solve_problem_with_backtracking(build_csp_problem(grid))


def check_industrial_safety(grid: Grid) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for cell in grid.iter_cells():
        if cell.zone != "Industrial":
            continue
        for neighbor in grid.get_neighbors(cell.row, cell.col):
            if neighbor.zone in {"School", "Hospital"}:
                errors.append(
                    ValidationError(
                        rule="R1",
                        cell=(cell.row, cell.col),
                        message=(
                            f"Industrial cell {(cell.row, cell.col)} is directly adjacent to "
                            f"{neighbor.zone} cell {(neighbor.row, neighbor.col)}"
                        ),
                    )
                )
                break
    return errors


def check_residential_coverage(grid: Grid) -> list[ValidationError]:
    hub_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_hub]
    errors: list[ValidationError] = []
    for cell in grid.iter_cells():
        if cell.zone != "Residential":
            continue
        if not hub_positions or min(manhattan((cell.row, cell.col), hub) for hub in hub_positions) > 3:
            errors.append(
                ValidationError(
                    rule="R2",
                    cell=(cell.row, cell.col),
                    message=f"Residential cell {(cell.row, cell.col)} is more than 3 cells away from every hub",
                )
            )
    return errors


def check_hub_charging(grid: Grid) -> list[ValidationError]:
    charging_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_charging]
    errors: list[ValidationError] = []
    for cell in grid.iter_cells():
        if not cell.is_hub:
            continue
        if not charging_positions or min(manhattan((cell.row, cell.col), charging) for charging in charging_positions) > 2:
            errors.append(
                ValidationError(
                    rule="R3",
                    cell=(cell.row, cell.col),
                    message=f"Drone hub {(cell.row, cell.col)} has no charging pad within 2 cells",
                )
            )
    return errors


def check_medical_access(grid: Grid) -> list[ValidationError]:
    hospital_cells = [cell for cell in grid.iter_cells() if cell.zone == "Hospital"]
    medical_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_medical_pickup]
    if not hospital_cells:
        return []
    if medical_positions and any(
        min(manhattan((hospital.row, hospital.col), pickup) for pickup in medical_positions) <= 1
        for hospital in hospital_cells
    ):
        return []
    return [
        ValidationError(
            rule="R4",
            cell=(hospital.row, hospital.col),
            message=f"Hospital cell {(hospital.row, hospital.col)} has no medical pickup within 1 cell",
        )
        for hospital in hospital_cells
    ]


def validate_grid(grid: Grid) -> ValidationResult:
    errors = []
    errors.extend(check_industrial_safety(grid))
    errors.extend(check_residential_coverage(grid))
    errors.extend(check_hub_charging(grid))
    errors.extend(check_medical_access(grid))
    warnings: list[str] = []
    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)