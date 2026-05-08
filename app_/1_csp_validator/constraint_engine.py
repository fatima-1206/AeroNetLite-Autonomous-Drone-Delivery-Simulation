"""Shared constraint rules and CSP problem construction for the validator."""

from __future__ import annotations

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





def _build_error(variable: CSPVariable) -> ValidationError:
    messages = {
        "R1": f"Industrial cell {variable.cell} is directly adjacent to a School or Hospital",
        "R2": f"Residential cell {variable.cell} is more than 3 cells away from every hub",
        "R3": f"Drone hub {variable.cell} has no charging pad within 2 cells",
        "R4": f"Hospital cell {variable.cell} has no medical pickup within 1 cell",
    }
    return ValidationError(rule=variable.rule, cell=variable.cell, message=messages[variable.rule])


def _value_is_consistent(variable: CSPVariable, value: tuple[int, int]) -> bool:
    if variable.rule == "R1":
        return True
    if variable.rule in {"R2", "R3", "R4"}:
        return value in variable.domain
    return False


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