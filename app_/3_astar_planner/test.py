# Test cases for A* implementation
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
APP_DIR = MODULE_DIR.parent

sys.path.insert(0, str(APP_DIR))

from shared_utils.main import create_sample_grid
from main import astar, plan_delivery_route

def test_basic_astar():
    """Test basic A* functionality."""
    grid = create_sample_grid()

    # Test 1 is to check Simple adjacent cells
    start = (0, 0)
    goal = (0, 1)
    path, cost, success = astar(start, goal, grid)
    print(f"Test 1 - Adjacent: Success={success}, Cost={cost}, Path={path}")
    assert success == True
    assert cost == 1.0  # Residential to Residential
    assert path == [(0, 0), (0, 1)]

    # Test 2 Through commercial corridor
    start = (0, 2)  # Commercial
    goal = (0, 3)  # Commercial
    path, cost, success = astar(start, goal, grid)
    print(f"Test 2 - Commercial: Success={success}, Cost={cost}, Path={path}")
    assert success == True
    assert cost == 0.8  # Commercial to Commercial

    # Test 3 is to check Blocked cell
    start = (0, 0)
    goal = (3, 6)  # No-fly zone
    path, cost, success = astar(start, goal, grid)
    print(f"Test 3 - Blocked goal: Success={success}, Cost={cost}, Path={path}")
    assert success == False
    assert cost == float('inf')
    assert path == []

    print("All basic A* tests passed!")

def test_plan_delivery():
    """Test the full delivery route planning."""
    grid = create_sample_grid()

    hub = (0, 0)
    pickup = (1, 1)
    dropoff = (2, 2)

    result = plan_delivery_route(hub, pickup, dropoff, grid)

    print(f"Delivery test: Success={result['success'] if result else False}")
    if result:
        print(f"Total cost: {result['total_cost']}")
        for i, path in enumerate(result['segments']):
            print(f"Segment {i+1}: {len(path)} steps")

        # Verify costs add up
        total_calc = sum(sum(grid.move_cost(r, c) for r, c in path[1:]) for path in result['segments'])
        print(f"Calculated total: {total_calc}, Reported: {result['total_cost']}")
        assert abs(total_calc - result['total_cost']) < 0.01

    print("Delivery route test passed!")

if __name__ == "__main__":
    test_basic_astar()
    test_plan_delivery()
    print("All tests passed")