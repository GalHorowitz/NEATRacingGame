import pygame

HANDLE_OFFSET = 135
FRAME_PADDING = 10
HANDLE_PADDING = 30
SPEEDOMETER_SCALE = 5

SPEEDOMETER_FRAME_SPRITE = None
SPEEDOMETER_HANDLE_SPRITE = None

def scale_sprite_by_factor(sprite_orig, factor):
	"""
	Generates a sprite by scaling `sprite_orig` by `factor`
	"""

	sprite_orig_rect = sprite_orig.get_rect()
	new_sprite_size = (sprite_orig_rect.width//factor, sprite_orig_rect.height//factor)
	return pygame.transform.scale(sprite_orig, new_sprite_size).convert_alpha()

def draw_speedometer(screen, value):
	"""
	Draws the speedometer on `screen`, with the handle aligned to `value` which is in the range [0, 1]
	"""

	global SPEEDOMETER_FRAME_SPRITE
	global SPEEDOMETER_HANDLE_SPRITE

	# Lazily load relevant sprites
	if SPEEDOMETER_FRAME_SPRITE is None:
		SPEEDOMETER_FRAME_SPRITE = scale_sprite_by_factor(pygame.image.load('assets/speedometer_frame.png'), SPEEDOMETER_SCALE)
	if SPEEDOMETER_HANDLE_SPRITE is None:
		SPEEDOMETER_HANDLE_SPRITE = pygame.image.load('assets/speedometer_handle.png')

	# Draw speedometer frame
	speedometer_frame_rect = SPEEDOMETER_FRAME_SPRITE.get_rect()
	screen_rect = screen.get_rect()
	frame_x = screen_rect.width - speedometer_frame_rect.width - FRAME_PADDING
	frame_y = screen_rect.height - speedometer_frame_rect.height - FRAME_PADDING
	screen.blit(SPEEDOMETER_FRAME_SPRITE, (frame_x, frame_y))

	# Rotate and draw speedometer handle
	rotated_handle = pygame.transform.rotate(SPEEDOMETER_HANDLE_SPRITE, HANDLE_OFFSET - value*180)
	sized_handle = scale_sprite_by_factor(rotated_handle, SPEEDOMETER_SCALE)
	handle_rect = sized_handle.get_rect()
	handle_x = frame_x + (speedometer_frame_rect.width - handle_rect.width)//2
	handle_y = frame_y + (speedometer_frame_rect.height - handle_rect.height)//2 + HANDLE_PADDING
	screen.blit(sized_handle, (handle_x, handle_y))
