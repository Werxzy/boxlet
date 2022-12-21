from boxlet import *
from boxlet.vulkan import *
import pyrr


manager.init(render_mode='vulkan')

mesh_list = [
	Mesh.gen_cube(0.05),
	Mesh(vertices = {
			'position' : [
				-0.05, -0.025, 0,
				-0.02, -0.025, 0,
				-0.03, 0.0, 0,
				0.0, -0.05, 0,
				0.02, -0.025, 0,
				0.05, -0.025,  0,
				0.03, 0.0, 0,
				0.04, 0.05, 0,
				0.0, 0.01, 0,
				-0.04, 0.05, 0,
			],
			'texcoord':[
				0.0, 0.25,
				0.3, 0.25,
				0.2, 0.5,
				0.5, 0.0,
				0.7, 0.25,
				1.0, 0.25, 
				0.8, 0.5, 
				0.9, 1.0, 
				0.5, 0.6, 
				0.1, 1.0,
			]
		},
		indices = [ 
			0,1,2, 1,3,4, 2,1,4, 4,5,6, 2,4,6, 6,7,8, 2,6,8, 2,8,9 
		],
		dim = 3
	),
	Mesh.gen_quad_3d(-0.049, 0.049),
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
		'vertex attributes' : [('position', 0), ('texcoord', 1)],
		'instance attributes' : [('model', 2)],
		'push constants' : ['box_viewProj'],
		'bindings' : [
			('ubo', 0, 'vertex'),
			('texture', 1, 'fragment')
		]
	},
	'shaders/vert.spv',
	'shaders/frag.spv',
	meshes
)

data_type = np.dtype([('model', '(4,4)f4')])
renderer = IndirectRenderer(graphics_pipeline, meshes, {
	0 : np.array([[1,1,0,0], [1,0,1,0], [0,1,1,0]], np.float32), # they are vec3s don't forget about padding
	1 : texture
})

mat = np.identity(4, np.float32)
mat[0][0] = 9/16
mat[2][0] = 0.5
mat[2][1] = 0.5
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

