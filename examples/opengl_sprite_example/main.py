from boxlet import *
from boxlet.opengl import *
from boxlet.opengl.renderers.instanced_renderer import InstancedRenderer
from math import floor
import random

manager.init(render_mode='opengl', vsync=True)

# render assets
sprite = pygame.image.load('examples/opengl_sprite_example/sprites_with_alpha.png')
w,h = sprite.get_size()

sub_locs = [(i*11, 37, 11, 18) for i in range(8)] # standing sprites
sub_locs.extend([(i*11, 18, 11, 18) for i in range(8)]) # walking sprites
sub_locs.extend([(33, 0, 11, 18), (77, 0, 11, 18)]) # alternate walking sprites
sub_locs.extend([(89, 41, 14, 14), (89, 26, 14, 14)]) # apple and fish sprites
sub_locs = [tuple([i[0]/w + 0.0001, i[1]/h + 0.0001, i[2]/w, i[3]/h]) for i in sub_locs] 
# converting coords, the '+ 0.0001's are probably not needed if the width and height are a power of 2
sub_sprites = MultiTexture(sprite, sub_locs)

sprite_shader = VertFragShader(vertex = """
	#version 330
	layout(location = 0) in vec2 position;
	layout(location = 1) in vec2 texcoord;
	layout(location = 2) in vec3 texPos;
	layout(location = 3) in vec4 uvPos; // .xy = position, .zw = scale

	uniform vec2 box_cameraSize;
	uniform vec2 box_cameraPos;

	uniform vec2 texSize;
	
	out vec2 uv;

	void main() {
		vec2 truePos = position * texSize * uvPos.zw + texPos.xy;
		vec2 screenPos = (truePos - box_cameraPos) * 2 / box_cameraSize;
		gl_Position = vec4(screenPos, texPos.z, 1);
		uv = texcoord * uvPos.zw + uvPos.xy;
	}
	""", 
	frag = """
	#version 330
	in vec2 uv;

	uniform sampler2D tex;

	out vec4 fragColor;

	void main() {
		vec4 color = texture(tex, uv);
		if(color.a < 0.5) discard;
		fragColor = color;
	}
	""")

class SpriteInstance(RenderInstance):
	position = 'attrib', [0,0,0], 'texPos'
	uv_pos = 'attrib', [0,0,1,1], 'uvPos'
	texture:MultiTexture = 'texture', 'tex'
	texture_size = 'uniform', 'texSize'

	def set_sprite(self, id):
		data = self.texture.sub_image_data[id]
		self.uv_pos = data

quad_model = Model.gen_quad_2d(-0.5, 0.5)

# render pipeline
camera = Camera2D(width_mult=0.25, height_mult=0.25, nearest=True, queue = 0, pass_names = ['default'])
default_pass = PassOpaque('default', 0)
sprite_renderer = InstancedRenderer(quad_model, sprite_shader, SpriteInstance, pass_name = 'default')
sprite_renderer.set_uniform('texture', sub_sprites)
sprite_renderer.set_uniform('texture_size', sub_sprites.size)
apply_frame = ApplyShaderToFrame(camera.texture, queue = 1000)


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
		[2,3,4],
		[1,0,5],
		[0,7,6],
	]

	def __init__(self):
		self.facing_dir = 3
		self.animation_time = 0
		self.pos = np.zeros(3, int)
		self.sprite = sprite_renderer.new_instance(position = self.pos)

	def fixed_update(self):
		b = pygame.key.get_pressed()
		mov = np.zeros(3, int)
		dir = [1,1]

		if b[pygame.K_a] != b[pygame.K_d]: 
			mov[0] = 1 if b[pygame.K_d] else -1
			dir[0] = mov[0] + 1
			
		if b[pygame.K_s] != b[pygame.K_w]: 
			mov[1] = 1 if b[pygame.K_w] else -1
			dir[1] = mov[1] + 1

		if dir == [1,1]:
			self.animation_time = 0

		else:
			self.pos += mov
			self.facing_dir = self.dir_map[dir[1]][dir[0]]
			self.animation_time += manager.fixed_delta_time * 8

	def vary_update(self):
		frame = 1 if self.animation_time == 0 else floor(self.animation_time) % 4
		bump = [0, (frame+1) % 2, 0]
		self.sprite.set_sprite(self.sprite_animation[self.facing_dir][frame])
		self.sprite.position = self.pos + bump

	@Entity.watch_event(pygame.KEYDOWN)
	def keydown(self, event):
		if event.key == pygame.K_ESCAPE:
			manager.quit()


class Item(Entity):
	def __init__(self, sprite_id = None, pos = [0,0,0]):
		self.pos = np.array(pos)
		self.sprite = sprite_renderer.new_instance(position = self.pos)
		self.sprite.set_sprite(sprite_id)


class Apple(Item):
	def __init__(self, pos = [0,0,0]):
		super().__init__(18, pos)


class Fish(Item):
	def __init__(self, pos = [0,0,0]):
		super().__init__(19, pos)


Player()

for _ in range(10):
	Apple([random.randint(-50, 50) for i in range(2)] + [0])

for _ in range(5):
	Fish([random.randint(-50, 50) for i in range(2)] + [0])

manager.run()

