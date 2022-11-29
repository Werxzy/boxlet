from . import *

class Mesh:
	def __init__(self, physical_device, logical_device, vertices = None) -> None:

		if vertices is None:
			vertices = np.array([
				0.0, -0.05, 0.0, 1.0, 0.0,
				0.05, 0.05, 0.0, 1.0, 0.0,
				-0.05, 0.05, 0.0, 1.0, 0.0,
			], dtype = np.float32)

		self.vertex_buffer = vk_memory.Buffer(
			physical_device, 
			logical_device, 
			vertices.nbytes, 
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			vertices
		)

	def destroy(self):
		self.vertex_buffer.destroy()


class MultiMesh(Mesh):
	def __init__(self, physical_device, logical_device, vertices:list[np.ndarray] = []) -> None:
		# TODO edit vertices ensure the component counts are the same?
		# TODO add indices
		# TODO add better control over vertex layout/data

		final_vertices = np.concatenate(vertices, dtype = np.float32)
		self.sizes = np.array([v.size // 5 for v in vertices], dtype = np.int32) # the '// 5' should be replaced
		self.offsets = np.cumsum(self.sizes, dtype = np.int32) - self.sizes # removes it's own starting size to get the starting positions

		super().__init__(physical_device, logical_device, final_vertices)


# this is very no me gusta
def get_pos_color_binding_description():

	return VkVertexInputBindingDescription(
		binding = 0, stride = 20, inputRate = VK_VERTEX_INPUT_RATE_VERTEX
	)

def get_pos_color_attribute_descriptions():

	return (
		VkVertexInputAttributeDescription( # 2d position
			binding = 0, location = 0,
			format = VK_FORMAT_R32G32_SFLOAT,
			offset = 0
		),
		VkVertexInputAttributeDescription( # rgb color
			binding = 0, location = 1,
			format = VK_FORMAT_R32G32B32_SFLOAT,
			offset = 8
		),
	)