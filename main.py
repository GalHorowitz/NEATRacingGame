import sys
import pygame
from game import Game
from neat.population import Population
import ui
import game_map

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
CARS_PER_GENERATION = 60

def main():
	"""
	The program's starting point and main logic
	"""

	# Initialize pygame, the screen and the framerate clock
	pygame.init()
	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
	frame_clock = pygame.time.Clock()

	# Lists to keep track of fitness and best network for every generation
	fitness_history = []
	network_history = []

	# Parse the map description and generate walls and checkpoints accordingly
	start_pos, walls, checkpoints = game_map.gen_map('assets/track.png')

	# Instantiate a new game simulation
	game = Game(CARS_PER_GENERATION, start_pos, walls, checkpoints)

	# Generate an initial population (with networks which have 4 inputs and 4 outputs)
	population = Population(CARS_PER_GENERATION, 4, 4)
	cur_generation = 0

	# Compute the usable neural network for each genome in the initial population
	networks = [organism.genome.as_neural_network() for organism in population.organisms]

	# The car sensor data that the neural networks use is the values sensed last frame, so we need
	# to save them
	last_car_sensors = None

	# We track the total runtime of the generation simulation so we can stop if the cars get stuck
	# but don't die
	running_time = 0

	# We also track the fitness from the last simulation update so we can detect if there was a
	# positivedelta in fitness, i.e. the cars made progress
	last_fitness = None

	while True:
		# Handle pygame events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				# Exit if the close button was pressed
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				# Keyboard shortcuts
				if event.key == pygame.K_f:
					# If the letter `f` was pressed, print the fitness of all simulated cars
					print(game.get_cars_fitness())
				elif event.key == pygame.K_s:
					# If the letter `s` was pressed, dump the history
					print('fitness_history =', fitness_history)
					print('network_history =', network_history)

		fitness = game.get_cars_fitness()
		if last_fitness is not None:
			# We go through each car and check if its fitness improved by some epsilon, to detect if
			# any of the cars made progress
			had_progress = False
			for last, cur in zip(last_fitness, fitness):
				if cur > last + 0.05:
					had_progress = True
					break

			# If some car did make progress, we don't want to end the simulation early, so we push
			# back the runtime by 100ms
			if had_progress:
				running_time = max(0, running_time - 100)

		last_fitness = fitness

		# If all the cars have died by colliding with a wall, or the cars did not make sufficient
		# progress in over 1 second (1000ms), we end the simulation
		if all(game.dead) or running_time > 1000:
			print(f'Finished generation {cur_generation}')
			print(f'Average: {sum(fitness)/len(fitness):5.2f} Max: {max(fitness):5.2f}')

			# Record the fitness scores of each car in the generation
			fitness_history.append(fitness)

			# Find and record the genome of the most fit organism fo this generation
			best_idx = 0
			for i in range(1, CARS_PER_GENERATION):
				if fitness[i] > fitness[best_idx]:
					best_idx = i
			network_history.append(population.organisms[best_idx].genome.connections)

			# Update NEAT's view of the fitness scores of the organisms so the genetic algorithm
			# can proceed. A tiny epsilon is added because a fitness score of zero does not work
			# well when the relative fitness is calculated
			for i in range(CARS_PER_GENERATION):
				population.organisms[i].fitness = 0.00001 + fitness[i]

			# Go through all of the genetic algorithm steps, creating the next generation
			population.epoch()
			# Keep track of the current generation
			cur_generation += 1
			# Reset the running time
			running_time = 0
			# Recompute the usable neural networks for the new organisms
			networks = [organism.genome.as_neural_network() for organism in population.organisms]
			# Reset the game simulation
			game = Game(CARS_PER_GENERATION, start_pos, walls, checkpoints)
			# Reset the last frame data
			last_car_sensors = None
			last_fitness = None

		# Background color
		screen.fill((57, 57, 57))

		# We need to choose which car the game camera tracks: We pick the most fit car which is not
		# dead
		best_car = None
		for i in range(0, CARS_PER_GENERATION):
			if game.dead[i]: continue
			if best_car is None or fitness[i] > fitness[best_car]:
				best_car = i
		# If all cars are dead we just default to the first one
		if best_car is None:
			best_car = 0
		game.track_car(best_car)

		# If this is the first frame, we don't yet have sensor data to base our decision on, so we
		# just don't move
		if last_car_sensors is None:
			controls = [{'forward': False, 'left': False, 'backward': False, 'right': False}]*CARS_PER_GENERATION
		else:
			# We compute the controls for each car
			controls = []
			for i in range(CARS_PER_GENERATION):
				# We run the sensor data from last frame through the car's network
				network_output = networks[i].evaluate_input(last_car_sensors[i])
				# We then decide whether to enable that control based on a simple threshold
				control = {
					'forward': network_output[0] >= 0,
					'left': network_output[1] >= 0,
					'backward': network_output[2] >= 0,
					'right': network_output[3] >= 0
				}
				controls.append(control)

		# We make a simulation update step
		last_car_sensors = game.update(frame_clock.get_time() / 1000, controls)
		# We ask the game to draw the current state to the screen
		game.draw_scene(screen)

		# We draw the speedometer on top of the game, showing the speed of the tracked car
		ui.draw_speedometer(screen, game.cars[best_car].get_normalized_speed())

		# We display the drawn frame
		pygame.display.flip()
		running_time += frame_clock.tick(30) # Limit framerate to 30 FPS

if __name__ == "__main__":
	main()
