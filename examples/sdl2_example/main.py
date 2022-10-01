import os
os.environ['BOXLET_PIXEL_SCALE'] = '3'
os.environ['BOXLET_FRAME_RATE'] = '120'
# Even though Player updates it's sprite on fixed update, 
# it looks better when the manager's frame rate matches or exceedes the monitor's framerate

from boxlet import *
from math import floor


# Sprite assets
sprite_sheet = pygame.image.load('examples/sdl2_example/sprites.png')
sprite_sheet.set_colorkey((0,64,0))

sub_locs = [(i*11, 0, 11, 18) for i in range(8)] # standing sprites
sub_locs.extend([(i*11, 19, 11, 18) for i in range(8)]) # walking sprites
sub_locs.extend([(33, 37, 11, 18), (77, 37, 11, 18)]) # alternate walking sprites
sub_locs.extend([(89, 0, 14, 14), (89, 15, 14, 14)]) # apple and fish sprites

sub_sprites = list(map(sprite_sheet.subsurface, sub_locs))


class Player(Entity):

	sprite_animation = [
		[8, 0, 8, 0],
		[9, 1, 9, 1],
		[10, 2, 10, 2],
		[11, 3, 16, 3],
		[12, 4, 12, 4],
		[13, 5, 13, 5],
		[14, 6, 14, 6],
		[15, 7, 17, 7],
	]

	dir_map = [
		[0,7,6],
		[1,0,5],
		[2,3,4],
	]

	def __init__(self):
		self.facing_dir = 3
		self.animation_time = 0
		self.pos = np.zeros(2, int)

	def fixed_update(self):
		b = pygame.key.get_pressed()
		mov = np.zeros(2, int)
		dir = [1,1]

		if b[pygame.K_a] != b[pygame.K_d]: 
			mov[0] = 1 if b[pygame.K_d] else -1
			dir[0] = mov[0] + 1
			
		if b[pygame.K_s] != b[pygame.K_w]: 
			mov[1] = 1 if b[pygame.K_s] else -1
			dir[1] = mov[1] + 1

		if dir == [1,1]:
			self.animation_time = 0

		else:
			self.pos += mov
			self.facing_dir = self.dir_map[dir[1]][dir[0]]
			self.animation_time += manager.fixed_delta_time * 8

	@Entity.watch_event(pygame.KEYDOWN)
	def keydown(self, event):
		if event.key == pygame.K_ESCAPE:
			manager.quit()

	def render(self):
		frame = 1 if self.animation_time == 0 else floor(self.animation_time) % 4
		bump = [0, (frame+1) % 2]
		sprite_id = self.sprite_animation[self.facing_dir][frame]
		manager.screen.blit(sub_sprites[sprite_id], self.pos - bump)


Player()

manager.run()

