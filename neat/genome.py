import random
import copy
import time

from neat.connection_gene import ConnectionGene
from neat.neural_network import NeuralNetwork, NeuralConnection
from neat.parameters import *
from neat.innovation import Innovation

class Genome:
	def __init__(self, num_inputs, num_outputs, connections=None, connections_by_out=None, nodes=None):
		self.num_inputs = num_inputs
		self.num_outputs = num_outputs
		self.nodes = list(range(num_inputs + 1 + num_outputs)) # Additional bias node

		if connections is None or connections_by_out is None or nodes is None:
			self.connections = []
			self.connections_by_out = dict()

			innov_count = 0

			# # Create randomly-weighed connections between every in and out node
			# for j in range(num_outputs):
			# 	self.connections_by_out[num_inputs + 1 + j] = []
			# 	for i in range(num_inputs + 1):
			# 		in_node = i
			# 		out_node = num_inputs + 1 + j
			# 		weight = (random.random() * 2) - 1

			# 		conn = ConnectionGene(in_node, out_node, weight, innov_count)
			# 		self.connections.append(conn)
			# 		self.connections_by_out[num_inputs + 1 + j].append(conn)

			# 		# TODO: DOCUMENT
			# 		innov_count += 1
			for i in range(num_outputs):
				weight = random.random()
				conn = ConnectionGene(num_inputs, num_inputs + 1 + i, weight, innov_count)
				innov_count += 1

				self.connections.append(conn)
				self.connections_by_out[num_inputs + 1 + i] = [conn]
		else:
			self.connections = connections
			self.connections_by_out = connections_by_out
			self.nodes = nodes

	def clone(self):
		return copy.deepcopy(self)

	def mutate(self, cur_gen_innovations, global_innovation_counter, global_node_counter):
		"""
		Mutates the genome in-place
		TODO: document `cur_gen_innovations`
		"""

		# We choose to either do one of the topological mutations, or try to do some
		# weight mutations
		if random.random() < NODE_MUTATION_CHANCE:
			# We add a new node by choosing a random connection and splitting it in the middle using
			# a new node
			connection_to_split_idx = random.randrange(len(self.connections))
			connection_to_split = self.connections[connection_to_split_idx]

			# We first check if this exact mutation already happened in this generation, and if so,
			# reuse its innovation numbers to prevent 'innovation explosion'
			innovation_num_a = None
			innovation_num_b = None
			new_node = None
			for innov in cur_gen_innovations:
				if innov.is_node_mutation and innov.old_innov_num == connection_to_split.innovation_num:
					innovation_num_a = innov.new_innov_num
					innovation_num_b = innov.new_innov_num2
					new_node = innov.new_node_id
					break

			# If this is a novel mutation, we give it new innovation numbers and record it
			if innovation_num_a is None:
				innovation_num_a = global_innovation_counter.next_id()
				innovation_num_b = global_innovation_counter.next_id()

				new_node = global_node_counter.next_id()

				new_innov = Innovation(True, connection_to_split.innovation_num, None, None,
					innovation_num_a, innovation_num_b, new_node)
				cur_gen_innovations.append(new_innov)

			self.nodes.append(new_node)

			# TODO: BASICALLY REDONE, DOC!

			connection_to_split.disabled = True

			conn_a = ConnectionGene(connection_to_split.in_node, new_node, 1.0, innovation_num_a)
			conn_b = ConnectionGene(new_node, connection_to_split.out_node, connection_to_split.weight,
				innovation_num_b)

			# We append the new connections to the connection list
			self.connections.append(conn_a)
			self.connections.append(conn_b)
			# We add a new `connection_by_out` list for the new node, which currently contains only
			# the new connection
			self.connections_by_out[new_node] = [conn_a]

			self.connections_by_out[connection_to_split.out_node].append(conn_b)

		elif random.random() < LINK_MUTATION_CHANCE:
			# We first find the layer of each node, this will be used to make sure we don't create
			# any recurrent links
			node_layer = self.get_node_layers()

			# When picking completely random links, some links will be invalid. It is much simpler,
			# to just try a few times to find a valid link and bail if none are found. This should
			# not have significant effect: the genetic proccess is inherently random anyway.
			for _ in range(50):

				# An input/bias node cannot be used as an out node, because the nodes are ordered
				# [input, bias, output, hidden], we pick a random index that starts at the first
				# output node
				first_output_idx = self.num_inputs + 1
				out_node = self.nodes[random.randrange(first_output_idx, len(self.nodes))]

				# An output node cannot be used as an in node, because the nodes are ordered
				# [input, bias, output, hidden], we pick a random index out of the number of
				# not-output nodes.
				in_node_idx = random.randrange(len(self.nodes) - self.num_outputs)
				# Because output nodes come before hidden nodes, this means that the index actually
				# points to an output node if it is one of the hidden nodes, so we remap indexes
				# in the output range to point to the corresponding node in the hidden range.
				if self.num_inputs + 1 <= in_node_idx < first_output_idx + self.num_outputs:
					in_node_idx = len(self.nodes) - in_node_idx + self.num_inputs
				in_node = self.nodes[in_node_idx]

				# First we have to make sure that the connection we are creating is not a recurrent
				# connection, as we only support feed-forward networks
				if node_layer[in_node] <= node_layer[out_node] and in_node != out_node:
					# We then check if this connection already exists by iterating over all links
					# that go into the chosen `out_node`
					already_exists = False
					for conn in self.connections_by_out[out_node]:
						if not conn.disabled and conn.in_node == in_node:
							already_exists = True
							break

					# If this is a new link, than we can add it
					if not already_exists:
						# We initialize the link with a random weight
						weight = random.random()

						# We first check if this exact mutation already happened in this generation,
						# and if so, reuse its innovation numbers to prevent 'innovation explosion'
						innovation_num = None
						for innov in cur_gen_innovations:
							if not innov.is_node_mutation and innov.node_start_id == in_node and \
								innov.node_end_id == out_node:
								innovation_num = innov.new_innov_num
								break

						# If this is a novel mutation, we give it a new innovation number and record it
						if innovation_num is None:
							innovation_num = global_innovation_counter.next_id()

							new_innov = Innovation(False, None, in_node, out_node, innovation_num)
							cur_gen_innovations.append(new_innov)

						# Create the new connection
						new_connection = ConnectionGene(in_node, out_node, weight, innovation_num)
						self.connections.append(new_connection)
						self.connections_by_out[out_node].append(new_connection)

						# We found a valid link, so we don't have to keep retrying
						break
		elif random.random() < WEIGHT_MUTATION_CHANCE:
			# TODO: The paper's source code has many more kinds of non-topological mutations,
			# but the paper only mentions these two. Might be worth to try adding them.

			for conn in self.connections:
				if conn.disabled: continue
				# For each connection we either randomize it completely (rarely) or perturb it
				# slightly
				if random.random() < WEIGHT_RANDOMIZED_CHANCE:
					conn.weight = random.random()
				else:
					# TODO: Try with other values of sigma, or simple random, this is arbitary
					conn.weight += random.gauss(0, 0.3)

	def get_compatibility_distance(self, other):
		"""
		Calculates the 'compatibility distance' between this genome and `other`. Compatibility
		distance is defined to be a linear combination of the number of excess genes, the number of
		disjoint genes, and the average weight differences of matching genes.
		"""

		# The number of total genes to count is the maximum of the two
		gene_amount = max(len(self.connections), len(other.connections))
		excess_genes = 0
		disjoint_genes = 0
		matching_genes = 0
		weight_difference_sum = 0

		# We go through each connection gene, and check if they match
		gene_a = 0
		gene_b = 0
		while gene_a < len(self.connections) or gene_b < len(other.connections):
			# Excess genes are the genes which do not match in the end, so if we ran out of genes
			# in either genome, all the remaining genes are excess
			if gene_a == len(self.connections):
				if not other.connections[gene_b].disabled:
					excess_genes += 1
				gene_b += 1
			elif gene_b == len(other.connections):
				if not self.connections[gene_a].disabled:
					excess_genes += 1
				gene_a += 1
			else:
				if self.connections[gene_a].disabled:
					gene_a += 1
					continue

				if other.connections[gene_b].disabled:
					gene_b += 1
					continue

				# The matching of the genes is done based on the innovation numbers which are
				# essentially historical markings
				innovation_a = self.connections[gene_a].innovation_num
				innovation_b = other.connections[gene_b].innovation_num
				if innovation_a == innovation_b:
					# If the genes have the same innovation number, they match, and we calculate the
					# weight difference
					matching_genes += 1
					weight_a = self.connections[gene_a].weight
					weight_b = other.connections[gene_b].weight
					weight_difference_sum += abs(weight_a - weight_b)

					gene_a += 1
					gene_b += 1
				elif innovation_a < innovation_b:
					# If the numbers dont match up, then one of the genes is 'earlier' in history.
					# We rely on this fact, because the genes are sorted in the list based on
					# insertion time, so if a gene is older innovation wise, we know that we need
					# to advance the gene index in that genome
					disjoint_genes += 1
					gene_a += 1
				else:
					disjoint_genes += 1
					gene_b += 1
		
		if matching_genes == 0:
			print(self.connections, other.connections)
			assert False

		# The final distance is then calculated based on formula (1) from the paper
		distance_part_1 = COMPATABILITY_COEFFICIENT_1 * excess_genes
		distance_part_2 = COMPATABILITY_COEFFICIENT_2 * disjoint_genes
		distance_part_3 = COMPATABILITY_COEFFICIENT_3 * (weight_difference_sum / matching_genes)
		return distance_part_1 + distance_part_2 + distance_part_3

	def get_node_layers(self, node_id_normalization=None):
		"""
		Returns an array which maps each node in the genome to a layer number if the genome would be
		represented as a simple feed-forward neural network. # TODO: DOC
		"""

		# Initially the nodes do not have a layer assigned to them
		if node_id_normalization is not None:
			node_layer = [None] * len(self.nodes)
		else:
			node_layer = dict()

		# The input nodes and the bias node are the only nodes that we know the layer of initially
		for i in range(self.num_inputs + 1):
			node_layer[i] = 0

		# We then figure out the layer of the nodes by iterating over the nodes we didn't assign a
		# layer for yet. Because we do not allow recuring networks, there must be at least one node
		# we can figure out the layer of by finding the maximal layer which flows to that node.
		# It is not possible that every node has some node which flows into it and doesn't have an
		# assigned layer yet, else this implies that a loop exists in the network. Because of this
		# we know that after O(n) iterations (each one taking O(n) time) we will have figured out
		# the layer of every node, so in total this will take O(n^2) time.
		# TODO: This is slow - use BFS

		# This is the list of node indexes we did not asssign a layer to yet
		nodes_to_place = list(range(self.num_inputs + 1, len(self.nodes)))

		#FIXME: DEBUG
		start_t = time.time()

		while len(nodes_to_place) > 0:
			if time.time() - start_t > 1: # FIXME: DEBUG
				print(nodes_to_place, node_layer, self.nodes)
				print(self.connections)
				assert False

			# As long as we did not assign a layer to every node, we try to find a node which we
			# can assign a layer to
			for loc, node_idx in enumerate(nodes_to_place):
				node = self.nodes[node_idx]
				finalized = True
				max_prev_layer = 0

				# For each connection going into this node, we find if it goes out of a node whose
				# layer we have figured out already. If we did not, this node cannot be assigned a
				# layer yet, but if it did, then its layer must be at least one more than the
				# maximal layer of incoming nodes.
				if node not in self.connections_by_out:
					print(node)
					print(self.nodes)
					print(self.connections)
					print(self.connections_by_out)
					assert False
				for conn in self.connections_by_out[node]:
					if conn.disabled: continue
					try:
						if node_id_normalization is not None:
							if node_layer[node_id_normalization[conn.in_node]] is None:
								finalized = False
								break
							else:
								max_prev_layer = max(max_prev_layer, node_layer[node_id_normalization[conn.in_node]])
						else:
							if conn.in_node not in node_layer:
								finalized = False
								break
							else:
								max_prev_layer = max(max_prev_layer, node_layer[conn.in_node])
					except:
						print(self.nodes, conn, node_id_normalization, node_layer)
						assert False

				if finalized:
					# All incoming links are from finalized nodes, so we can assign the layer of
					# this node
					if node_id_normalization is not None:
						node_layer[node_id_normalization[node]] = max_prev_layer + 1
					else:
						node_layer[node] = max_prev_layer + 1
					nodes_to_place.pop(loc)
					break

		return node_layer

	def as_neural_network(self):
		"""
		Converts the genome into a simple feed-forward neural network
		"""

		# TODO: DOC
		node_id_normalization = dict()
		for idx, node in enumerate(self.nodes):
			node_id_normalization[node] = idx

		# We first figure out the layer of each node
		node_layer = self.get_node_layers(node_id_normalization)

		# We then need to convert the assignment from node to layer, to a network evaluation order
		# which ensures that a node is evalauted only if all incoming nodes have already been
		# evaluated
		evaluation_order = []
		try:
			last_layer = max(node_layer)
		except:
			print(node_layer) # FIXME: DEBUG
			exit()

		for layer_idx in range(1, last_layer + 1):
			# For each layer, we add all nodes that belong to it to the evaluation order
			for node, layer in enumerate(node_layer):
				if layer == layer_idx:
					evaluation_order.append(node)

		# We then generate a connections representation which is useful for network evaluation:
		# For each node we supply a list of connections which go into it
		network_connections = [None]*len(self.nodes)
		for node_id in self.connections_by_out:
			normal_node_id = node_id_normalization[node_id]
			node_conns = self.connections_by_out[node_id]
			network_connections[normal_node_id] = []

			if node_conns is not None:
				for conn in node_conns:
					if conn.disabled: continue
					neural_conn = NeuralConnection(node_id_normalization[conn.in_node], conn.weight)
					network_connections[normal_node_id].append(neural_conn)

		# Construct the neural network
		return NeuralNetwork(self.num_inputs, self.num_outputs, evaluation_order, network_connections)

	@staticmethod
	def from_crossover(parent_a, parent_b):

		"""
		self.num_inputs = num_inputs
		self.num_outputs = num_outputs
		self.nodes = ...

		self.connections = []
		self.connections_by_out = [None] * (num_inputs + 1)
		"""

		# TODO: DOC DOC DOC
		genome_a = parent_a.genome
		genome_b = parent_b.genome

		connections = []
		connections_by_out = dict()
		nodes = nodes = list(range(genome_a.num_inputs + 1 + genome_a.num_outputs))

		parent_a_better = parent_a.fitness > parent_b.fitness
		if parent_a.fitness == parent_b.fitness:
			# We break fitness ties by picking the smaller parent to incentivize simpler networks
			parent_a_better = len(genome_a.connections) < len(genome_b.connections)

		gene_a = 0
		gene_b = 0
		while gene_a < len(genome_a.connections) or gene_b < len(genome_b.connections):
			# Excess genes are the genes which do not match in the end, so if we ran out of genes
			# in either genome, all the remaining genes are excess
			if gene_a == len(genome_a.connections):
				if parent_a_better:
					break
				new_gene = genome_b.connections[gene_b]
				gene_b += 1
				if new_gene.disabled:
					continue
			elif gene_b == len(genome_b.connections):
				if not parent_a_better:
					break
				new_gene = genome_a.connections[gene_a]
				gene_a += 1
				if new_gene.disabled:
					continue
			else:
				if genome_a.connections[gene_a].disabled:
					gene_a += 1
					continue
				if genome_b.connections[gene_b].disabled:
					gene_b += 1
					continue

				# The matching of the genes is done based on the innovation numbers which are
				# essentially historical markings
				innovation_a = genome_a.connections[gene_a].innovation_num
				innovation_b = genome_b.connections[gene_b].innovation_num
				if innovation_a == innovation_b:
					if random.random() < 0.5:
						new_gene = genome_a.connections[gene_a]
					else:
						new_gene = genome_b.connections[gene_b]

					gene_a += 1
					gene_b += 1
				elif innovation_a < innovation_b:
					new_gene = genome_a.connections[gene_a]
					# If the numbers dont match up, then one of the genes is 'earlier' in history.
					# We rely on this fact, because the genes are ordered in the list based on
					# insertion time, so if a gene is older innovation wise, we know that we need
					# to advance the gene index in that genome
					gene_a += 1

					if not parent_a_better:
						continue
				else:
					new_gene = genome_b.connections[gene_b]
					gene_b += 1

					if parent_a_better:
						continue

			new_gene = copy.deepcopy(new_gene) # NOTE: If connections are shared disabling is shared!!!
			connections.append(new_gene)
			if new_gene.out_node in connections_by_out:
				connections_by_out[new_gene.out_node].append(new_gene)
			else:
				connections_by_out[new_gene.out_node] = [new_gene]

			if new_gene.in_node not in nodes:
				nodes.append(new_gene.in_node)
			if new_gene.out_node not in nodes:
				nodes.append(new_gene.out_node)

		return Genome(genome_a.num_inputs, genome_a.num_outputs, connections, connections_by_out, nodes)
