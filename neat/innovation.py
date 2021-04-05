from dataclasses import dataclass

@dataclass
class Innovation:
	# Whether this is a node mutation or a link mutation
	is_node_mutation: bool

	# For node innovations
	old_innov_num: int

	# For link innovations
	node_start_id: int
	node_end_id: int

	# The innovation number assigned to this mutation
	new_innov_num: int
	new_innov_num2: int = None # For node mutation (two new links)

	# The id assigned to the new node in a node innovation
	new_node_id: int = None
