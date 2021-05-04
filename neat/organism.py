from dataclasses import dataclass
from neat.genome import Genome

@dataclass
class Organism:
	# The genome that this organism uses
	genome: Genome

	# The fitness of the organism, initially None, assigned post-simulation
	fitness: float = None

	# The adjusted `shared` fitness of the organism
	adjusted_fitness: float = None

	# The number of expected offspring based on the adjusted fitness
	expected_offspring: int = None
