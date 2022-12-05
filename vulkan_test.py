from boxlet.vulkan import *

my_app = app.App(640, 480)



meshes = vk_mesh.MultiMesh(my_app.graphics_engine.physical_device, my_app.graphics_engine.logical_device, [
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

p, l = my_app.graphics_engine.physical_device, my_app.graphics_engine.logical_device
data_type = np.dtype([('model', '(4,4)f4')])
renderer = vk_renderer.TestRenderer(p, l, meshes, data_type)

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

my_app.run()

meshes.destroy()

my_app.close()
