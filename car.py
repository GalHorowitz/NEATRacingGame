import math
import pygame
from math_utils import Vector, Ray

FRICTION_ACCEL = 200
MAX_VELOCITY = 500
CAR_BOUNDING_BOX_WIDTH = 141
CAR_BOUDNING_BOX_HEIGHT = 65
RAY_ANGLE = math.radians(25)

class Car:
	"""
	Represents a car in-game
	"""

	# Holds the sprite used to draw any instance of Car. Lazily loaded by `Car.get_sprite()`
	car_sprite = None

	def __init__(self, initial_x, initial_y):
		"""
		Constructs a car with the given initial position: `(initial_x, initial_y)`
		"""

		self.position = Vector(initial_x, initial_y)
		self.direction = 0 # In radians

		self.velocity = 0
		self.acceleration = 0

	def physics_update(self, delta_time):
		"""
		Updates the car's position and velocity based on its acceleration, given that `delta_time`
		seconds passed since the last `physics_update` call.
		"""

		self.position += delta_time*self.velocity*Vector.unit_from_angle(self.direction)
		self.velocity += delta_time*self.acceleration

		# Deal with floating-point instability
		if abs(self.velocity) < 0.9:
			self.velocity = 0

		if math.fabs(self.velocity) > MAX_VELOCITY:
			self.velocity *= MAX_VELOCITY/(math.fabs(self.velocity))

	def set_move_acceleration(self, acceleration):
		"""
		Sets the car's total acceleration for the next physics update, also applies friction.
		"""
		self.acceleration = acceleration

		if math.fabs(self.velocity) > 0:
			friction_magnitude = min(self.velocity, FRICTION_ACCEL)
			self.acceleration -= math.copysign(friction_magnitude, self.velocity)

	def draw(self, screen, screen_mapping):
		"""
		Draws the car on `screen`, with the position adjusted based on the provided `screen_mapping`
		"""

		rotated_sprite = pygame.transform.rotate(Car.get_sprite(), self.direction * 180/math.pi)

		sprite_rect = rotated_sprite.get_rect()
		sprite_middle = Vector(sprite_rect.width, sprite_rect.height)/2
		sprite_position = self.position - sprite_middle
		screen_position = sprite_position + screen_mapping
		screen.blit(rotated_sprite, screen_position.as_tuple())

	def get_sight_rays(self):
		"""
		Returns a list of Ray objects representing the sensors of the car
		"""

		rays = []
		for ray_angle in (-RAY_ANGLE, 0, RAY_ANGLE):
			start_pos = self.position
			direction = Vector.unit_from_angle(self.direction+ray_angle)
			rays.append(Ray(start_pos, direction))
		return rays

	def get_bounding_box(self):
		"""
		Returns a list represention of the 4 points that define the car's bounding box.

		This method is expensive, if possible (i.e. the car's position and direction doesn't change)
		the result should be cached.
		"""

		half_width = CAR_BOUNDING_BOX_WIDTH/2
		half_height = CAR_BOUDNING_BOX_HEIGHT/2
		car_rect = [
			(Vector(half_width, half_height).rotated(self.direction) + self.position).as_tuple(),
			(Vector(half_width, -half_height).rotated(self.direction) + self.position).as_tuple(),
			(Vector(-half_width, -half_height).rotated(self.direction) + self.position).as_tuple(),
			(Vector(-half_width, half_height).rotated(self.direction) + self.position).as_tuple()
		]
		return car_rect

	def get_normalized_speed(self):
		"""
		Returns a normalized value representing the magnitude of the velocity
		"""
		return math.fabs(self.velocity)/MAX_VELOCITY

	@staticmethod
	def get_sprite():
		"""
		Returns the sprite used to draw a car. Lazily loads the sprite upon request.
		"""

		if Car.car_sprite is None:
			Car.car_sprite = pygame.transform.scale(pygame.image.load('assets/red_car.png'), (165, 78)).convert_alpha()
		return Car.car_sprite
