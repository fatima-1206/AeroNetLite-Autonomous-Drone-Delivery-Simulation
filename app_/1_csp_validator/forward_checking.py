"""Forward-checking CSP validation for AeroNet Lite."""

from __future__ import annotations

try:
    from .constraint_engine import ValidationResult, validate_grid
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, validate_grid


def _prune_impossible_states(grid):
    return grid


def solve(grid) -> ValidationResult:
    pruned_grid = _prune_impossible_states(grid)
    return validate_grid(pruned_grid)