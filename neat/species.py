import random
import math

from neat.genome import Genome
from neat.parameters import *

class Species:
	def __init__(self, representative_organism, global_species_counter):
		self.id = global_species_counter.next_id()
		self.representative = representative_organism.genome
		self.organisms = [representative_organism]

		self.expected_offspring = None

	def rank_organisms(self):
		"""
		Sorts the organisms in the species from the most fit to the least fit
		"""

		self.organisms.sort(key=lambda x: x.fitness, reverse=True)

	def adjust_fitness(self):
		"""
		Calculates an adjusted fitness for each organism in the species which takes into account
		different factors which should contribute to faster growth
		"""

		for organism in self.organisms:
			# For each organism in the species we calculate the 'shared' fitness
			organism.adjusted_fitness = organism.fitness / len(self.organisms)

	def eliminate_unfit(self):
		"""
		Discards all organisms in this species whose fitness lands them below the
		`SURVIVAL_THRESHOLD`. Assumption: organisms are already sorted by fitness.
		"""

		# Calculate the number of organisms that will survive to have offspring, adding 1 ensures
		# that at least one will survive
		num_parents = math.floor(SURVIVAL_THRESHOLD * len(self.organisms)) + 1

		# We then only keep the `num_parents` most fit organisms in the species (organisms are
		# already sorted by fitness)
		self.organisms = self.organisms[:num_parents]

	def calculate_expected_offspring(self, fractional_leftover):
		"""
		Calculates the total expected offspring of this species, the result is stored internally.
		The parameter `fractional_leftover` is the fractional (<1) carry from previous species,
		which can be used by this species to complete a fractional amount.
		The return value is the next fractional carry.
		"""

		# The purpose of a fractional carry is to 'spread' the extras across all species, and not
		# just add all the extra fractional parts to the best species at the end

		# Calculate the sum of expected offstring for each organism in the species
		expected_offspring = 0
		for organism in self.organisms:
			expected_offspring += organism.expected_offspring

		# This is the fractional part of the number of expected offspring
		fractional_part = expected_offspring - math.floor(expected_offspring)
		# Check if combining the fractional part with the fractional leftover results in an extra
		# offspring
		if fractional_leftover + fractional_part > 1:
			# Add an extra offspring
			expected_offspring += 1
			# Update the fractional leftover
			fractional_leftover = fractional_leftover + fractional_part - 1

		# Store the total number of expected offstring
		self.expected_offspring = math.floor(expected_offspring)

		# Return the carry
		return fractional_leftover

	def choose_parent_proportionally(self, total_fitness):
		"""
		Choose a random parent with a greater chance for more fit parents. This is done based on a
		'roulette wheel' method, where the slot's width is proportional to the relative fitness.
		The returned value is the index of the organism in the `organisms` list.
		"""

		# This is the 'spinning' of the wheel: We choose the point along the entire fitness spectrum
		# where the ball lands
		ball_land_point = random.random() * total_fitness

		# We then go through the wheel to find which organism's slot the ball landed in
		cur_organism_index = 0
		accumulated_fitness = self.organisms[0].fitness
		while accumulated_fitness < ball_land_point:
			# While the ball land point is still beyond the end of the current slot, we go on to the
			# next organism slot
			cur_organism_index += 1
			accumulated_fitness += self.organisms[cur_organism_index].fitness

		return cur_organism_index

	def reproduce(self, population, cur_gen_innovations):
		"""
		Generates the species' organisms' expected number of offspring.
		Assumption: The species in the population are sorted by fitness, the organisms in each
		species are sorted by fitness.
		"""

		offspring = []

		# We compute the total fitness once for use during reproduction
		total_fitness = 0
		for organism in self.organisms:
			total_fitness += organism.fitness

		for i in range(self.expected_offspring):
			if i == 0 and self.expected_offspring > 5:
				# If we expect more than 5 offspring, we want to ensure that the champion is carried
				# over to the next generation, so the first offspring is just a clone of the champion
				offspring.append(self.organisms[0].genome.clone())

			elif len(self.organisms) == 1 or random.random() < MUTATION_ONLY_OFFSPRING:
				# We decide by chance if we want to produce the next generation by mutating the
				# parents, or by cross-over. If there is only one parent, we can't cross-over anyway

				# We choose the parent to mutate
				parent_index = self.choose_parent_proportionally(total_fitness)
				# And then clone and mutate it
				mutated_offspring = self.organisms[parent_index].genome.clone()
				mutated_offspring.mutate(cur_gen_innovations, population.global_innovation_counter, population.global_node_counter)
				offspring.append(mutated_offspring)

			else:
				# In this case we want to cross over, so we need to pick two parents
				first_parent = self.organisms[self.choose_parent_proportionally(total_fitness)]

				# Check that there are other species, and roll the dice to decide if we do
				# inter-species mating
				if len(population.species) > 1 and random.random() < INTERSPECIES_MATING_RATE:
					# In the (rare) case the cross over is inter-species, we need to pick a parent
					# from the entire population, we first choose a random species
					# We just try a to pick a random species a few times to get a random species
					# which is not us: if we fail, this will just result in intra-species mating
					# which is fine. (The likelyhood of that is small)
					for _ in range(6):
						other_species = random.choice(population.species)
						if other_species.id == self.id:
							continue

					# We pick the most fit parent from the other species
					second_parent = other_species.organisms[0]
				else:
					# This is intra-species mating, so we just pick a second parent normally
					second_parent = self.organisms[self.choose_parent_proportionally(total_fitness)]

				new_offspring = Genome.from_crossover(first_parent, second_parent)

				# We also decide by chance if to further mutate the result of the crossover. In the
				# case we randomly picked the same parent twice, we always mutate (we detect this by
				# checking if the compatability distance between the parents is zero)
				parent_compat_dist = first_parent.genome.get_compatibility_distance(second_parent.genome)
				if random.random() < MUTATION_AFTER_CROSSOVER or parent_compat_dist == 0:
					new_offspring.mutate(cur_gen_innovations, population.global_innovation_counter, population.global_node_counter)

				offspring.append(new_offspring)

		return offspring
