"""Real-Time Disruption Handler for AeroNet Lite.

This module manages runtime disruptions in drone delivery operations:
- No-fly zone activation
- Route impact detection  
- Autonomous rerouting using A* pathfinding
- Event logging and status tracking
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from shared_utils.main import Grid, GridCell

# Import A* from Module 3 - dynamically load to avoid circular imports
def _load_astar():
    """Dynamically load A* function from Module 3."""
    astar_module_path = Path(__file__).parent.parent / "3_astar_planner" / "main.py"
    spec = importlib.util.spec_from_file_location("astar_module", astar_module_path)
    astar_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(astar_module)
    return astar_module.astar

try:
    # Try direct import first
    import _3_astar_planner.main
    astar = _3_astar_planner.main.astar
except (ImportError, ModuleNotFoundError):
    # Fallback to dynamic loading
    astar = _load_astar()


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Drone:
    """Represents a delivery drone with route and status tracking."""
    id: str
    current_position: tuple[int, int]
    target: tuple[int, int]
    route: list[tuple[int, int]]
    status: str = "ACTIVE"  # ACTIVE, DELAYED, FAILED, RETURNING


# ============================================================================
# Helper Functions
# ============================================================================

def is_no_fly(cell: GridCell | dict) -> bool:
    """Check if a cell is marked as no-fly zone.
    
    Args:
        cell: GridCell dataclass or dict representation
        
    Returns:
        True if cell is no-fly, False otherwise
    """
    if isinstance(cell, GridCell):
        return cell.no_fly
    elif isinstance(cell, dict):
        return cell.get("no_fly", False)
    return False


def set_no_fly(cell: GridCell | dict, value: bool) -> GridCell | dict:
    """Set no-fly status on a cell (dataclass or dict).
    
    Args:
        cell: GridCell dataclass or dict representation
        value: True to mark as no-fly, False otherwise
        
    Returns:
        Updated cell (GridCell or dict)
    """
    if isinstance(cell, GridCell):
        return replace(cell, no_fly=value)
    elif isinstance(cell, dict):
        cell["no_fly"] = value
        return cell
    return cell


# ============================================================================
# Core Disruption Functions
# ============================================================================

def activate_no_fly(grid: Grid, row: int, col: int) -> str:
    """Activate a no-fly zone at the specified grid cell.
    
    Args:
        grid: The simulation grid
        row: Row coordinate (0-9)
        col: Column coordinate (0-9)
        
    Returns:
        Event log string describing the action
        
    Example:
        "Step 11: No-fly cell activated at (4, 7)"
    """
    if not grid.in_bounds(row, col):
        return f"Error: Cell ({row}, {col}) is out of bounds"
    
    grid.update_cell(row, col, no_fly=True)
    return f"No-fly cell activated at ({row}, {col})"


def route_contains_blocked_cell(route: list[tuple[int, int]], grid: Grid) -> bool:
    """Check if a drone route intersects any no-fly zones.
    
    Args:
        route: List of (row, col) waypoints
        grid: The simulation grid
        
    Returns:
        True if route contains any no-fly cell, False otherwise
    """
    for row, col in route:
        cell = grid.get_cell(row, col)
        if cell is not None and is_no_fly(cell):
            return True
    return False


def reroute_drone(drone: Drone, grid: Grid) -> str:
    """Reroute a drone to its target using A* pathfinding.
    
    Updates drone.route and drone.status based on pathfinding success.
    
    Args:
        drone: Drone object with current_position, target, and status
        grid: The simulation grid
        
    Returns:
        Status string describing reroute attempt
    """
    # Use A* to find new path from current position to target
    path, cost, success = astar(drone.current_position, drone.target, grid)
    
    if success:
        drone.route = path
        drone.status = "ACTIVE"
        return f"Drone {drone.id} rerouted successfully using A*"
    else:
        drone.status = "DELAYED"
        return f"Drone {drone.id} cannot reach destination safely"


def force_return_to_hub(drone: Drone, nearest_hub: tuple[int, int], grid: Grid) -> str:
    """Reroute a drone back to its nearest hub using A* pathfinding.
    
    Used when a drone cannot reach its original target and must return to base.
    
    Args:
        drone: Drone object to reroute
        nearest_hub: Hub coordinates (row, col)
        grid: The simulation grid
        
    Returns:
        Status string describing return attempt
    """
    path, cost, success = astar(drone.current_position, nearest_hub, grid)
    
    if success:
        drone.route = path
        drone.target = nearest_hub
        drone.status = "RETURNING"
        return f"Drone {drone.id} returning to hub at {nearest_hub}"
    else:
        drone.status = "FAILED"
        return f"Drone {drone.id} cannot return to hub"


# ============================================================================
# Disruption Manager Class
# ============================================================================

class DisruptionManager:
    """Orchestrates disruption detection and response for the drone fleet.
    
    Responsibilities:
    - Maintain event logs
    - Activate no-fly zones
    - Detect drones on affected routes
    - Trigger rerouting for impacted drones
    - Track delivery status
    
    Example:
        manager = DisruptionManager()
        manager.trigger_no_fly(grid, 4, 7)
        manager.check_and_reroute(drones, grid)
        manager.print_event_log()
    """
    
    def __init__(self):
        """Initialize the DisruptionManager with empty event log."""
        self.event_log: list[str] = []
        self.step_counter: int = 0
    
    def add_event(self, event: str) -> None:
        """Add an event to the log with step counter.
        
        Args:
            event: Event description string
        """
        self.step_counter += 1
        timestamped_event = f"Step {self.step_counter}: {event}"
        self.event_log.append(timestamped_event)
        print(timestamped_event)
    
    def trigger_no_fly(self, grid: Grid, row: int, col: int) -> None:
        """Activate a no-fly zone and log the event.
        
        Args:
            grid: The simulation grid
            row: Row coordinate
            col: Column coordinate
        """
        event = activate_no_fly(grid, row, col)
        self.add_event(event)
    
    def check_and_reroute(self, drones: list[Drone], grid: Grid) -> None:
        """Check all drones for route conflicts and reroute if needed.
        
        Detects drones on no-fly intersecting routes and triggers rerouting.
        Only reroutes affected drones (those with blocked routes).
        
        Args:
            drones: List of Drone objects
            grid: The simulation grid
        """
        affected_count = 0
        
        for drone in drones:
            if route_contains_blocked_cell(drone.route, grid):
                affected_count += 1
                event = reroute_drone(drone, grid)
                self.add_event(event)
        
        if affected_count == 0:
            self.add_event(f"No drones affected by disruption ({len(drones)} active)")
    
    def print_event_log(self) -> None:
        """Display the complete event log to console."""
        print("\n" + "=" * 60)
        print("DISRUPTION HANDLER EVENT LOG")
        print("=" * 60)
        for event in self.event_log:
            print(event)
        print("=" * 60)
        print(f"Total events logged: {len(self.event_log)}")
        print("=" * 60 + "\n")


def create_sample_drones(grid: Grid) -> list[Drone]:
    """Create sample drones with predefined routes for demonstration."""
    
    # Drone D1: Route from (1,1) to (8,8) passing through (4,7)
    drone_d1 = Drone(
        id="D1",
        current_position=(1, 1),
        target=(8, 8),
        route=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)],
        status="ACTIVE"
    )
    
    # Drone D2: Route from (0,0) to (9,9) passing through (3,6)
    drone_d2 = Drone(
        id="D2",
        current_position=(0, 0),
        target=(9, 9),
        route=[(0, 0), (1, 1), (2, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 6), (9, 9)],
        status="ACTIVE"
    )
    
    # Drone D3: Route from (5,0) to (5,9) safe from current no-fly zones
    drone_d3 = Drone(
        id="D3",
        current_position=(5, 0),
        target=(5, 9),
        route=[(5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9)],
        status="ACTIVE"
    )
    
    return [drone_d1, drone_d2, drone_d3]


# ============================================================================
# Demo / Main Simulation
# ============================================================================

if __name__ == "__main__":
    """Run a demonstration of the disruption handler."""
    
    # Import grid creation utility
    from shared_utils.main import create_sample_grid
    
    print("\n" + "=" * 70)
    print("AeroNet Lite - Real-Time Disruption Handler Demo")
    print("=" * 70 + "\n")
    
    # Step 1 Initialize grid
    print("[1] Initializing 10x10 simulation grid...")
    grid = create_sample_grid()
    print("    Grid loaded with hubs, no-fly zones, and charging stations\n")
    
    # Step 2 Create sample drones with predefined routes
    print("[2] Creating 3 sample drones with initial routes...")
    
    # Drone D1 Route from (1,1) to (8,8) passing through (4,7)
    drone_d1 = Drone(
        id="D1",
        current_position=(1, 1),
        target=(8, 8),
        route=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)],
        status="ACTIVE"
    )
    
    # Drone D2 Route from (0,0) to (9,9) passing through (3,6)
    drone_d2 = Drone(
        id="D2",
        current_position=(0, 0),
        target=(9, 9),
        route=[(0, 0), (1, 1), (2, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 6), (9, 9)],
        status="ACTIVE"
    )
    
    # Drone D3 Route from (5,0) to (5,9) safe from current no-fly zones
    drone_d3 = Drone(
        id="D3",
        current_position=(5, 0),
        target=(5, 9),
        route=[(5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9)],
        status="ACTIVE"
    )
    
    drones = [drone_d1, drone_d2, drone_d3]
    print(f"    Created {len(drones)} drones")
    print(f"    Drone D1: {drone_d1.current_position} → {drone_d1.target} (ACTIVE)")
    print(f"    Drone D2: {drone_d2.current_position} → {drone_d2.target} (ACTIVE)")
    print(f"    Drone D3: {drone_d3.current_position} → {drone_d3.target} (ACTIVE)\n")
    
    # Step 3 Initialize DisruptionManager and begin monitoring
    print("[3] Starting DisruptionManager...")
    manager = DisruptionManager()
    manager.add_event("DisruptionManager initialized - monitoring 3 drones")
    print()
    
    # Step 4 Trigger first disruption (additional no-fly zone at 4,7)
    print("[4] Triggering disruption: Activating no-fly zone at (4, 7)...")
    manager.trigger_no_fly(grid, 4, 7)
    print()
    
    # Step 5 Check routes and reroute affected drones
    print("[5] Scanning drones for affected routes...")
    manager.check_and_reroute(drones, grid)
    print()
    
    # Step 6 Trigger second disruption (no-fly at 3,6)
    print("[6] Triggering secondary disruption: Activating no-fly zone at (3, 6)...")
    manager.trigger_no_fly(grid, 3, 6)
    print()
    
    # Step 7 Check routes again after second disruption
    print("[7] Re-scanning all drones after secondary disruption...")
    manager.check_and_reroute(drones, grid)
    print()
    
    # Step 8 Print final status report
    print("[8] Final Drone Status Report:")
    for drone in drones:
        route_length = len(drone.route)
        print(f"    {drone.id}: {drone.status:8s} | Target: {drone.target} | Route length: {route_length} waypoints")
    print()
    
    # Step 9 Print complete event log
    print("[9] Printing complete event log...")
    manager.print_event_log()
    
    print("Disruption Handler Demo Complete")
    print("=" * 70 + "\n")
