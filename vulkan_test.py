from boxlet import *
from boxlet.vulkan import *


manager.init(render_mode='vulkan')

mesh_list = [
	Mesh.gen_cube(0.05),
	Mesh.gen_sphere(0.06, 4),
	Mesh.gen_quad_3d(-0.049, 0.049),
]

meshes = MultiMesh(mesh_list)

mesh_list.clear()
# clears out extra meshes that aren't needed after initializing the multimeshh

texture = Texture(pygame.image.load("examples/opengl_example/box.png"))

# base_vert = Shader('vertex', 'examples/vulkan_example/shaders/test_shader/vert.spv')
# base_frag = Shader('fragment', 'examples/vulkan_example/shaders/test_shader/frag.spv')
base_vert = Shader('vertex', 'examples/vulkan_example/shaders/mrt_test_shader/vert.spv')
base_frag = Shader('fragment', 'examples/vulkan_example/shaders/mrt_test_shader/frag.spv')
vignette_vert = Shader('vertex', 'examples/vulkan_example/shaders/vignette_shader/vert.spv')
vignette_frag = Shader('fragment', 'examples/vulkan_example/shaders/vignette_shader/frag.spv')

# - - - - - - - - - - - - - - - - - - - - - - -
#	render pipeline creation
# - - - - - - - - - - - - - - - - - - - - - - -


camera_step = Camera3D(priority = -1)
camera_controller = CameraController(camera_step)
camera_controller.pos[2] -= 1

# - - render pass for normal rendering to texture - -
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

srt = SimpleRenderTarget(layers = 2)
render_pass = RenderPass(srt, clear_colors = [[1.0, 0.5, 0.25, 1.0]])
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
	base_vert,
	base_frag,
	meshes
)
renderer = IndirectRenderer(graphics_pipeline, meshes, {
	0 : np.array([[1,1,0,0], [1,0,1,0], [0,1,1,0]], np.float32), # they are vec3s don't forget about padding
	1 : texture
})


# - - render pass for presenting - -
shader_layout_screen = ShaderAttributeLayout(
	bindings = {
		'texture': ('sampler2D',),
	},
)

render_pass_screen = RenderPass(priority=1)
graphics_pipeline_screen = GraphicsPipeline(
	render_pass_screen,
	shader_layout_screen,
	{
		'vertex attributes' : [('position', 0), ('texcoord', 1)],
		'bindings' : [
			('texture', 0, 'fragment')
		]
	},
	vignette_vert,
	vignette_frag,
	ScreenRenderer.get_screen_mesh()
)
renderer_screen = ScreenRenderer(graphics_pipeline_screen, {
	# 0 : srt.get_color_images()[0]
	0 : srt.get_color_images()[1]
})

# - - - - - - - - - - - - - - - - - - - - - - -

instances_to_delete = []
test = 0

for y in np.arange(-1.0, 1.0, 0.05):
	inst = renderer.create_instance(0)
	inst.set(0, Tmath.translate([-0.3 + (y%0.4)/3, y, y % 0.11]))
	test = (test + 1) % 4
	if test == 0:
		instances_to_delete.append(inst)

for y in np.arange(-1.0, 1.0, 0.1):
	inst = renderer.create_instance(1)
	inst.set(0, Tmath.translate([(y%0.4)/3, y, y % 0.11]))
	test = (test + 1) % 8
	if test == 0:
		instances_to_delete.append(inst)

for y in np.arange(-1.0, 1.0, 0.1):
	inst = renderer.create_instance(2)
	inst.set(0, Tmath.translate([0.3 + (y%0.4)/3, y, y % 0.11]))
	test = (test + 1) % 2
	if test == 0:
		instances_to_delete.append(inst)

for i in instances_to_delete:
	i.destroy()

for y in np.arange(-1.0, 1.0, 0.1):
	inst = renderer.create_instance(2)
	inst.set(0, Tmath.translate([0.4 + (y%0.4)/3, y, y % 0.11]))


# import random 
class FPSCheck(Entity):
	def __init__(self):
		self.t = 0
		self.c = 0

	def vary_update(self):
		self.t += manager.delta_time
		self.c += 1

		# if manager.delta_time > 0:
		# 	print(1.0 / manager.delta_time)

		if self.t >= 1:
			print(self.c)
			self.t = self.c = 0

	# def fixed_update(self):	
	# 	inst = renderer.create_instance(0)
	# 	inst.set(0, Tmath.translate([random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)]))


FPSCheck()

manager.run()

