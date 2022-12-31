from boxlet import *
from boxlet.vulkan import *
import random


manager.init(render_mode='vulkan')

mesh_list = [
	Mesh.gen_cube(),
	Mesh.gen_sphere(divisions = 4),
]

meshes = MultiMesh(mesh_list)

for m in mesh_list:
	m.destroy()
mesh_list.clear()
# clears out extra meshes that aren't needed after initializing the multimeshh

texture = Texture(pygame.image.load("examples/opengl_example/box.png"))

# - - - - - - - - - - - - - - - - - - - - - - -
#	render pipeline creation
# - - - - - - - - - - - - - - - - - - - - - - -

# Updates/manages the values for the camera matrix that is passed to the shader.
camera_step = Camera3D(priority = -1)

# Prepares what kinds of data will be used for the renderer(s).
# objects that are used between multiple renderers will have all their 
# 	information layed out here.
shader_layout = ShaderAttributeLayout(
	attributes = [
		('model', 'mat4'),
	],
	push_constants = {
		'box_viewProj': 'mat4', 
	},
	bindings = {
		'ubo' : [('color1', 'vec3'), ('color2', 'vec3'), ('color3', 'vec3')],
		'texture': ('sampler2D',),
	},
)

# Specifies a render pass, showing where the shaders are rendered
#	and how they are applied to the render target.
render_pass = RenderPass()

# Specifies what data is used from the layout for the shader.
graphics_pipeline = GraphicsPipeline(
	render_pass,
	shader_layout,
	{
		'vertex attributes' : [('position', 0), ('texcoord', 1)],
		'instance attributes' : [('model', 2)],
		'push constants' : ['box_viewProj'],
		'bindings' : [
			('ubo', 0, 'vertex'),
			('texture', 1, 'fragment')
		]
	},
	'shaders/test_shader/vert.spv',
	'shaders/test_shader/frag.spv',
	meshes
)

# creates a renderer that uses one or more graphics pipelines.
# instances of models will usually be created through these renderers.
renderer = IndirectRenderer(graphics_pipeline, meshes, {
	0 : np.array([[1,1,0,0], [1,0,1,0], [0,1,1,0]], np.float32), # they are vec3s don't forget about padding
	1 : texture
})

# - - - - - - - - - - - - - - - - - - - - - - -

camera_controller = CameraController(camera_step)
camera_controller.pos[:] = (0,0,-15)

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
		inst = renderer.create_instance(random.randint(0,1))
		inst.set(0, Tmath.translate([random.random() * 30 - 15 for _ in range(3)]))
		# or inst.set('model, ...)

ModelSpawner()

bigbox = renderer.create_instance(0)
mat = Tmath.translate((0,-30,0))
mat = np.matmul(Tmath.rotate(45, np.array([0,1,0])), mat)
mat = np.matmul(Tmath.scale((15,15,15)), mat)
bigbox.set(0, mat)

manager.run()

