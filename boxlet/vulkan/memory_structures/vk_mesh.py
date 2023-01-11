from ...util_3d.extra import load_obj_data
from .. import Buffer, np
from ..vk_module import *


class Mesh(TrackedInstances):
	def __init__(self, vertices:dict[str, list[float]] = None, indices:list[int] = None, dim = 2, component_counts = {}, name = '') -> None:
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
		self.name = name

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

		self.index_count = len(indices)

	def init_buffers(self):
		# initializes the buffers only when they are actually used
		# this is so that things like MultiMesh can use them beforehand

		if self.vertex_buffer: return

		self.vertex_buffer = Buffer(
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			self._vertices_data
		)

		self.index_buffer = Buffer(
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

	@classmethod
	def load_obj(cls, file):
		models = [
			cls(vertices = vertices, indices = indices, dim = dim, name = name)
			for name, vertices, indices, dim
			in load_obj_data(file)
		]
		if len(models) == 1:
			return models[0]
		return models

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
			dim = 3, 
			name = 'cube'
		)

	@staticmethod
	def gen_sphere(size = 1, divisions = 3):
		# can redistribute the segments to make the sphere look rounder
		segments = np.linspace(-1, 1, divisions + 1)
		segments = np.transpose(np.meshgrid(segments, segments))
		segments = segments.reshape((-1,2))

		axis_x = [
			[1,0,0], [0,0,1], [-1,0,0], [0,0,-1], [1,0,0], [-1,0,0],
		]
		axis_y = [
			[0,1,0], [0,1,0], [0,1,0], [0,1,0], [0,0,1], [0,0,1],
		]
		all_pos = []
		for ax, ay in zip(axis_x, axis_y):
			pos = np.matmul(segments, np.array([ax, ay]))
			normal = np.cross(ax, ay)

			pos += np.tile(normal, (pos.shape[0], 1))

			pos = (pos.T / np.linalg.norm(pos, axis = 1)).T
			all_pos.append(pos)
			
		positions = np.concatenate(all_pos).flatten() * size
		texcoords = np.tile((segments + 1) * 0.5, (6, 1)).flatten()

		ind_range = np.arange(divisions)
		m = np.repeat(ind_range, divisions) * (divisions + 1) + np.tile(ind_range, divisions)
		n = m + (divisions + 1)
		m_1 = m + 1
		n_1 = n + 1

		point_count = (divisions + 1) ** 2
		face_count = (divisions) ** 2
		faces = np.repeat(np.arange(6) * point_count, face_count * 6)
		indices = np.stack([m, n, n_1, m, n_1, m_1], axis = -1).flatten()
		indices = faces + np.tile(indices, 6)

		return Mesh(
			{
				'position' : positions,
				'texcoord' : texcoords
			},
			indices,
			dim = 3,
			name = 'sphere'
		)


	@staticmethod
	def gen_quad_2d(low = -1, high = 1, flip = False):
		return Mesh(
			vertices = {
				'position':[
					low,low, low,high, high,high, high,low
				], 
				'texcoord':[
					0,0, 0,1, 1,1, 1,0
				],
			},
			indices = [0,2,1, 0,3,2] if flip else [0,1,2, 0,2,3],
			dim = 2,
			name = 'quad'
		) 

	@staticmethod
	def gen_quad_3d(low = -1, high = 1, flip = False):
		return Mesh(
			vertices = {
				'position':[
					low,low,0, low,high,0, high,high,0, high,low,0
				], 
				'texcoord':[
					0,0, 0,1, 1,1, 1,0
				],
			},
			indices = [0,2,1, 0,3,2] if flip else [0,1,2, 0,2,3],
			dim = 3,
			name = 'quad'
		) 


class MultiMesh(Mesh):
	def __init__(self, meshes:list[Mesh]) -> None:	
		if not all(m.vertex_dtype == meshes[0].vertex_dtype for m in meshes):
			
			# merges all of the dtypes together
			# if a name only exists in one dtype, 
			# 	all other meshes will set it to 0
			# if a name exists in multiple, 
			# 	the selected dtype will be the longest one
			new_data_format:dict[str, np.dtype] = {}
			for m in meshes:
				for name in m.vertex_dtype.names:
					dt = m.vertex_dtype[name]
					if (name not in new_data_format 
						or new_data_format[name].itemsize < dt.itemsize
						):
						new_data_format[name] = dt

			self.vertex_dtype = np.dtype(list(new_data_format.items()))
			self.stride = 0
			self.offset_data = {}

			# creates the new offset and stride data
			for name in self.vertex_dtype.names:
				size = self.vertex_dtype[name].itemsize

				if size == 4:
					vk_format = VK_FORMAT_R32_SFLOAT
				elif size == 8:
					vk_format = VK_FORMAT_R32G32_SFLOAT
				elif size == 12:
					vk_format = VK_FORMAT_R32G32B32_SFLOAT
				elif size == 16:
					vk_format = VK_FORMAT_R32G32B32A32_SFLOAT

				self.offset_data[name] = (vk_format, self.stride)
				self.stride += size

			# creates numpy arrays in the new dtype format
			vertices = []
			for m in meshes:
				old_dtype = m._vertices_data.dtype
				new_vert = np.zeros(m._vertices_data.shape, self.vertex_dtype)

				# for each subtype that overlaps between the old and new
				for t in old_dtype.names:
					if t in self.vertex_dtype.names:
						# fit in the old data
						new_vert[t][:, 0:old_dtype[t].shape[0]] = m._vertices_data[t]

				vertices.append(new_vert)

		else:
			self.vertex_dtype = meshes[0].vertex_dtype
			self.stride = meshes[0].stride
			self.offset_data = meshes[0].offset_data

			vertices = [m._vertices_data for m in meshes]

		indices = [m._indices_data for m in meshes]

		self.vertex_buffer = None
		self.index_buffer = None

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

		self.name = 'multi'

		self.names = {
			model.name : i for i, model in enumerate(meshes)
		}

