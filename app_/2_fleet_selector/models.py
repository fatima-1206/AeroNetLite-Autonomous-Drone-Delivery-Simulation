# class of drone type which has name, cost, payload and range
@dataclass(frozen=True, slots=True)
class DroneType:
	name: str
	cost: int
	payload_kg: float
	max_range_cells: int

# class of fleet selection which has number of light and heavy drones, cost, total payload, coverage and score
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
    # dictionary of items to assign values with strings
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

