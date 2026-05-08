"""Disruption Handler module

Real-Time Disruption Handler for the AeroNet Lite drone delivery simulation.
Manages no-fly zone activation, route impact detection, autonomous rerouting,
and event logging.

Classes:
    - Drone: Represents a delivery drone with route and status tracking

Functions:
    - is_no_fly: Check if a cell is a no-fly zone
    - set_no_fly: Mark a cell as no-fly zone
    - activate_no_fly: Activate no-fly zone on grid
    - route_contains_blocked_cell: Detect no-fly cells in a route
    - reroute_drone: Reroute drone using A* pathfinding
    - force_return_to_hub: Force drone to return to nearest hub

Classes:
    - DisruptionManager: Orchestrates disruption detection and response
"""

from .main import (
    Drone,
    is_no_fly,
    set_no_fly,
    activate_no_fly,
    route_contains_blocked_cell,
    reroute_drone,
    force_return_to_hub,
    DisruptionManager,
)

__all__ = [
    "Drone",
    "is_no_fly",
    "set_no_fly",
    "activate_no_fly",
    "route_contains_blocked_cell",
    "reroute_drone",
    "force_return_to_hub",
    "DisruptionManager",
]
