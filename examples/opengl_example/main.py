import os
os.environ['BOXLET_RENDER_MODE'] = 'opengl'

from boxlet import *
import random

# render assets/pipeline
box_model = Model.load_obj("examples/opengl_example/cube.obj")
box_texture = Texture(pygame.image.load("examples/opengl_example/box.png"), nearest=False)

SimpleClearStep(queue = 0)
camera = Camera3D(queue = 50)
models = ModelInstancedRenderer(box_model, box_texture, queue = 100)


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

