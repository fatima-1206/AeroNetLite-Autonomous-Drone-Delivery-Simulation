
# this function is the brute force implementation to find the best selection of fleets
# it evaluates all feasible combinations of light and heavy fleets
def brute_force_select_fleet(*, budget: int, demand_kg: float) -> FleetSelection:
	"""Exhaustively evaluate all feasible light and/or heavy combinations."""
	# find the max num of drones we could have if we only had one type
    max_light = budget // LIGHT_DRONE.cost
	max_heavy = budget // HEAVY_DRONE.cost
    # start with a baseline to have something to compare against
	best_selection = evaluate_fleet(0, 0, budget=budget, demand_kg=demand_kg)
	# rank fleets by score and coverage and lowest cost
    best_key = (best_selection.score, best_selection.coverage_percentage, -best_selection.total_cost)

    # now try every possible combination to find the best one
	for light_drones in range(max_light + 1):
		for heavy_drones in range(max_heavy + 1):
			selection = evaluate_fleet(light_drones, heavy_drones, budget=budget, demand_kg=demand_kg)
			if selection.total_cost > budget:
				continue
			current_key = (selection.score, selection.coverage_percentage, -selection.total_cost)
			if current_key > best_key:
				best_selection = selection
				best_key = current_key
    # return the best combination
	return best_selection
