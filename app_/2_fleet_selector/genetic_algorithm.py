""" Implementation of genetic algorithm """


# the initial population has random drone combos
def initialize_population(*, population_size: int, budget: int, rng: random.Random) -> list[tuple[int, int]]:
	return [_random_candidate(rng=rng, budget=budget) for _ in range(population_size)]

# select parent using tournament selection (the better one wins out of two)
def select_parent(population: list[tuple[int, int]], fitnesses: list[float], *, rng: random.Random) -> tuple[int, int]:
	"""Tournament selection keeps the implementation simple and stable."""
	# pick two parents and let them fight - survival of the fittest
    first = rng.randrange(len(population))
	second = rng.randrange(len(population))
	return population[first] if fitnesses[first] >= fitnesses[second] else population[second]

# crossover of genes to make a ~cute~ no better baby
def crossover(parent_a: tuple[int, int], parent_b: tuple[int, int], *, rng: random.Random) -> tuple[int, int]:
	return (
		parent_a[0] if rng.random() < 0.5 else parent_b[0],
		parent_a[1] if rng.random() < 0.5 else parent_b[1],
	)

# genes change randomly to ensure variation in baby 
def mutate(candidate: tuple[int, int], *, rng: random.Random, mutation_rate: float) -> tuple[int, int]:
	light_drones, heavy_drones = candidate
	if rng.random() < mutation_rate:
		light_drones += rng.choice((-1, 1))
	if rng.random() < mutation_rate:
		heavy_drones += rng.choice((-1, 1))
	return light_drones, heavy_drones

# check for fitness of fleet using fitness function
def _population_fitness(
	population: Iterable[tuple[int, int]],
	*,
	budget: int,
	demand_kg: float,
) -> list[float]:
	return [evaluate_fleet(light, heavy, budget=budget, demand_kg=demand_kg).score for light, heavy in population]

# the whole genetic algorithm implemented here to select fleet
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
    # keep reproducing for specific amount of generations (set to 40)
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

