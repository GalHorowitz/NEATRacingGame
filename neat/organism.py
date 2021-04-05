from dataclasses import dataclass
from neat.genome import Genome

@dataclass
class Organism:
	genome: Genome
	fitness: float = None
	adjusted_fitness: float = None
	expected_offspring: int = None
