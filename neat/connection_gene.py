from dataclasses import dataclass

@dataclass
class ConnectionGene:
	# The id of the node this connection comes out of
	in_node: int

	# The id of the node this connection enters
	out_node: int

	# The weight of this connection
	weight: float

	# The number of the innovation this connection was created in
	innovation_num: int

	# Whether or not this connection is disabled: by default it is enabled
	disabled: bool = False
