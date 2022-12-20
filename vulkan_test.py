from boxlet import *
from boxlet.vulkan import *
import pyrr


manager.init(render_mode='vulkan')

meshes = MultiMesh(
	[
	np.array([ # triangle
		0.0, -0.05, 0.0, 1.0, 0.0,
		0.05, 0.05, 0.0, 1.0, 0.0,
		-0.05, 0.05, 0.0, 1.0, 0.0,
	]),
	np.array([ # square
		-0.05, 0.05, 1.0, 0.0, 0.0,
		-0.05, -0.05, 1.0, 0.0, 0.0,
		0.05, -0.05, 1.0, 0.0, 0.0,
		0.05, 0.05, 1.0, 0.0, 0.0,
	]),
	np.array([ # star4
		-0.05, -0.025, 0.0, 0.0, 1.0,
		-0.02, -0.025, 0.0, 0.0, 1.0,
		-0.03, 0.0, 0.0, 0.0, 1.0,
		0.0, -0.05, 0.0, 0.0, 1.0,
		0.02, -0.025, 0.0, 0.0, 1.0,
		0.05, -0.025, 0.0, 0.0, 1.0, 
		0.03, 0.0, 0.0, 0.0, 1.0, 
		0.04, 0.05, 0.0, 0.0, 1.0, 
		0.0, 0.01, 0.0, 0.0, 1.0, 
		-0.04, 0.05, 0.0, 0.0, 1.0,
	]),
],
[
	np.array([
		0,1,2
	]),
	np.array([
		0,1,2, 2,3,0
	]),
	np.array([
		0,1,2, 1,3,4, 2,1,4, 4,5,6, 2,4,6, 6,7,8, 2,6,8, 2,8,9, 
	]),
])

texture = Texture(pygame.image.load("examples/opengl_example/box.png"))

# - - - - - - - - - - - - - - - - - - - - - - -
#	render pipeline creation
# - - - - - - - - - - - - - - - - - - - - - - -
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
render_pass = RenderPass()
graphics_pipeline = GraphicsPipeline(
	render_pass,
	shader_layout,
	{
		'attributes' : [('model', 2)],
		'push constants' : ['box_viewProj'],
		'bindings' : [
			('ubo', 0, 'vertex'),
			('texture', 1, 'fragment')
		]
	},
	'shaders/vert.spv',
	'shaders/frag.spv'
)

data_type = np.dtype([('model', '(4,4)f4')])
renderer = IndirectRenderer(graphics_pipeline, meshes, {
	0 : np.array([[1,1,0,0], [1,0,1,0], [0,1,1,0]], np.float32), # they are vec3s don't forget about padding
	1 : texture
})

mat = np.identity(4, np.float32)
mat[0][0] = 9/16
PushConstantManager.set_global('box_viewProj', mat)

# - - - - - - - - - - - - - - - - - - - - - - -

instances_to_delete = []
test = 0

for y in np.arange(-1.0, 1.0, 0.05):
	inst = renderer.create_instance(0)
	inst.set(0, pyrr.matrix44.create_from_translation([-0.3 + (y%0.4)/3, y, 0]))
	test = (test + 1) % 4
	if test == 0:
		instances_to_delete.append(inst)

for y in np.arange(-1.0, 1.0, 0.1):
	inst = renderer.create_instance(1)
	inst.set(0, pyrr.matrix44.create_from_translation([(y%0.4)/3, y, 0]))
	test = (test + 1) % 8
	if test == 0:
		instances_to_delete.append(inst)

for y in np.arange(-1.0, 1.0, 0.1):
	inst = renderer.create_instance(2)
	inst.set(0, pyrr.matrix44.create_from_translation([0.3 + (y%0.4)/3, y, 0]))
	test = (test + 1) % 2
	if test == 0:
		instances_to_delete.append(inst)

for i in instances_to_delete:
	i.destroy()

for y in np.arange(-1.0, 1.0, 0.1):
	inst = renderer.create_instance(2)
	inst.set(0, pyrr.matrix44.create_from_translation([0.4 + (y%0.4)/3, y, 0]))


manager.run()

