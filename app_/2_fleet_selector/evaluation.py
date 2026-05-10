
def estimate_total_demand(grid: Grid) -> float:
	"""Estimate the fleet demand requirement from the shared grid model."""
	# add the demand from every cell and divide by 1000
    return round(sum(cell.demand for cell in grid.iter_cells()) / 1000.0, 2)


def evaluate_fleet(
	light_drones: int, heavy_drones: int,*,budget: int,demand_kg: float,
) -> FleetSelection:
	# figure out the total bill and how much the fleet can carry
    total_cost = (light_drones * LIGHT_DRONE.cost) + (heavy_drones * HEAVY_DRONE.cost)
	total_payload = (light_drones * LIGHT_DRONE.payload_kg) + (heavy_drones * HEAVY_DRONE.payload_kg)
	# find the demand of what we are covering
    if demand_kg <= 0:
		coverage_percentage = 100.0
	else:
		coverage_percentage = min((total_payload / demand_kg) * 100.0, 100.0)
	# calculate how much budget we have eaten up
    budget_used_percentage = min((total_cost / budget) * 100.0, 999.0) if budget > 0 else 0.0
	# the fleet has a score, high coverage is valyed and spending too much is bad
    score = (0.75 * coverage_percentage) - (0.25 * budget_used_percentage)
	return FleetSelection(
		light_drones=light_drones,
		heavy_drones=heavy_drones,
		total_cost=total_cost,
		total_payload_kg=round(total_payload, 2),
		demand_kg=demand_kg,
		coverage_percentage=round(coverage_percentage, 2),
		budget_used_percentage=round(budget_used_percentage, 2),
		score=round(score, 2),
	)

# fix the candidates 
def repair_candidate(light_drones: int, heavy_drones: int, *, budget: int) -> tuple[int, int]:
	# dont allow negatives here
    light_drones = max(0, light_drones)
	heavy_drones = max(0, heavy_drones)
	# if over budget remove heavy drones if they cost more otherwise remove a light drone
    while ((light_drones * LIGHT_DRONE.cost) + (heavy_drones * HEAVY_DRONE.cost)) > budget:
		if heavy_drones > 0 and ((heavy_drones * HEAVY_DRONE.cost) >= (light_drones * LIGHT_DRONE.cost) or light_drones == 0):
			heavy_drones -= 1
		elif light_drones > 0:
			light_drones -= 1
		else:
            # nothing to remove so break
			break
	return light_drones, heavy_drones
