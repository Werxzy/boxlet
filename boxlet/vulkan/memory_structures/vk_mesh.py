from ..vk_module import *
from .. import *


class Mesh(TrackedInstances):
	def __init__(self, vertices:dict[str, list[float]] = None, indices:list[int] = None, dim = 2, component_counts = {}) -> None:
		if vertices is None:
			vertices = {
				'position' : [-0.5,-0.5, -0.5,0.5, 0.5,0.5, 0.5,-0.5],
				'texcoord' : [0,0, 0,1, 1,1, 1,0],
				'normal' : [0,0, 0,0, 0,0, 0,0],
				}

		if indices is None:
			indices = np.array([0,1,2, 0,2,3], dtype = np.int32)

		self.stride = 0
		self.offset_data = {}

		data_format = []
		component_counts = {
			'position' : 0,
			'texcoord' : 2,
			'normal' : 0,
		} | component_counts

		component_counts = {
			name : count or dim
			for name, count in component_counts.items()
		}

		vertex_count = len(vertices['position']) // (component_counts['position'] or dim)

		for name in vertices:
			count = component_counts[name]
			data_format.append((name, f'({count},)f4'))
			# currently forces vertex data types to floats

			if count == 1:
				vk_format = VK_FORMAT_R32_SFLOAT
			elif count == 2:
				vk_format = VK_FORMAT_R32G32_SFLOAT
			elif count == 3:
				vk_format = VK_FORMAT_R32G32B32_SFLOAT
			elif count == 4:
				vk_format = VK_FORMAT_R32G32B32A32_SFLOAT

			self.offset_data[name] = (vk_format, self.stride)
			self.stride += count * 4

		self.vertex_dtype = np.dtype(data_format)

		vertex_data = np.array([0] * vertex_count, self.vertex_dtype)
		for name, values in vertices.items():
			vertex_data[name] = np.array(values, np.float32).reshape((-1, component_counts[name]))

		# this is primarily to have data calculated, but not loaded to the gpu
		self._vertices_data = vertex_data
		self._indices_data = indices
		self.vertex_buffer = None
		self.index_buffer = None

	def init_buffers(self):
		# initializes the buffers only when they are actually used
		# this is so that things like MultiMesh can use them beforehand

		if self.vertex_buffer: return

		self.vertex_buffer = vk_memory.Buffer(
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			self._vertices_data
		)

		self.index_buffer = vk_memory.Buffer(
			VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
			self._indices_data 
		)

	def on_destroy(self):
		if not self.vertex_buffer: return
		
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
			indexType = VK_INDEX_TYPE_UINT32
		)

	def get_descriptions(self, attr:list[tuple[str, int]], binding = 0):
		bind_desc = [
			VkVertexInputBindingDescription(
				binding = binding, stride = self.stride, inputRate = VK_VERTEX_INPUT_RATE_VERTEX
			)
		]

		attr_desc = [
			VkVertexInputAttributeDescription( # rgb color
				binding = binding, location = loc,
				format = self.offset_data[name][0],
				offset = self.offset_data[name][1]
			)
			for name, loc in attr
		]

		return bind_desc, attr_desc

	@staticmethod
	def gen_cube(size = 1):
		return Mesh(
			vertices = {
				'position' : np.array([
					 1,-1,-1,	 1, 1,-1,	 1,-1, 1,	 1, 1, 1,
					-1, 1,-1,	-1, 1, 1,	 1, 1,-1,	 1, 1, 1,
					-1,-1, 1,	 1,-1, 1,	-1, 1, 1,	 1, 1, 1,
					-1,-1,-1,	-1,-1, 1,	-1, 1,-1,	-1, 1, 1,
					-1,-1,-1,	 1,-1,-1,	-1,-1, 1,	 1,-1, 1,
					-1,-1,-1,	-1, 1,-1,	 1,-1,-1,	 1, 1,-1,
				]) * size,
				'texcoord' : [
					0,0, 1,0, 0,1, 1,1,
					0,0, 0,1, 1,0, 1,1,
					0,0, 1,0, 0,1, 1,1,
					0,0, 1,0, 0,1, 1,1,
					0,0, 0,1, 1,0, 1,1,
					0,0, 1,0, 0,1, 1,1,
				]
			},
			indices = [
				0,1,2, 1,3,2, 4,5,6, 5,7,6, 
				8,9,10, 9,11,10, 12,13,14, 13,15,14, 
				16,17,18, 17,19,18, 20,21,22, 21,23,22],
			dim = 3)

	@staticmethod
	def gen_quad_2d(low = -1, high = 1):
		return Mesh(
			vertices = {
				'position':[
					low,low, low,high, high,high, high,low
				], 
				'texcoord':[
					0,0, 0,1, 1,1, 1,0
				],
			},
			indices = [0,1,2, 0,2,3],
			dim = 2) 

	@staticmethod
	def gen_quad_3d(low = -1, high = 1):
		return Mesh(
			vertices = {
				'position':[
					low,low,0, low,high,0, high,high,0, high,low,0
				], 
				'texcoord':[
					0,0, 0,1, 1,1, 1,0
				],
			},
			indices = [0,1,2, 0,2,3],
			dim = 3) 


class MultiMesh(Mesh):
	def __init__(self, meshes:list[Mesh]) -> None:	
		assert all(m.vertex_dtype == meshes[0].vertex_dtype for m in meshes)
		# all data types need to match
		# TODO find gaps and fill data with 0s
		#	then probably notify that there were gaps

		self.vertex_dtype = meshes[0].vertex_dtype
		self.stride = meshes[0].stride
		self.offset_data = meshes[0].offset_data
		self.vertex_buffer = None
		self.index_buffer = None

		vertices = [m._vertices_data for m in meshes]
		indices = [m._indices_data for m in meshes]

		final_vertices = np.concatenate(vertices)
		final_indices = np.concatenate(indices, dtype = np.int32)

		sizes = np.array([len(v) for v in vertices], dtype = np.int32) # the '// 5' should be replaced
		self.vertex_offsets = np.cumsum(sizes, dtype = np.int32) - sizes # removes it's own starting size to get the starting positions

		self.index_counts = np.array([len(ind) for ind in indices], dtype = np.int32)
		self.index_offsets = np.cumsum(self.index_counts, dtype = np.int32) - self.index_counts

		self.mesh_count = len(vertices)

		self._vertices_data = final_vertices
		self._indices_data = final_indices

		# vertex_buffer[index_buffer[i + index_offsets[m]] + vertex_offets[m]]
		# i = range(index_counts[m])
		# m = model id

