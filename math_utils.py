import math

class Vector:
	"""
	Represents a simple 2D cartesian vector.
	"""

	def __init__(self, x, y):
		self.x = x
		self.y = y

	def magnitude(self):
		"""
		Returns the magnitude of the vector.

		This uses a sqrt which is slow, use `sqr_magnitude` for comparisons.
		"""

		return math.sqrt(self.sqr_magnitude())

	def sqr_magnitude(self):
		"""
		Returns the squared magnitude of the vector.
		"""

		return self.x**2 + self.y**2

	def normalized(self):
		"""
		Returns a new vector with the same direction and a magnitude of 1.
		"""

		return self * (1/self.magnitude())

	def angle(self):
		"""
		Returns the angle of the vector with regards to the X-axis in radians.
		"""

		return math.atan2(self.y, self.x)

	def rotated(self, angle_off):
		"""
		Returns a new vector with the same magnitude and with angle rotated by `angle_off`
		"""

		return self.magnitude()*Vector.unit_from_angle(self.angle() + angle_off)

	def __repr__(self):
		return f'Vector(x={self.x}, y={self.y})'

	def __add__(self, other):
		return Vector(self.x+other.x, self.y+other.y)

	def __sub__(self, other):
		return Vector(self.x-other.x, self.y-other.y)

	def __mul__(self, other):
		return Vector(self.x * other, self.y * other)

	def __rmul__(self, other):
		return Vector(self.x * other, self.y * other)

	def __truediv__(self, other):
		return Vector(self.x / other, self.y / other)

	def as_tuple(self):
		return (self.x, self.y)

	@staticmethod
	def unit_from_angle(angle):
		"""
		Constructs a unit-vector (magnitude of 1) with the specified `angle`
		"""

		return Vector(math.cos(angle), -math.sin(angle))

	@staticmethod
	def from_tuple(t):
		return Vector(t[0], t[1])

class Ray:
	def __init__(self, start, direction):
		self.start = start
		self.direction = direction

		if self.direction.sqr_magnitude() != 1.0:
			self.direction = self.direction.normalized()

class Rectangle:
	def __init__(self, vert_a, vert_b, vert_c, vert_d):
		self.verts = (vert_a, vert_b, vert_c, vert_d)

		side_a = (Vector.from_tuple(self.verts[0])-Vector.from_tuple(self.verts[1])).magnitude()
		side_b = (Vector.from_tuple(self.verts[1])-Vector.from_tuple(self.verts[3])).magnitude()
		self.sqr_half_side = max(side_a/2, side_b/2)**2
