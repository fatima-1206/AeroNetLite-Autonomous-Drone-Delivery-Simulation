"""Shared constraint rules for the CSP validator."""

from __future__ import annotations

from dataclasses import asdict, dataclass

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