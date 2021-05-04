from dataclasses import dataclass

@dataclass
class NeuralConnection:
	# The id of the node this connection comes out of
	in_node: int

	# The weight of this connection
	weight: float
