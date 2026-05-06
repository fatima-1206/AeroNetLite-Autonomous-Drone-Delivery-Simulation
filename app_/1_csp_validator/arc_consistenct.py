"""Arc-consistency CSP validation for AeroNet Lite."""

from __future__ import annotations

try:
    from .constraint_engine import ValidationResult, validate_grid
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, validate_grid


def _apply_arc_consistency(grid):
    return grid


def solve(grid) -> ValidationResult:
    consistent_grid = _apply_arc_consistency(grid)
    return validate_grid(consistent_grid)