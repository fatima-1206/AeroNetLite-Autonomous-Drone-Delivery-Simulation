"""Backtracking-style CSP validation for AeroNet Lite."""

from __future__ import annotations

try:
    from .constraint_engine import ValidationResult, validate_grid
except ImportError:  # pragma: no cover - allows direct execution
    from constraint_engine import ValidationResult, validate_grid


def _validate_rules_in_order(grid) -> ValidationResult:
    return validate_grid(grid)


def solve(grid) -> ValidationResult:
    return _validate_rules_in_order(grid)