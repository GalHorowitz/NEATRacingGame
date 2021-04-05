from neat.genome import Genome
from neat.organism import Organism
from neat.species import Species
from neat.unique_id import UniqueId
from neat.parameters import *

class Population:
	def __init__(self, population_size, num_inputs, num_outputs):
		self.population_size = population_size

		self.organisms = []
		for _ in range(population_size):
			self.organisms.append(Organism(Genome(num_inputs, num_outputs)))

		self.global_innovation_counter = UniqueId((num_inputs + 1) * num_outputs) # TODO: DOCUMENT
		self.global_node_counter = UniqueId(num_inputs + 1 + num_outputs)

		self.species = []

	def speciate(self):
		"""
		Seperates the organisms in the population into species
		"""

		# We first remove the organisms attached to each species from the last generation,
		# but we do not remove the the representative of each species from the last generation
		for species in self.species:
			species.organisms.clear()

		for organism in self.organisms:
			# For each organism we try to find a species whose representative is close enough
			found_species = False
			for s_idx, species in enumerate(self.species):
				# Calculate how compatible the species representative is to our organism
				compat_dist = organism.genome.get_compatibility_distance(species.representative)
				if compat_dist < SPECIATION_THRESHOLD:
					# If it is below the threshold, then the organism belongs to this species
					found_species = True
					species.organisms.append(organism)
					organism.species = s_idx
					break

			if not found_species:
				# If this organism is different enough such that it is not compatible with any of
				# the existing species, we create a new species with the organism as the
				# representative
				organism.species = len(self.species)
				self.species.append(Species(organism))
		
		# Remove species which have no organisms in this population. We iterate backwards so we can
		# delete from the list while iterating
		for i in range(len(self.species)-1, -1, -1):
			if len(self.species[i].organisms) == 0:
				self.species.pop(i)

	def epoch(self):
		"""
		Advances the population one generation
		"""

		# We first seperate the organisms into species
		self.speciate()

		# Within each species we sort the organisms by fitness
		for species in self.species:
			species.rank_organisms()

		# We then sort the species by the fitness of the most fit organism in each species
		self.species.sort(key=lambda x: x.organisms[0].fitness, reverse=True)

		# TODO: Flag lowest performing species over age 20 every 30 generations (Competitive coevolution)

		for species in self.species:
			# For each species, we adjust the fitness of all its organisms based on some factors
			species.adjust_fitness()


		average_fitness = self.calc_average_fitness()
		for organism in self.organisms:
			# For each organism, the proportion of expected offstring is the ratio between its
			# fitness and the average fitness across the entire population. This way offspring is
			# distributed with proprtion to fitness.
			organism.expected_offspring = organism.adjusted_fitness/average_fitness

		total_expected_offspring = 0
		fractional_leftover = 0
		for species in self.species:
			# For each species, calculate the expected offstring given the last leftover, and update
			# it to the new leftover
			fractional_leftover = species.calculate_expected_offspring(fractional_leftover)
			# Add the the offstring to the total count
			total_expected_offspring += species.expected_offspring

		# Remove species which had no offspring. We do this by iterating over the array backwards so
		# we can delete species as we are iterating
		for i in range(len(self.species)-1, -1, -1):
			if self.species[i].expected_offspring == 0:
				self.species.pop(i)

		# Check if the fractional distribution of children led to less offspring than the size of
		# the population
		if total_expected_offspring < self.population_size:
			# Find the 'best' species, i.e. the species which expects most offspring
			max_expected = 0
			best_species = 0
			for s_idx, species in enumerate(self.species):
				if max_expected < species.expected_offspring:
					max_expected = species.expected_offspring
					best_species = s_idx

			# Add the extra child to the best species
			self.species[best_species].expected_offspring += self.population_size - total_expected_offspring

		# TODO: Population-level stagnation

		new_generation = []
		cur_gen_innovations = []
		for species in self.species:
			# For each species, we eliminate the organisms unfit to be parents
			species.eliminate_unfit()

			new_generation.extend(species.reproduce(self, cur_gen_innovations))

			# age species
			# regenerate species list
			# clear species state

		self.organisms = [Organism(genome) for genome in new_generation]

		"""
		1. If the maximum fitness of a species did not improve in 15 generations, the networks in
		the stagnant species were not allowed to reproduce.

		2. The champion of each species with more than five networks was copied into the next
		generation unchanged.

		3. Every species is assigned a potentially different number of offspring in proportion to
		the sum of adjusted fitnesses f'_i of its member organisms. Species then reproduce by first
		eliminating the lowest performing members from the population. The entire population is then
		replaced by the offspring of the remaining organisms in each species.

		4. In rare cases when the fitness of the entire population does not improve for more than 20
		generations, only the top two species are allowed to reproduce, refocusing the search into
		the most promising spaces.
		"""

	def calc_average_fitness(self):
		"""
		Calculates the average (adjusted) fitness across all organisms in the population
		"""
		total_fitness = 0
		for organism in self.organisms:
			total_fitness += organism.adjusted_fitness

		return total_fitness/self.population_size
