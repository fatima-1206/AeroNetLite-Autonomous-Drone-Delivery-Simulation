import heapq

def astar(start, goal, grid):

    # Check if start or goal is blocked
    if grid.is_blocked(start[0], start[1]) or grid.is_blocked(goal[0], goal[1]):
        return [], float('inf'), False

    # Directions: right, down, left, up
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    # Heuristic: Manhattan distance scaled by minimum step cost
    def heuristic(a, b):
        return (abs(a[0] - b[0]) + abs(a[1] - b[1])) * 0.8

    # Priority queue: (f_score, state)
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), start))

    # g_score: state -> cost from start
    g_score = {start: 0}

    # parent: state -> previous state
    parent = {start: None}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = []
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()
            return path, g_score[goal], True

        for dr, dc in directions:
            nr, nc = current[0] + dr, current[1] + dc
            if grid.in_bounds(nr, nc) and not grid.is_blocked(nr, nc):
                tentative_g = g_score[current] + grid.move_cost(nr, nc)
                if tentative_g < g_score.get((nr, nc), float('inf')):
                    g_score[(nr, nc)] = tentative_g
                    parent[(nr, nc)] = current
                    f_score = tentative_g + heuristic((nr, nc), goal)
                    heapq.heappush(open_set, (f_score, (nr, nc)))

    # No path found
    return [], float('inf'), False

def plan_delivery_route(hub, pickup, dropoff, grid):

    segments = []
    total_cost = 0.0

    # Segment 1: hub -> pickup
    path1, cost1, success1 = astar(hub, pickup, grid)
    if not success1:
        print("Error: No path found from hub to pickup")
        return None
    segments.append(path1)
    total_cost += cost1

    # Segment 2: pickup -> dropoff
    path2, cost2, success2 = astar(pickup, dropoff, grid)
    if not success2:
        print("Error: No path found from pickup to dropoff")
        return None
    segments.append(path2)
    total_cost += cost2

    # Segment 3: dropoff -> hub
    path3, cost3, success3 = astar(dropoff, hub, grid)
    if not success3:
        print("Error: No path found from dropoff to hub")
        return None
    segments.append(path3)
    total_cost += cost3

    return {
        "segments": segments,
        "total_cost": total_cost,
        "success": True
    }