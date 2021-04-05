import math
import pygame
from math_utils import Rectangle

HORIZ_WALL_COLOR = (182, 255, 0)
VERT_WALL_COLOR = (0, 127, 14)
UPPER_LEFT_WALL_COLOR = (0, 0, 255)
UPPER_RIGHT_WALL_COLOR = (124, 20, 0)
LOWER_RIGHT_WALL_COLOR = (0, 255, 255)
LOWER_LEFT_WALL_COLOR = (124, 0, 79)
CAR_START_COLOR = (255, 0, 12)
CHECKPOINT_MARKER_COLOR = (255, 106)

GRID_SIZE = 200
WALL_INSERT = 0.3

def gen_map():
	track = pygame.image.load('assets/track.png')
	pxarray = pygame.PixelArray(track)

	start_pos = None
	checkpoints = dict()
	walls = []

	wall_width = GRID_SIZE*(1 - 2*WALL_INSERT)
	diag_offset = wall_width/2

	for y in range(pxarray.shape[1]):
		for x in range(pxarray.shape[0]):
			color_at_px = track.unmap_rgb(pxarray[x, y])[:3]
			if color_at_px == CAR_START_COLOR:
				start_pos = ((x+.5)*GRID_SIZE, (y+.5)*GRID_SIZE)
				checkpoints[0] = start_pos
			elif color_at_px == HORIZ_WALL_COLOR:
				walls.append(Rectangle(
					(x*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					(x*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE)
				))
			elif color_at_px == VERT_WALL_COLOR:
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, y*GRID_SIZE)
				))
			elif color_at_px == UPPER_LEFT_WALL_COLOR:
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE + diag_offset, (y+WALL_INSERT)*GRID_SIZE + diag_offset),
					((x+WALL_INSERT)*GRID_SIZE + diag_offset, (y+1)*GRID_SIZE + diag_offset)
				))
			elif color_at_px == UPPER_RIGHT_WALL_COLOR:
				walls.append(Rectangle(
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					(x*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					(x*GRID_SIZE - diag_offset, (y+WALL_INSERT)*GRID_SIZE + diag_offset),
					((x+1-WALL_INSERT)*GRID_SIZE - diag_offset, (y+1)*GRID_SIZE + diag_offset)
				))
			elif color_at_px == LOWER_RIGHT_WALL_COLOR:
				walls.append(Rectangle(
					((x+1-WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					(x*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					(x*GRID_SIZE - diag_offset, (y+1-WALL_INSERT)*GRID_SIZE - diag_offset),
					((x+1-WALL_INSERT)*GRID_SIZE - diag_offset, y*GRID_SIZE - diag_offset)
				))
			elif color_at_px == LOWER_LEFT_WALL_COLOR:
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE + diag_offset, (y+1-WALL_INSERT)*GRID_SIZE - diag_offset),
					((x+WALL_INSERT)*GRID_SIZE + diag_offset, y*GRID_SIZE - diag_offset),
				))
			elif color_at_px[:2] == CHECKPOINT_MARKER_COLOR:
				checkpoints[color_at_px[2]] = (((x+.5)*GRID_SIZE, (y+.5)*GRID_SIZE))

	ordered_checkpoints = [checkpoints[i] for i in range(len(checkpoints))]

	return (start_pos, walls, ordered_checkpoints)

"""
def gen_map():
	track = pygame.image.load('assets/track.png')
	pxarray = pygame.PixelArray(track)

	start_pos = None
	checkpoints = dict()
	walls = []

	for y in range(pxarray.shape[1]):
		for x in range(pxarray.shape[0]):
			color_at_px = track.unmap_rgb(pxarray[x, y])[:3]
			if color_at_px == CAR_START_COLOR:
				start_pos = ((x+.5)*GRID_SIZE, (y+.5)*GRID_SIZE)
				checkpoints[0] = start_pos
			elif color_at_px == HORIZ_WALL_COLOR:
				walls.append(Rectangle(
					(x*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					(x*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE)
				))
			elif color_at_px == VERT_WALL_COLOR:
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, y*GRID_SIZE)
				))
			elif color_at_px == UPPER_LEFT_WALL_COLOR:
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE)
				))
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE)
				))
			elif color_at_px == UPPER_RIGHT_WALL_COLOR:
				walls.append(Rectangle(
					(x*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					(x*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE)
				))
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+1)*GRID_SIZE)
				))
			elif color_at_px == LOWER_RIGHT_WALL_COLOR:
				walls.append(Rectangle(
					(x*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					(x*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE)
				))
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE)
				))
			elif color_at_px == LOWER_LEFT_WALL_COLOR:
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+1)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+1-WALL_INSERT)*GRID_SIZE)
				))
				walls.append(Rectangle(
					((x+WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, y*GRID_SIZE),
					((x+1-WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE),
					((x+WALL_INSERT)*GRID_SIZE, (y+WALL_INSERT)*GRID_SIZE)
				))
			elif color_at_px[:2] == CHECKPOINT_MARKER_COLOR:
				checkpoints[color_at_px[2]] = (((x+.5)*GRID_SIZE, (y+.5)*GRID_SIZE))

	ordered_checkpoints = [checkpoints[i] for i in range(len(checkpoints))]

	return (start_pos, walls, ordered_checkpoints)
"""