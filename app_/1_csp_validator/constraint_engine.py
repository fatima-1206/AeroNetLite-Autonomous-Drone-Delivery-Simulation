"""shared constraint rules and csp problem construction for the validator"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Literal

try:
    from ..shared_utils.main import Grid, GridCell, manhattan
except ImportError:
    from pathlib import Path
    import sys

    MODULE_DIR = Path(__file__).resolve().parent
    APP_DIR = MODULE_DIR.parent
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    from shared_utils.main import Grid, GridCell, manhattan


# represents a single constraint violation with details about which rule failed
@dataclass(slots=True)
class ValidationError:
    # which rule was violated (r1, r2, r3, or r4)
    rule: str
    # the grid cell location where the problem occurred
    cell: tuple[int, int]
    # human-readable explanation of what went wrong
    message: str


# the final result of validating a grid, tells us if it's valid and why not if it isn't
@dataclass(slots=True)
class ValidationResult:
    # true if the grid passes all constraints, false otherwise
    valid: bool
    # list of all constraint violations found
    errors: list[ValidationError]
    # non-critical warnings that don't make the grid invalid
    warnings: list[str]

    # convert to dictionary format for easier serialization
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": [asdict(error) for error in self.errors],
            "warnings": list(self.warnings),
        }


# represents a single variable in the constraint satisfaction problem
# this corresponds to checking one constraint at one location
@dataclass(slots=True)
class CSPVariable:
    # unique identifier for this variable (e.g., "R1:2,4")
    name: str
    # which constraint rule this variable represents
    rule: str
    # the grid cell this variable is checking
    cell: tuple[int, int]
    # the set of valid values (cell locations) this variable can take
    domain: list[tuple[int, int]]


# a complete constraint satisfaction problem for the grid
@dataclass(slots=True)
class CSPProblem:
    # the grid being validated
    grid: Grid
    # all the variables (constraints to check) derived from the grid
    variables: list[CSPVariable]


# type alias defining which solving algorithms we support
SolverMode = Literal["backtracking", "forward_checking", "arc_consistency"]


# build a constraint satisfaction problem from the grid
# this converts the grid into variables and domains that solvers can work with
def build_csp_problem(grid: Grid) -> CSPProblem:
    variables: list[CSPVariable] = []

    # find all special cell positions in the grid
    hub_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_hub]
    charging_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_charging]
    pickup_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_medical_pickup]

    # go through each cell and create csp variables based on the cell's type and constraints
    for cell in grid.iter_cells():
        # r1: industrial zones must not be adjacent to schools or hospitals
        if cell.zone == "Industrial":
            variables.append(
                CSPVariable(
                    name=f"R1:{cell.row},{cell.col}",
                    rule="R1",
                    cell=(cell.row, cell.col),
                    # if the industrial cell has forbidden neighbors, domain is empty (violation)
                    domain=[(cell.row, cell.col)] if not _has_forbidden_neighbor(grid, cell) else [],
                )
            )
        # r2: residential zones must be within 3 cells of at least one hub
        elif cell.zone == "Residential":
            variables.append(
                CSPVariable(
                    name=f"R2:{cell.row},{cell.col}",
                    rule="R2",
                    cell=(cell.row, cell.col),
                    # domain is all hubs within manhattan distance 3
                    domain=[hub for hub in hub_positions if manhattan((cell.row, cell.col), hub) <= 3],
                )
            )
        # r3: drone hubs must have a charging pad within 2 cells
        elif cell.is_hub:
            variables.append(
                CSPVariable(
                    name=f"R3:{cell.row},{cell.col}",
                    rule="R3",
                    cell=(cell.row, cell.col),
                    # domain is all charging pads within manhattan distance 2
                    domain=[charging for charging in charging_positions if manhattan((cell.row, cell.col), charging) <= 2],
                )
            )
        # r4: hospitals must have a medical pickup within 1 cell
        elif cell.zone == "Hospital":
            variables.append(
                CSPVariable(
                    name=f"R4:{cell.row},{cell.col}",
                    rule="R4",
                    cell=(cell.row, cell.col),
                    # domain is all medical pickups within manhattan distance 1
                    domain=[pickup for pickup in pickup_positions if manhattan((cell.row, cell.col), pickup) <= 1],
                )
            )

    # sort variables by rule type and then by position for consistent processing order
    # this helps with reproducibility and debugging
    rule_order = {"R1": 0, "R2": 1, "R3": 2, "R4": 3}
    variables.sort(key=lambda variable: (rule_order[variable.rule], variable.cell[0], variable.cell[1]))
    return CSPProblem(grid=grid, variables=variables)


# check if an industrial zone cell is adjacent to a school or hospital
# if it is, that's a violation of the industrial safety rule
def _has_forbidden_neighbor(grid: Grid, cell: GridCell) -> bool:
    return any(neighbor.zone in {"School", "Hospital"} for neighbor in grid.get_neighbors(cell.row, cell.col))





# create an error message for a variable with an empty domain
# this means the constraint represented by the variable cannot be satisfied
def _build_error(variable: CSPVariable) -> ValidationError:
    # each rule has its own error message explaining what went wrong
    messages = {
        "R1": f"Industrial cell {variable.cell} is directly adjacent to a School or Hospital",
        "R2": f"Residential cell {variable.cell} is more than 3 cells away from every hub",
        "R3": f"Drone hub {variable.cell} has no charging pad within 2 cells",
        "R4": f"Hospital cell {variable.cell} has no medical pickup within 1 cell",
    }
    return ValidationError(rule=variable.rule, cell=variable.cell, message=messages[variable.rule])


# check if a value is consistent with a constraint variable's domain
# this is used during constraint propagation to prune invalid values
def _value_is_consistent(variable: CSPVariable, value: tuple[int, int]) -> bool:
    # r1 is always consistent if we get here (domain was already set correctly)
    if variable.rule == "R1":
        return True
    # for r2, r3, r4: check if the value is in the allowed domain
    if variable.rule in {"R2", "R3", "R4"}:
        return value in variable.domain
    return False


# check rule r1: industrial zones cannot be adjacent to schools or hospitals
# this is a direct validation function (not part of the csp solver)
def check_industrial_safety(grid: Grid) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for cell in grid.iter_cells():
        if cell.zone != "Industrial":
            continue
        # look at all neighbors of this industrial cell
        for neighbor in grid.get_neighbors(cell.row, cell.col):
            # if we find a forbidden neighbor, record the error
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


# check rule r2: residential zones must be within 3 cells of at least one hub
def check_residential_coverage(grid: Grid) -> list[ValidationError]:
    # find all hub positions first
    hub_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_hub]
    errors: list[ValidationError] = []
    for cell in grid.iter_cells():
        if cell.zone != "Residential":
            continue
        # check if this residential cell is too far from all hubs
        if not hub_positions or min(manhattan((cell.row, cell.col), hub) for hub in hub_positions) > 3:
            errors.append(
                ValidationError(
                    rule="R2",
                    cell=(cell.row, cell.col),
                    message=f"Residential cell {(cell.row, cell.col)} is more than 3 cells away from every hub",
                )
            )
    return errors


# check rule r3: drone hubs must have a charging pad within 2 cells
def check_hub_charging(grid: Grid) -> list[ValidationError]:
    # find all charging pad positions
    charging_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_charging]
    errors: list[ValidationError] = []
    for cell in grid.iter_cells():
        if not cell.is_hub:
            continue
        # check if this hub has a nearby charging pad
        if not charging_positions or min(manhattan((cell.row, cell.col), charging) for charging in charging_positions) > 2:
            errors.append(
                ValidationError(
                    rule="R3",
                    cell=(cell.row, cell.col),
                    message=f"Drone hub {(cell.row, cell.col)} has no charging pad within 2 cells",
                )
            )
    return errors


# check rule r4: hospitals must have a medical pickup point within 1 cell
def check_medical_access(grid: Grid) -> list[ValidationError]:
    # find all hospital and medical pickup positions
    hospital_cells = [cell for cell in grid.iter_cells() if cell.zone == "Hospital"]
    medical_positions = [(cell.row, cell.col) for cell in grid.iter_cells() if cell.is_medical_pickup]
    # if there are no hospitals, this rule is automatically satisfied
    if not hospital_cells:
        return []
    # if all hospitals have at least one nearby medical pickup, we're good
    if medical_positions and any(
        min(manhattan((hospital.row, hospital.col), pickup) for pickup in medical_positions) <= 1
        for hospital in hospital_cells
    ):
        return []
    # otherwise every hospital that doesn't have nearby medical access is an error
    return [
        ValidationError(
            rule="R4",
            cell=(hospital.row, hospital.col),
            message=f"Hospital cell {(hospital.row, hospital.col)} has no medical pickup within 1 cell",
        )
        for hospital in hospital_cells
    ]


# run all the direct constraint checks and combine the results
# this is the non-csp validation approach (checks all rules directly)
def validate_grid(grid: Grid) -> ValidationResult:
    # collect all errors from each constraint check
    errors = []
    errors.extend(check_industrial_safety(grid))
    errors.extend(check_residential_coverage(grid))
    errors.extend(check_hub_charging(grid))
    errors.extend(check_medical_access(grid))
    warnings: list[str] = []
    # grid is valid if and only if there are no errors
    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)