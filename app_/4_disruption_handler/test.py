"""Unit tests for the Real-Time Disruption Handler module.

Tests cover:
- No-fly zone activation
- Route blocking detection
- Successful and failed rerouting
- Event logging
- DisruptionManager orchestration
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from shared_utils.main import create_sample_grid, Grid, GridCell
from main import (
    Drone,
    is_no_fly,
    set_no_fly,
    activate_no_fly,
    route_contains_blocked_cell,
    reroute_drone,
    force_return_to_hub,
    DisruptionManager,
)


# ============================================================================
# Test Helper Functions
# ============================================================================

def test_is_no_fly():
    """Test no-fly detection with both GridCell and dict representations."""
    print("Testing is_no_fly()...")
    
    # Test with GridCell
    cell_no_fly = GridCell(0, 0, "Open Field", 1000, no_fly=True)
    cell_safe = GridCell(0, 1, "Open Field", 1000, no_fly=False)
    
    assert is_no_fly(cell_no_fly) == True, "Should detect no-fly GridCell"
    assert is_no_fly(cell_safe) == False, "Should detect safe GridCell"
    
    # Test with dict
    dict_no_fly = {"no_fly": True, "row": 0, "col": 0}
    dict_safe = {"no_fly": False, "row": 0, "col": 1}
    
    assert is_no_fly(dict_no_fly) == True, "Should detect no-fly dict"
    assert is_no_fly(dict_safe) == False, "Should detect safe dict"
    
    print("  ✓ is_no_fly() tests passed\n")


def test_set_no_fly():
    """Test setting no-fly status on both GridCell and dict representations."""
    print("Testing set_no_fly()...")
    
    # Test with GridCell
    cell = GridCell(0, 0, "Open Field", 1000, no_fly=False)
    updated_cell = set_no_fly(cell, True)
    assert updated_cell.no_fly == True, "Should update GridCell no_fly to True"
    
    updated_cell = set_no_fly(updated_cell, False)
    assert updated_cell.no_fly == False, "Should update GridCell no_fly to False"
    
    # Test with dict
    cell_dict = {"no_fly": False}
    updated_dict = set_no_fly(cell_dict, True)
    assert updated_dict["no_fly"] == True, "Should update dict no_fly to True"
    
    print("  ✓ set_no_fly() tests passed\n")


# ============================================================================
# Core Function Tests
# ============================================================================

def test_activate_no_fly():
    """Test no-fly zone activation on the grid."""
    print("Testing activate_no_fly()...")
    
    grid = create_sample_grid()
    
    # Test: Activate no-fly at (2, 5)
    result = activate_no_fly(grid, 2, 5)
    assert "(2, 5)" in result, "Should mention activated cell in result"
    
    cell = grid.get_cell(2, 5)
    assert cell is not None and cell.no_fly == True, "Cell should be marked as no-fly"
    
    # Test: Out of bounds
    result_oob = activate_no_fly(grid, 15, 15)
    assert "out of bounds" in result_oob.lower(), "Should indicate out of bounds error"
    
    print("  ✓ activate_no_fly() tests passed\n")


def test_route_contains_blocked_cell():
    """Test detection of no-fly cells in drone routes."""
    print("Testing route_contains_blocked_cell()...")
    
    grid = create_sample_grid()
    
    # Create a route that doesn't hit no-fly zones initially
    safe_route = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
    assert route_contains_blocked_cell(safe_route, grid) == False, "Safe route should not contain blocked cells"
    
    # Route through known no-fly zone (3, 6)
    risky_route = [(2, 6), (3, 6), (4, 6)]
    assert route_contains_blocked_cell(risky_route, grid) == True, "Route through no-fly should be detected"
    
    # Activate a new no-fly zone and test
    activate_no_fly(grid, 5, 5)
    new_route = [(4, 5), (5, 5), (6, 5)]
    assert route_contains_blocked_cell(new_route, grid) == True, "New no-fly zone should be detected in route"
    
    print("  ✓ route_contains_blocked_cell() tests passed\n")


def test_reroute_drone_success():
    """Test successful drone rerouting with A* pathfinding."""
    print("Testing reroute_drone() - success case...")
    
    grid = create_sample_grid()
    
    # Create drone with blocked route
    drone = Drone(
        id="D_TEST1",
        current_position=(0, 0),
        target=(2, 2),
        route=[(0, 0), (3, 6), (2, 2)],  # Route hits no-fly at (3, 6)
        status="ACTIVE"
    )
    
    # Reroute should succeed (ACTIVE -> ACTIVE)
    result = reroute_drone(drone, grid)
    assert "successfully" in result.lower(), "Reroute should succeed"
    assert drone.status == "ACTIVE", "Drone status should remain ACTIVE after successful reroute"
    assert drone.route != [(0, 0), (3, 6), (2, 2)], "Route should be updated"
    
    print("  ✓ reroute_drone() success tests passed\n")


def test_reroute_drone_failure():
    """Test failed drone rerouting when no path exists."""
    print("Testing reroute_drone() - failure case...")
    
    grid = create_sample_grid()
    
    # Create drone with impossible target (no-fly zone)
    drone = Drone(
        id="D_TEST2",
        current_position=(0, 0),
        target=(3, 6),  # No-fly zone - unreachable
        route=[(0, 0), (1, 1), (3, 6)],
        status="ACTIVE"
    )
    
    # Reroute should fail (ACTIVE -> DELAYED)
    result = reroute_drone(drone, grid)
    assert "cannot reach" in result.lower(), "Reroute should fail"
    assert drone.status == "DELAYED", "Drone status should be DELAYED after failed reroute"
    
    print("  ✓ reroute_drone() failure tests passed\n")


def test_force_return_to_hub():
    """Test forcing a drone to return to its hub."""
    print("Testing force_return_to_hub()...")
    
    grid = create_sample_grid()
    hub = (1, 3)  # Known hub position from sample grid
    
    # Create drone at a safe location
    drone = Drone(
        id="D_TEST3",
        current_position=(5, 5),
        target=(9, 9),
        route=[(5, 5), (6, 6), (7, 7), (8, 8), (9, 9)],
        status="ACTIVE"
    )
    
    # Force return to hub
    result = force_return_to_hub(drone, hub, grid)
    assert "returning" in result.lower(), "Should indicate returning to hub"
    assert drone.status == "RETURNING", "Drone status should be RETURNING"
    assert drone.target == hub, "Drone target should be updated to hub"
    assert len(drone.route) > 0, "Drone should have a valid return route"
    
    print("  ✓ force_return_to_hub() tests passed\n")


# ============================================================================
# DisruptionManager Tests
# ============================================================================

def test_disruption_manager_add_event():
    """Test event logging in DisruptionManager."""
    print("Testing DisruptionManager.add_event()...")
    
    manager = DisruptionManager()
    assert len(manager.event_log) == 0, "Event log should start empty"
    assert manager.step_counter == 0, "Step counter should start at 0"
    
    # Add events
    manager.add_event("First event")
    manager.add_event("Second event")
    
    assert len(manager.event_log) == 2, "Event log should have 2 events"
    assert manager.step_counter == 2, "Step counter should be 2"
    assert "Step 1:" in manager.event_log[0], "Event should be timestamped"
    assert "Step 2:" in manager.event_log[1], "Event should be timestamped"
    
    print("  ✓ DisruptionManager.add_event() tests passed\n")


def test_disruption_manager_trigger_no_fly():
    """Test no-fly zone triggering via DisruptionManager."""
    print("Testing DisruptionManager.trigger_no_fly()...")
    
    grid = create_sample_grid()
    manager = DisruptionManager()
    
    # Trigger no-fly
    manager.trigger_no_fly(grid, 7, 7)
    
    assert len(manager.event_log) == 1, "Event log should have 1 event"
    assert manager.step_counter == 1, "Step counter should be 1"
    
    cell = grid.get_cell(7, 7)
    assert cell is not None and cell.no_fly == True, "Cell should be marked as no-fly"
    
    print("  ✓ DisruptionManager.trigger_no_fly() tests passed\n")


def test_disruption_manager_check_and_reroute():
    """Test DisruptionManager's rerouting orchestration."""
    print("Testing DisruptionManager.check_and_reroute()...")
    
    grid = create_sample_grid()
    manager = DisruptionManager()
    
    # Create drones - one affected, one not
    drone_affected = Drone(
        id="D_AFFECTED",
        current_position=(0, 0),
        target=(5, 5),
        route=[(0, 0), (1, 1), (2, 2), (3, 6), (4, 4), (5, 5)],  # Hits no-fly at (3, 6)
        status="ACTIVE"
    )
    
    drone_safe = Drone(
        id="D_SAFE",
        current_position=(5, 0),
        target=(5, 9),
        route=[(5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9)],
        status="ACTIVE"
    )
    
    drones = [drone_affected, drone_safe]
    
    # Check and reroute
    manager.check_and_reroute(drones, grid)
    
    assert len(manager.event_log) >= 1, "Should have logged rerouting events"
    assert drone_affected.status == "ACTIVE", "Affected drone should be rerouted successfully"
    assert drone_safe.status == "ACTIVE", "Safe drone should remain ACTIVE"
    
    print("  ✓ DisruptionManager.check_and_reroute() tests passed\n")


def test_disruption_manager_print_event_log():
    """Test event log printing functionality."""
    print("Testing DisruptionManager.print_event_log()...")
    
    manager = DisruptionManager()
    manager.add_event("Test event 1")
    manager.add_event("Test event 2")
    manager.add_event("Test event 3")
    
    # Should not raise any exceptions
    manager.print_event_log()
    
    assert len(manager.event_log) == 3, "Should have 3 events"
    
    print("  ✓ DisruptionManager.print_event_log() tests passed\n")


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_disruption_workflow():
    """Integration test: Complete disruption detection and response workflow."""
    print("Testing full disruption workflow...")
    
    grid = create_sample_grid()
    manager = DisruptionManager()
    
    # Create drones
    drone1 = Drone(
        id="D1",
        current_position=(1, 1),
        target=(8, 8),
        route=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)],
        status="ACTIVE"
    )
    
    drone2 = Drone(
        id="D2",
        current_position=(0, 0),
        target=(9, 9),
        route=[(0, 0), (1, 1), (2, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 6), (9, 9)],
        status="ACTIVE"
    )
    
    drones = [drone1, drone2]
    
    # Workflow
    manager.trigger_no_fly(grid, 4, 7)
    manager.check_and_reroute(drones, grid)
    
    manager.trigger_no_fly(grid, 3, 6)
    manager.check_and_reroute(drones, grid)
    
    # Verify
    assert len(manager.event_log) >= 2, "Should have multiple events"
    assert all(d.status in ["ACTIVE", "DELAYED", "FAILED", "RETURNING"] for d in drones), \
        "All drones should have valid status"
    
    print("  ✓ Full disruption workflow tests passed\n")


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AeroNet Lite - Disruption Handler Unit Tests")
    print("=" * 70 + "\n")
    
    try:
        # Helper function tests
        test_is_no_fly()
        test_set_no_fly()
        
        # Core function tests
        test_activate_no_fly()
        test_route_contains_blocked_cell()
        test_reroute_drone_success()
        test_reroute_drone_failure()
        test_force_return_to_hub()
        
        # DisruptionManager tests
        test_disruption_manager_add_event()
        test_disruption_manager_trigger_no_fly()
        test_disruption_manager_check_and_reroute()
        test_disruption_manager_print_event_log()
        
        # Integration tests
        test_full_disruption_workflow()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)