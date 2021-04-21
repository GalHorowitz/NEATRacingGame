import math

class NeuralConnection:
	def __init__(self, in_node, weight):
		self.in_node = in_node
		self.weight = weight
	
	def __repr__(self):
		return f'NeuralConnection(in_node={self.in_node}, weight={self.weight})'

class NeuralNetwork:
	def __init__(self, num_inputs, num_outputs, evaluation_order, connections):
		self.num_inputs = num_inputs
		self.num_outputs = num_outputs

		# The evaluation order contains all hidden and output nodes, so we add the number of inputs
		# and the bias node to get the total node count
		self.num_nodes = len(evaluation_order) + num_inputs + 1

		# The evaluation order is a list of node indices which ensures that a node is evaluated only
		# after all its incoming nodes have been evaluated already
		self.evaluation_order = evaluation_order

		# `connections` is a 2D list, which holds the list of connections that go into each node
		self.connections = connections
	
	def __repr__(self):
		return f'NeuralNetwork(num_inputs={self.num_inputs}, num_outputs={self.num_outputs}, evaluation_order={repr(self.evaluation_order)}, connections={repr(self.connections)})'

	def evaluate_input(self, network_input):
		"""
		Feeds the input `network_input` through the network and returns an array of the values of
		the output nodes.
		"""

		# Holds the values of the nodes
		node_values = [None]*self.num_nodes

		# The values of the input nodes are the inputs
		for i in range(self.num_inputs):
			node_values[i] = network_input[i]
		# The value of the bias node is always 1
		node_values[self.num_inputs] = 1

		# We then evaluate each node according to the evaluation order, which ensures that a node is
		# evaluated only after all its incoming nodes have been evaluated already
		for node in self.evaluation_order:
			# Calculate the weighted sum of the node
			node_sum = 0
			for conn in self.connections[node]:
				node_sum += node_values[conn.in_node]*conn.weight

			# Set the node value of the weighted sum passed through the activation function
			node_values[node] = sigmoid(node_sum)

		# The order of nodes is always [inputs, bias, outputs, hidden], so this slice of the node
		# values is exactly the output values
		return node_values[self.num_inputs+1:][:self.num_outputs]

def sigmoid(x):
	return (2/(1 + math.exp(-4.9 * x)))-1
