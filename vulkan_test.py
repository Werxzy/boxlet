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

y_range = np.arange(-1.0, 1.0, 0.2)

triangle_positions = np.array([pyrr.matrix44.create_from_translation([-0.3, y, 0]) for y in y_range], dtype = np.float32)
square_positions = np.array([pyrr.matrix44.create_from_translation([0, y, 0]) for y in y_range], dtype = np.float32)
star_positions = np.array([pyrr.matrix44.create_from_translation([0.3, y, 0]) for y in y_range], dtype = np.float32)
positions = np.concatenate([triangle_positions, square_positions, star_positions])

p, l = my_app.graphics_engine.physical_device, my_app.graphics_engine.logical_device
vk_renderer.TestRenderer(p, l, meshes, positions)


my_app.run()

meshes.destroy()

my_app.close()
