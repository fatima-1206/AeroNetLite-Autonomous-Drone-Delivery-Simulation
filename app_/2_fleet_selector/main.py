"""Genetic-algorithm fleet selector for AeroNet Lite.

The module keeps the chromosome intentionally small: each candidate fleet is a
pair of integers representing the number of light drones and heavy drones.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import sys
from pathlib import Path
from typing import Iterable, Literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app_.shared_utils.main import Grid, create_sample_grid


@dataclass(frozen=True, slots=True)
class DroneType:
	name: str
	cost: int
	payload_kg: float
	max_range_cells: int


@dataclass(frozen=True, slots=True)
class FleetSelection:
	light_drones: int
	heavy_drones: int
	total_cost: int
	total_payload_kg: float
	demand_kg: float
	coverage_percentage: float
	budget_used_percentage: float
	score: float

	@property
	def counts(self) -> tuple[int, int]:
		return self.light_drones, self.heavy_drones

	def to_dict(self) -> dict[str, float | int]:
		return {
			"light_drones": self.light_drones,
			"heavy_drones": self.heavy_drones,
			"total_cost": self.total_cost,
			"total_payload_kg": self.total_payload_kg,
			"demand_kg": self.demand_kg,
			"coverage_percentage": self.coverage_percentage,
			"budget_used_percentage": self.budget_used_percentage,
			"score": self.score,
		}


LIGHT_DRONE = DroneType(name="Light Drone", cost=1000, payload_kg=2.0, max_range_cells=12)
HEAVY_DRONE = DroneType(name="Heavy Drone", cost=1800, payload_kg=5.0, max_range_cells=20)
DRONE_TYPES = (LIGHT_DRONE, HEAVY_DRONE)
SelectionMethod = Literal["ga", "bf"]


def estimate_total_demand(grid: Grid) -> float:
	"""Estimate the fleet demand requirement from the shared grid model."""
	return round(sum(cell.demand for cell in grid.iter_cells()) / 1000.0, 2)


def evaluate_fleet(
	light_drones: int,
	heavy_drones: int,
	*,
	budget: int,
	demand_kg: float,
) -> FleetSelection:
	total_cost = (light_drones * LIGHT_DRONE.cost) + (heavy_drones * HEAVY_DRONE.cost)
	total_payload = (light_drones * LIGHT_DRONE.payload_kg) + (heavy_drones * HEAVY_DRONE.payload_kg)
	if demand_kg <= 0:
		coverage_percentage = 100.0
	else:
		coverage_percentage = min((total_payload / demand_kg) * 100.0, 100.0)
	budget_used_percentage = min((total_cost / budget) * 100.0, 999.0) if budget > 0 else 0.0
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


def repair_candidate(light_drones: int, heavy_drones: int, *, budget: int) -> tuple[int, int]:
	light_drones = max(0, light_drones)
	heavy_drones = max(0, heavy_drones)
	while ((light_drones * LIGHT_DRONE.cost) + (heavy_drones * HEAVY_DRONE.cost)) > budget:
		if heavy_drones > 0 and ((heavy_drones * HEAVY_DRONE.cost) >= (light_drones * LIGHT_DRONE.cost) or light_drones == 0):
			heavy_drones -= 1
		elif light_drones > 0:
			light_drones -= 1
		else:
			break
	return light_drones, heavy_drones


def _random_candidate(*, rng: random.Random, budget: int) -> tuple[int, int]:
	max_light = budget // LIGHT_DRONE.cost
	max_heavy = budget // HEAVY_DRONE.cost
	light_drones = rng.randint(0, max_light)
	heavy_drones = rng.randint(0, max_heavy)
	return repair_candidate(light_drones, heavy_drones, budget=budget)


def initialize_population(*, population_size: int, budget: int, rng: random.Random) -> list[tuple[int, int]]:
	return [_random_candidate(rng=rng, budget=budget) for _ in range(population_size)]


def select_parent(population: list[tuple[int, int]], fitnesses: list[float], *, rng: random.Random) -> tuple[int, int]:
	"""Tournament selection keeps the implementation simple and stable."""
	first = rng.randrange(len(population))
	second = rng.randrange(len(population))
	return population[first] if fitnesses[first] >= fitnesses[second] else population[second]


def crossover(parent_a: tuple[int, int], parent_b: tuple[int, int], *, rng: random.Random) -> tuple[int, int]:
	return (
		parent_a[0] if rng.random() < 0.5 else parent_b[0],
		parent_a[1] if rng.random() < 0.5 else parent_b[1],
	)


def mutate(candidate: tuple[int, int], *, rng: random.Random, mutation_rate: float) -> tuple[int, int]:
	light_drones, heavy_drones = candidate
	if rng.random() < mutation_rate:
		light_drones += rng.choice((-1, 1))
	if rng.random() < mutation_rate:
		heavy_drones += rng.choice((-1, 1))
	return light_drones, heavy_drones


def _population_fitness(
	population: Iterable[tuple[int, int]],
	*,
	budget: int,
	demand_kg: float,
) -> list[float]:
	return [evaluate_fleet(light, heavy, budget=budget, demand_kg=demand_kg).score for light, heavy in population]


def brute_force_select_fleet(*, budget: int, demand_kg: float) -> FleetSelection:
	"""Exhaustively evaluate all feasible light/heavy combinations."""
	max_light = budget // LIGHT_DRONE.cost
	max_heavy = budget // HEAVY_DRONE.cost
	best_selection = evaluate_fleet(0, 0, budget=budget, demand_kg=demand_kg)
	best_key = (best_selection.score, best_selection.coverage_percentage, -best_selection.total_cost)

	for light_drones in range(max_light + 1):
		for heavy_drones in range(max_heavy + 1):
			selection = evaluate_fleet(light_drones, heavy_drones, budget=budget, demand_kg=demand_kg)
			if selection.total_cost > budget:
				continue
			current_key = (selection.score, selection.coverage_percentage, -selection.total_cost)
			if current_key > best_key:
				best_selection = selection
				best_key = current_key

	return best_selection


def select_fleet(
	grid: Grid | None = None,
	*,
	budget: int = 10_000,
	population_size: int = 30,
	generations: int = 40,
	mutation_rate: float = 0.2,
	random_seed: int | None = None,
	method: SelectionMethod = "ga",
) -> FleetSelection:
	"""Return the best fleet using either GA search or brute force."""
	active_grid = grid if grid is not None else create_sample_grid()
	demand_kg = estimate_total_demand(active_grid)
	if method == "bf":
		return brute_force_select_fleet(budget=budget, demand_kg=demand_kg)

	rng = random.Random(random_seed)
	population = initialize_population(population_size=population_size, budget=budget, rng=rng)
	best_selection = evaluate_fleet(0, 0, budget=budget, demand_kg=demand_kg)

	for _ in range(generations):
		fitnesses = _population_fitness(population, budget=budget, demand_kg=demand_kg)
		current_best_index = max(range(len(population)), key=fitnesses.__getitem__)
		current_best = evaluate_fleet(*population[current_best_index], budget=budget, demand_kg=demand_kg)
		if current_best.score > best_selection.score:
			best_selection = current_best

		next_population: list[tuple[int, int]] = [population[current_best_index]]
		while len(next_population) < population_size:
			parent_a = select_parent(population, fitnesses, rng=rng)
			parent_b = select_parent(population, fitnesses, rng=rng)
			child = crossover(parent_a, parent_b, rng=rng)
			child = mutate(child, rng=rng, mutation_rate=mutation_rate)
			child = repair_candidate(*child, budget=budget)
			next_population.append(child)
		population = next_population

	return best_selection


def run_demo(method: SelectionMethod | None = None) -> None:
	if method is not None:
		selected_method: SelectionMethod = method
	else:
		raw_method = sys.argv[1] if len(sys.argv) > 1 else "ga"
		if raw_method == "ga":
			selected_method = "ga"
		elif raw_method == "bf":
			selected_method = "bf"
		else:
			raise ValueError('method must be "ga" or "bf"')
	selection = select_fleet(random_seed=7, method=selected_method)
	print(f"Selected fleet using {selected_method}:", selection.to_dict())


if __name__ == "__main__":
	run_demo()
