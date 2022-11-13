import os

os.environ['BOXLET_RENDER_MODE'] = 'opengl'
os.environ['BOXLET_OPENGL_VSYNC'] = '1'

from boxlet import *
from boxlet.opengl.renderers.instanced_renderer import InstancedRenderer
import random

# render assets
box_model = Model.load_obj("examples/opengl_example/cube.obj")
box_texture = Texture(pygame.image.load("examples/opengl_example/box.png"), nearest=False)

shader = VertFragShader(vertex = """
	#version 330
	layout(location = 0) in vec3 position;
	layout(location = 1) in vec2 texcoord;
	layout(location = 2) in mat4 model;

	uniform mat4 box_viewProj;

	out vec2 uv;

	void main() {
		gl_Position = box_viewProj * model * vec4(position, 1);
		uv = texcoord;
	}
	""", 
	frag = """
	#version 330
	in vec2 uv;

	uniform sampler2D tex;

	out vec4 fragColor;

	void main() {
		fragColor = texture(tex, uv);
	}
	""")

class ModelInstance(RenderInstance):
	model_matrix:np.ndarray = 'attrib', 'mat4', 'model'
	texture = 'texture', 'tex'

# render pipeline
camera = Camera3D(queue = 0, pass_names = ['default'])
default_pass = PassOpaque('default', 0)
models = InstancedRenderer(box_model, shader, ModelInstance, pass_name = 'default')
models.set_uniform('texture', box_texture)
apply_frame = ApplyShaderToFrame(camera.texture, queue = 1000)


# world assets
cc = CameraController(camera)
cc.pos[:] = (0,0,-15)

class ModelSpawner(Entity):
	def __init__(self):
		self.timer = 0
		self.rate = 1

	# def fixed_update(self):
	# 	...
	
	def vary_update(self):
		self.timer += manager.delta_time
		while self.timer > self.rate:
			self.timer -= self.rate
			self.spawn_cube()
			
	@Entity.watch_event(pygame.KEYDOWN)
	def keydown(self, event):
		if event.key == pygame.K_f:
			self.spawn_cube()

	def spawn_cube(self):
		new_model = models.new_instance(model_matrix = Tmath.translate([random.random() * 30 - 15 for _ in range(3)]))
		# or new_model.model_matrix = ...
		
ModelSpawner()

bigbox = models.new_instance()
mat = Tmath.translate((0,-30,0))
mat = np.matmul(Tmath.rotate(45, np.array([0,1,0])), mat)
mat = np.matmul(Tmath.scale((30,30,30)), mat)
bigbox.model_matrix = mat

manager.run()

