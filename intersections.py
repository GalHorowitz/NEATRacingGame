import math
from math_utils import Vector

def ray_rect_intersection(ray, rect):
	"""
	Finds the intersection between a ray and a rectangle.

	Returns a tuple containing the point of intersection and the ray distance, or (None, None) if
	there is no intersection. `ray` must be of type `Ray`. `rect` must be a tuple of 4 `(x,y)`
	points.
	"""

	# A line intersects with a rectangle if and only if one of the sides of the rectangle intersects
	# with the line segment. Because we are interested in the first point along the ray that
	# intersects with the rectangle we need to check for intersection with all sides, and return
	# the intersection point closest to `ray.start`

	closest_point = None
	closest_sqr_distance = None
	for i in range(4):
		seg_point_a = rect[i]
		seg_point_b = rect[(i+1)%4]

		inter = ray_segment_intersection(ray, (seg_point_a, seg_point_b))
		if inter is not None:
			sqr_distance = (inter - ray.start).sqr_magnitude()
			if closest_point is None or closest_sqr_distance > sqr_distance:
				closest_point = inter
				closest_sqr_distance = sqr_distance

	if closest_point is not None:
		return (closest_point, math.sqrt(closest_sqr_distance))
	else:
		return (None, None)


def ray_segment_intersection(ray, segment):
	"""
	Finds the point of intersection between a ray and a segment, or returns None if such a point
	does not exist.

	`ray` must be of type `Ray`. A `segment` is a tuple of two `(x, y)` points that define the start
	and end	of the segment accordingly.
	"""

	# Based on Wikipedia's `Line–line intersection`
	x1 = ray.start.x
	y1 = ray.start.y
	ray_point = ray.start + ray.direction
	x2 = ray_point.x
	y2 = ray_point.y
	x3, y3 = segment[0]
	x4, y4 = segment[1]

	t_num = ((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))
	t_den = ((x1-x2)*(y3-y4)-(y1-y2)*(x3-x4))
	u_num = -((x1-x2)*(y1-y3)-(y1-y2)*(x1-x3))
	u_den = ((x1-x2)*(y3-y4)-(y1-y2)*(x3-x4))

	# The condition is essentially 0 <= u <= 1 and 0 <= t but we check it this way to avoid having
	# to actually do the division unless we must.
	if u_den != 0 and (u_num*u_den) >= 0 and abs(u_num) <= abs(u_den) \
		and t_den != 0.0 and (t_num*t_den) >= 0:
		# Intersection!

		u = u_num/u_den
		return Vector(x3+u*(x4-x3), y3+u*(y4-y3))
	else:
		return None

def rect_rect_intersection(rect_a, rect_b):
	"""
	Determines whether or not the rectangles `rect_a` and `rect_b` intersect.

	The paramters must be tuples of 4 points, each point a tuple of `(x, y)`
	"""

	# Accordng to the Seperating Axis Theorem we know that a rectangle doesn't intersect another
	# if and only if one of the lines that the rectangle's segments lie on can be used to seperate
	# 2D space into two parts, such that each rectangle is in a different part. Practically,
	# this means we can iterate over the 4 segments of each rectangle, and then calculate the
	# point-to-line distance for each of the vertices of the other rectangle, and if they all lie on
	# the other side of the line segment, we know that the rectangles do not intersect.

	could_not_seperate_using_a = rect_rect_intersection_helper(rect_a, rect_b)
	could_not_seperate_using_b = rect_rect_intersection_helper(rect_b, rect_a)

	return could_not_seperate_using_a and could_not_seperate_using_b

def rect_rect_intersection_helper(rect_a, rect_b):
	"""
	Checks if rect_a's segments can be used to seperate the rectangles
	"""

	for i in range(4):
		seg_point_a = rect_a[i]
		seg_point_b = rect_a[(i+1)%4]

		check_point = rect_a[(i+2)%4]
		check_point_side = point_side_of_line(check_point, seg_point_a, seg_point_b)

		all_other_side = True
		for j in range(4):
			if check_point_side == point_side_of_line(rect_b[j], seg_point_a, seg_point_b):
				all_other_side = False
				break

		if all_other_side:
			return False

	return True

def point_side_of_line(point, line_a, line_b):
	"""
	Returns a boolean value which represents which side of the line defined by (`line_a`, `line_b`)
	the point `point` lies on. A value on its own is meaningless, and must be compared to another
	point.

	`point`, `line_a` and `line_b` must all be `(x, y)` tuples
	"""

	# The sign of the expression `(x-x1)(y2-y1)-(y-y1)(x2-x1)` for point P(x,y) and line AB
	# where A(x1,y1) and B(x2,y2) determines the side of the point P with regard to the line AB.

	x, y = point
	x1, y1 = line_a
	x2, y2 = line_b

	return ((x-x1)*(y2-y1)-(y-y1)*(x2-x1)) > 0
