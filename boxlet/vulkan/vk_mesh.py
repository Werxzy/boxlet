from . import *

class Mesh:
	def __init__(self, physical_device, logical_device, vertices = None, indices = None) -> None:

		if vertices is None:
			vertices = np.array([
				0.0, -0.05, 0.0, 1.0, 0.0,
				0.05, 0.05, 0.0, 1.0, 0.0,
				-0.05, 0.05, 0.0, 1.0, 0.0,
			], dtype = np.float32)

		if indices is None:
			indices = np.array([
				0, 1, 2,
			], dtype = np.int32)

		self.vertex_buffer = vk_memory.Buffer(
			physical_device, 
			logical_device, 
			vertices.nbytes, 
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			vertices
		)

		self.index_buffer = vk_memory.Buffer(
			physical_device, 
			logical_device, 
			indices.nbytes, 
			VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
			indices
		)

	def destroy(self):
		self.vertex_buffer.destroy()
		self.index_buffer.destroy()

	def bind(self, command_buffer):
		vkCmdBindVertexBuffers(
			commandBuffer = command_buffer, firstBinding = 0, bindingCount = 1,
			pBuffers = [self.vertex_buffer.buffer],
			pOffsets = (0,)
		)

		vkCmdBindIndexBuffer(
			commandBuffer = command_buffer, 
			buffer = self.index_buffer.buffer,
			offset = 0,
			indexType = VK_INDEX_TYPE_UINT32 # 16 bit might be more efficient in larger loads
		)


class MultiMesh(Mesh):
	def __init__(self, physical_device, logical_device, vertices:list[np.ndarray] = [], indices:list[np.ndarray] = []) -> None:
		# TODO edit vertices ensure the component counts are the same?
		# TODO add better control over vertex layout/data

		final_vertices = np.concatenate(vertices, dtype = np.float32)
		final_indices = np.concatenate(indices, dtype = np.int32)

		sizes = np.array([v.size // 5 for v in vertices], dtype = np.int32) # the '// 5' should be replaced
		self.vertex_offsets = np.cumsum(sizes, dtype = np.int32) - sizes # removes it's own starting size to get the starting positions

		self.index_counts = np.array([ind.size for ind in indices], dtype = np.int32)
		self.index_offsets = np.cumsum(self.index_counts, dtype = np.int32) - self.index_counts

		print(self.index_offsets)

		# vertex_buffer[index_buffer[i + index_offsets[m]] + vertex_offets[m]]
		# i = range(index_counts[m])
		# m = model id

		super().__init__(physical_device, logical_device, final_vertices, final_indices)


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