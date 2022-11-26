from . import *

class Mesh:
	def __init__(self, physical_device, logical_device, vertices = None) -> None:
		self.logical_device = logical_device

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

class MultiMesh:
	def __init__(self, physical_device, logical_device, vertices = []) -> None:
		pass
		# TODO multimesh is used for indirect draw calls

		


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