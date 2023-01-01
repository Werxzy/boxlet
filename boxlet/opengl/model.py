from ctypes import c_float, c_int, c_void_p, sizeof

from OpenGL.GL import *

from .. import *

from ..util_3d.extra import load_obj_data


class Model:
	def __init__(self, vertex = None, index = [], dim = 2) -> None:
		if vertex is None:
			vertex = {
				'position' : [-0.5,-0.5, -0.5,0.5, 0.5,0.5, 0.5,-0.5],
				'texcoord' : [0,0, 0,1, 1,1, 1,0],
				'normal' : [0,0, 0,0, 0,0, 0,0],
				}

		types = []
		self._stride_data:dict[str, tuple[int,int,int]] = {}
		self.vertex_stride = 0

		def add_variable(name, size):
			nonlocal self, types
			types.append((name, np.float32, size))
			byte_size = size * sizeof(c_float)
			self._stride_data[name] = (self.vertex_stride, byte_size, size)
			self.vertex_stride += byte_size

		for v, s in [('position', dim), ('texcoord', 2), ('normal', dim)]:
			if v in vertex and vertex[v] is not None and len(vertex[v]) > 0:
				add_variable(v, s)

		self._vertex_dtype = np.dtype(types)
		length = len(vertex['position']) // dim
		self._vertex_data = np.array([0] * length, self._vertex_dtype)
		for n, d in self._stride_data.items():
			self._vertex_data[n] = np.array(vertex[n]).reshape((-1,d[2]))

		self._index_data = np.array(index or [0,1,2, 0,2,3], np.int32)
		self.size = dim + 2
		self.dim = dim 
		self.index_count = self._index_data.shape[0]

		self.vbo = None
		self.ebo = None

	def _gen_buffer(self):
		self.vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
		glBufferData(GL_ARRAY_BUFFER, self._vertex_data, GL_STATIC_DRAW) 

		self.ebo = glGenBuffers(1)
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, self._index_data, GL_STATIC_DRAW) 

	def bind(self, shader:'Shader' = None, **kwargs):
		'Binds vertex positions to location 0 in the array buffer, vertex UV coordinates to location 1 in the array buffer, and the indicies to the element array buffer.'
		
		# Doesn't create buffer unless the model is actually bound
		if self.vbo is None:
			self._gen_buffer()
		
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

		if shader:
			for name, (start, _, count) in self._stride_data.items():
				if name in shader.vertex_attributes:
					index = shader.vertex_attributes[name][2]
					glVertexAttribPointer(index, count, GL_FLOAT, GL_FALSE, self.vertex_stride, c_void_p(start))
					glEnableVertexAttribArray(index)
		elif kwargs:
			for name, (start, _, count) in self._stride_data.items():
				if name in kwargs:
					index = kwargs[name]
					glVertexAttribPointer(index, count, GL_FLOAT, GL_FALSE, self.vertex_stride, c_void_p(start))
					glEnableVertexAttribArray(index)
		else:
			raise Exception('No bind points provided')

		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo) # ebo is bound to the vao here

	# def __del__(self):
	# 	glDeleteVertexArrays(1, [self.vbo])
	# 	glDeleteBuffers(2, [self.vao, self.ebo])

	@classmethod
	def load_obj(cls, file):
		vertex, index, dim = load_obj_data(file)
		return cls(vertex = vertex, index = index, dim = dim)

	@staticmethod
	def gen_cube(size = 1):
		return Model(
			vertex = {
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
			index = [0,1,2, 1,3,2, 4,5,6, 5,7,6, 8,9,10, 9,11,10, 12,13,14, 13,15,14, 16,17,18, 17,19,18, 20,21,22, 21,23,22],
			dim = 3)

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

		return Model(
			{
				'position' : positions,
				'texcoord' : texcoords
			},
			indices,
			dim = 3
		)

	@staticmethod
	def gen_quad_2d(low = -1, high = 1):
		return Model(
			vertex = {
				'position':[
					low,low, 
					low,high, 
					high,high, 
					high,low
				], 
				'texcoord':[
					0,0, 0,1, 1,1, 1,0
				],
			},
			index = [0,1,2, 0,2,3],
			dim = 2)


class MultiModel:

	# This class isn't compatible with Model yet as it doesn't apply the recent changes to Model.

	def __init__(self, *models:Model):
		# All models need to contain the same type of data.

		self.dim = models[0].dim 
		self.size = self.dim + 2
		
		vertex = []
		index = []

		self.model_locations:list[tuple[int, int]] = [] 
		self.model_dict:dict[Model, tuple[int, int]] = {}
		# list and dictionary of (element count, element start)
		
		for m in models:
			if m.dim != self.dim: 
				raise Error('Invalid model input')

			loc = (m._index_data, len(index) * sizeof(c_int))
			self.model_locations.append(loc)
			self.model_dict[m] = loc

			vertex.append(m._vertex_data)
			index.append(m._index_data)

		self._vertex_data = np.array(vertex, np.float32)
		self._index_data = np.array(index, np.int32)
		self._index_count = self._index_data.shape[0]

		self.vbo = None
		self.ebo = None

	def _gen_buffer(self):
		self.vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
		glBufferData(GL_ARRAY_BUFFER, self._vertex_data, GL_STATIC_DRAW) 

		self.ebo = glGenBuffers(1)
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, self._index_data, GL_STATIC_DRAW) 

	def bind(self):
		'Binds vertex positions to location 0 in the array buffer, vertex UV coordinates to location 1 in the array buffer, and the indicies to the element array buffer.'
		# currently just a copy of Model.bind()

		# add parameters to allow customization of binding things other than vertex position or uv coordinate

		# Doesn't create buffer unless the model is actually bound
		if self.vbo is None:
			self._gen_buffer()
		
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

		glVertexAttribPointer(0, self.dim, GL_FLOAT, GL_FALSE, sizeof(c_float)*self.size, c_void_p(0))
		glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, sizeof(c_float)*self.size, c_void_p(sizeof(c_float)*self.dim))

		glEnableVertexAttribArray(0)
		glEnableVertexAttribArray(1)

		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo) # ebo is bound to the vao here

