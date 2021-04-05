from dataclasses import dataclass

@dataclass
class ConnectionGene:
	in_node: int
	out_node: int
	weight: float
	innovation_num: int
	disabled: bool = False
