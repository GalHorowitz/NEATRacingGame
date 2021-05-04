import pygame
from car import Car, MAX_VELOCITY
from math_utils import Vector
from intersections import rect_rect_intersection, ray_rect_intersection
import game_map

CAR_ACCELERATION = 300
CAR_ROTATION_SPEED = 0.07
MAX_RAY_LENGTH = 220

class Game:
	"""
	Represents a game simulation
	"""

	def __init__(self, num_cars, start_pos, walls, checkpoints):
		self.camera_position = Vector(0, 0)

		self.walls = walls
		self.checkpoints = [Vector.from_tuple(x) for x in checkpoints]

		start_pos_x, start_pos_y = start_pos
		self.cars = [Car(start_pos_x, start_pos_y) for _ in range(num_cars)]
		self.reached_checkpoint = [0]*num_cars
		self.dead = [False]*num_cars

		self.tracked_car = 0

	def update(self, delta_time, car_controls):
		"""
		Updates the physical game state given that `delta_time` seconds passed since the last call
		to update. The inputs that control each car are represented by a dictionary, and those dicts
		are ordered by car index in `car_controls`. An array is returned which holds info about each
		car: [normalized_speed, normalized_ray_dist1, normalized_ray_dist2, normalized_ray_dist3]
		"""

		for car_idx, car in enumerate(self.cars):
			if self.dead[car_idx]: continue

			car_acceleration = 0
			if car_controls[car_idx]['forward']:
				car_acceleration += CAR_ACCELERATION
			if car_controls[car_idx]['backward']:
				car_acceleration -= CAR_ACCELERATION

			if car_controls[car_idx]['left']:
				car.direction += CAR_ROTATION_SPEED
			if car_controls[car_idx]['right']:
				car.direction -= CAR_ROTATION_SPEED

			car.set_move_acceleration(car_acceleration)
			car.physics_update(delta_time)

			# This method is expensive, so we cache the result because we know the rotation of the car
			# won't change
			cached_car_rect = car.get_bounding_box()
			is_intersecting = False
			for wall in self.walls:
				# For each wall, we check if the car's bounding box intersects the wall
				if rect_rect_intersection(wall.verts, cached_car_rect):
					is_intersecting = True
					break
			if is_intersecting:
				# If we found any intersection, the car dies
				self.dead[car_idx] = True

			# We calculate the distance to the next checkpoint
			next_checkpoint_idx = (self.reached_checkpoint[car_idx] + 1) % len(self.checkpoints)
			next_checkpoint = self.checkpoints[next_checkpoint_idx]
			next_checkpoint_dist_sq = (car.position - next_checkpoint).sqr_magnitude()
			dist_threshold = game_map.GRID_SIZE*(1 + game_map.WALL_INSERT)
			if next_checkpoint_dist_sq < dist_threshold**2:
				# If we are below the distance threshold, we update the reached_checkpoint dict to
				# reflect that the car reached a new checkpoint
				self.reached_checkpoint[car_idx] = next_checkpoint_idx

		# Update camera position to follow the tracked car
		self.camera_position = self.cars[self.tracked_car].position

		# We then generate the sensor info for each car for use as input to the neural networks
		ray_dists = self.calc_ray_dists()
		car_info = [None]*len(self.cars)
		for i, car in enumerate(self.cars):
			# This isn't the prettiest code, but combining lists is slow the idiomatic way
			car_info[i] = [self.cars[i].velocity/MAX_VELOCITY, ray_dists[i][0], ray_dists[i][1], ray_dists[i][2]]
		return car_info

	def calc_ray_dists(self):
		"""
		Calculates the hit distance for each sensor ray, for each car
		"""

		ray_dists = [None]*len(self.cars)

		for i, car in enumerate(self.cars):
			ray_dists[i] = [1]*3
			for j, ray in enumerate(car.get_sight_rays()):
				inter_point, ray_dist = self.raycast_against_walls(ray, MAX_RAY_LENGTH)
				if inter_point is not None and ray_dist <= MAX_RAY_LENGTH:
					ray_dists[i][j] = ray_dist / MAX_RAY_LENGTH

		return ray_dists

	def draw_scene(self, screen):
		"""
		Draws the game state on `screen`
		"""

		screen_mapping = self.get_screen_mapping(screen)

		# We draw each checkpoint
		for cp_idx, checkpoint in enumerate(self.checkpoints):
			# If this checkpoint is the last checkpoint the tracked car reached, we mark it with a
			# different color
			if cp_idx == self.reached_checkpoint[self.tracked_car]:
				circle_color = (221, 40, 0)
			else:
				circle_color = (0, 130, 224)
			pygame.draw.circle(screen, circle_color, (checkpoint + screen_mapping).as_tuple(), 20)


		for car_idx, car in enumerate(self.cars):
			if self.dead[car_idx]: continue

			# We draw the sensor rays of each car
			for ray in car.get_sight_rays():
				start_pos = ray.start + screen_mapping
				full_end_pos = ray.start + ray.direction*MAX_RAY_LENGTH + screen_mapping
				pygame.draw.line(screen, (255, 0, 0), start_pos.as_tuple(), full_end_pos.as_tuple())

				inter_point, ray_dist = self.raycast_against_walls(ray, MAX_RAY_LENGTH)
				if inter_point is not None and ray_dist <= MAX_RAY_LENGTH:
					end_pos = inter_point + screen_mapping
					pygame.draw.line(screen, (0, 255, 0), start_pos.as_tuple(), end_pos.as_tuple(), 2)

			# We draw the body of each car
			car.draw(screen, screen_mapping)

		# We draw each wall. Because there are many walls, and this is expensive, we don't draw walls
		# that are too far away to show up on screen
		screen_rect = screen.get_rect()
		cutoff_dist_sq = 2 * (screen_rect.width**2 + screen_rect.height**2)
		for wall in self.walls:
			mapped_wall = map_rect_to_screen(wall.verts, screen_mapping)
			if mapped_wall[0][0]**2 + mapped_wall[0][1]**2 > cutoff_dist_sq:
				continue
			pygame.draw.polygon(screen, (160, 160, 160), mapped_wall)

	def raycast_against_walls(self, ray, max_ray_length=0):
		# Raycasting against every wall (and therefore against every rect segment) is way too slow
		# with regards to the amount of ray-casts we want to perform every frame. As such, we must
		# prune away walls that we know we can't hit anyway, i.e. those that are too far away to
		# hit. We can only use that optimization if we know the `max_ray_length`.

		candidate_walls = []
		if max_ray_length == 0:
			candidate_walls = self.walls
		else:
			for wall in self.walls:
				# For each wall, we find the minimum distance to the ray start from the vertices
				min_sqr_dist_lower_bound = None
				for vert in wall.verts:
					sqr_vert_dist = (Vector.from_tuple(vert) - ray.start).sqr_magnitude()
					sqr_dist_lower_bound = sqr_vert_dist-wall.sqr_half_side
					if min_sqr_dist_lower_bound is None or sqr_dist_lower_bound < min_sqr_dist_lower_bound:
						min_sqr_dist_lower_bound = sqr_dist_lower_bound

				# We then only consider walls that are below the threshold as candidates for hit detection
				if min_sqr_dist_lower_bound < max_ray_length**2:
					candidate_walls.append(wall)

		# We go through each candidate wall, and calculate if an intersection exists between and the
		# wall and ray, if it does, we update the hit point if it is closer to the ray start
		closest_point = None
		shortest_distance = None
		for wall in candidate_walls:
			inter_point, ray_dist = ray_rect_intersection(ray, wall.verts)
			if ray_dist is not None:
				if shortest_distance is None or ray_dist < shortest_distance:
					closest_point = inter_point
					shortest_distance = ray_dist

		return (closest_point, shortest_distance)

	def get_screen_mapping(self, screen):
		"""
		Calculates a vector that when added to a point in game-space maps it to screen-space
		"""

		screen_rect = screen.get_rect()
		screen_middle = Vector(screen_rect.width, screen_rect.height)/2

		return screen_middle - self.camera_position

	def get_cars_fitness(self):
		"""
		Returns a list with the calculated fitness of each car
		"""

		# The fitness of a car is essentially the distance it covered on the track. Because
		# measuring the exact distance is costly, we use a set of checkpoints along the track to
		# estimate the total distance

		# As an optimization, we calculate the accumulated distance after each checkpoint
		checkpoint_acc = [0]*len(self.checkpoints)
		for i in range(1, len(self.checkpoints)):
			checkpoint_acc[i] = checkpoint_acc[i-1]
			checkpoint_acc[i] += (self.checkpoints[i] - self.checkpoints[i-1]).magnitude()

		fitness = [0]*len(self.cars)
		for i in range(len(self.cars)):
			# Because we reach a checkpoint whenever we get close enough to it, the `reached_checkpoint`
			# list might actually contain the next checkpoint, if we are just before it, so we grab
			# both the reached checkpoint and the one before it
			reached_checkpoint = self.reached_checkpoint[i]
			prev_checkpoint = self.checkpoints[(reached_checkpoint - 1)%len(self.checkpoints)]

			# We calculate the distance between the car and the previous checkpoint
			dist_to_prev = (prev_checkpoint - self.cars[i].position).magnitude()
			# We calculate the distance between these two checkpoint, which we will use to determine
			# if we actually passed the "reached" checkpoint
			last_checkpoint_dist = (self.checkpoints[reached_checkpoint] - prev_checkpoint).magnitude()

			# If the distance to the previous checkpoint is less than the distance between the previous
			# and current checkpoint, we didn't actually reach the checkpoint yet
			if dist_to_prev < last_checkpoint_dist:
				# If the car is before the first checkpoint, it drived backwards
				if reached_checkpoint == 0:
					fitness[i] = 0
				else:
					# The fitness is then the accumulated distance up to the previous checkpoint plus the
					# distance the car covered since it passed that last checkpoint
					fitness[i] = checkpoint_acc[(reached_checkpoint - 1)%len(self.checkpoints)] + dist_to_prev
			else:
				# The fitness is then the accumulated distance up to the current checkpoint plus the
				# distance the covered sicne it passed the current checkpoint
				dist_to_reached = (self.checkpoints[reached_checkpoint] - self.cars[i].position).magnitude()
				fitness[i] = checkpoint_acc[reached_checkpoint] + dist_to_reached

		# Distance in pixels grows quite rapidly, so we multiply everything by 0.01 to get fitness
		# scores in a saner range
		for i in range(len(self.cars)):
			fitness[i] *= 0.01

		return fitness

	def track_car(self, car_idx):
		"""
		Sets `car_idx` to be the car tracked by the camera
		"""

		self.tracked_car = car_idx

def map_rect_to_screen(rect, screen_mapping):
	"""
	Helper function to adjust a rect's vertices based on a mapping
	"""

	return [(v[0] + screen_mapping.x, v[1] + screen_mapping.y) for v in rect]
