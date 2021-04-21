import sys
import pygame
from game import Game
from neat.population import Population
import ui
import game_map

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

def old_main():
	pygame.init()
	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
	frame_clock = pygame.time.Clock()

	start_pos, walls, checkpoints = game_map.gen_map()

	game = Game(1, start_pos, walls, checkpoints)
	key_state = {'forward': False, 'left': False, 'backward': False, 'right': False}

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_w:
					key_state['forward'] = True
				elif event.key == pygame.K_a:
					key_state['left'] = True
				elif event.key == pygame.K_s:
					key_state['backward'] = True
				elif event.key == pygame.K_d:
					key_state['right'] = True
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_w:
					key_state['forward'] = False
				elif event.key == pygame.K_a:
					key_state['left'] = False
				elif event.key == pygame.K_s:
					key_state['backward'] = False
				elif event.key == pygame.K_d:
					key_state['right'] = False

		screen.fill((57, 57, 57))

		game.update(frame_clock.get_time() / 1000, [key_state]*20)
		game.draw_scene(screen)

		ui.draw_speedometer(screen, game.cars[0].get_normalized_speed())

		pygame.display.flip()
		frame_clock.tick(30) # Limit framerate to 30 FPS
		# print(frame_clock.get_fps())

CARS_PER_GENERATION = 60

def new_main():
	pygame.init()
	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
	frame_clock = pygame.time.Clock()

	fitness_history = []
	network_history = []

	start_pos, walls, checkpoints = game_map.gen_map()

	game = Game(CARS_PER_GENERATION, start_pos, walls, checkpoints)

	population = Population(CARS_PER_GENERATION, 4, 4)
	cur_generation = 0
	networks = [organism.genome.as_neural_network() for organism in population.organisms]

	last_controls = [None]*CARS_PER_GENERATION
	for i in range(CARS_PER_GENERATION):
		last_controls[i] = ({'forward': False, 'left': False, 'backward': False, 'right': False})
	last_fitness = None

	running_time = 0

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_f:
					print(game.get_cars_fitness())
				elif event.key == pygame.K_s:
					print('fitness_history =', fitness_history)
					print('network_history =', network_history)

		fitness = game.get_cars_fitness()

		if last_fitness is not None:
			had_progress = False
			for last, cur in zip(last_fitness, fitness):
				if cur > last + 0.01:
					had_progress = True
					break

			if had_progress:
				running_time = max(0, running_time - 100)

		last_fitness = fitness

		if all(game.dead) or running_time > 1000:
			print(f'Finished generation {cur_generation}')
			print(f'Average: {sum(fitness)/len(fitness):5.2f} Max: {max(fitness):5.2f}')

			fitness_history.append(fitness)
			best_idx = 0
			for i in range(1, CARS_PER_GENERATION):
				if fitness[i] > fitness[best_idx]:
					best_idx = i
			network_history.append(population.organisms[best_idx].genome.connections)

			try:
				for i in range(CARS_PER_GENERATION):
					population.organisms[i].fitness = 0.00001 + fitness[i]
			except:
				print(len(population.organisms), len(fitness), fitness)
				assert False

			population.epoch()
			cur_generation += 1
			running_time = 0
			networks = [organism.genome.as_neural_network() for organism in population.organisms]
			for i in range(CARS_PER_GENERATION):
				last_controls[i] = ({'forward': False, 'left': False, 'backward': False, 'right': False})
			game = Game(CARS_PER_GENERATION, start_pos, walls, checkpoints)


		screen.fill((57, 57, 57))

		best_car = None
		for i in range(0, CARS_PER_GENERATION):
			if game.dead[i]: continue
			if best_car is None or fitness[i] > fitness[best_car]:
				best_car = i
		if best_car is None:
			best_car = 0
		game.track_car(best_car)

		cars_info = game.update(frame_clock.get_time() / 1000, last_controls)
		game.draw_scene(screen)

		for i in range(CARS_PER_GENERATION):
			network_output = networks[i].evaluate_input(cars_info[i])
			last_controls[i]['forward'] = network_output[0] >= 0
			last_controls[i]['left'] = network_output[1] >= 0
			last_controls[i]['backward'] = network_output[2] >= 0
			last_controls[i]['right'] = network_output[3] >= 0

		ui.draw_speedometer(screen, game.cars[best_car].get_normalized_speed())

		pygame.display.flip()
		running_time += frame_clock.tick(30) # Limit framerate to 30 FPS
		# print(frame_clock.get_fps())

if __name__ == "__main__":
	new_main()
