import pygame

HANDLE_OFFSET = 135
FRAME_PADDING = 10
HANDLE_PADDING = 30
SPEEDOMETER_SCALE = 5

speedometer_frame_sprite = None
speedometer_handle_sprite = None

def scale_sprite_by_factor(sprite_orig, factor):
		sprite_orig_rect = sprite_orig.get_rect()
		new_sprite_size = (sprite_orig_rect.width//factor, sprite_orig_rect.height//factor)
		return pygame.transform.scale(sprite_orig, new_sprite_size).convert_alpha()

def draw_speedometer(screen, value):
	global speedometer_frame_sprite
	global speedometer_handle_sprite

	if speedometer_frame_sprite is None:
		speedometer_frame_sprite = scale_sprite_by_factor(pygame.image.load('assets/speedometer_frame.png'), SPEEDOMETER_SCALE)
	if speedometer_handle_sprite is None:
		speedometer_handle_sprite = pygame.image.load('assets/speedometer_handle.png')
	
	speedometer_frame_rect = speedometer_frame_sprite.get_rect()
	screen_rect = screen.get_rect()
	frame_x = screen_rect.width - speedometer_frame_rect.width - FRAME_PADDING
	frame_y = screen_rect.height - speedometer_frame_rect.height - FRAME_PADDING
	screen.blit(speedometer_frame_sprite, (frame_x, frame_y))

	rotated_handle = pygame.transform.rotate(speedometer_handle_sprite, HANDLE_OFFSET - value*180)
	sized_handle = scale_sprite_by_factor(rotated_handle, SPEEDOMETER_SCALE)
	handle_rect = sized_handle.get_rect()
	handle_x = frame_x + (speedometer_frame_rect.width - handle_rect.width)//2
	handle_y = frame_y + (speedometer_frame_rect.height - handle_rect.height)//2 + HANDLE_PADDING
	screen.blit(sized_handle, (handle_x, handle_y))
