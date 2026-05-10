""" consonants for light drone, heavy drone and drone types"""

LIGHT_DRONE = DroneType(name="Light Drone", cost=1000, payload_kg=2.0, max_range_cells=12)
HEAVY_DRONE = DroneType(name="Heavy Drone", cost=1800, payload_kg=5.0, max_range_cells=20)
DRONE_TYPES = (LIGHT_DRONE, HEAVY_DRONE)
