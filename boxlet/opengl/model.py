from OpenGL.GL import *
import numpy as np
from ctypes import sizeof, c_float, c_void_p, c_int

class Model:
	def __init__(self, vertex = [], index = [], dim = 2) -> None:
		self._vertex_data = np.array(vertex or [-0.5, -0.5, 0, 0,  -0.5, 0.5, 0, 1,  0.5, 0.5, 1, 1,  0.5, -0.5, 1, 0], np.float32)
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

	def bind(self):
		'Binds vertex positions to location 0 in the array buffer, vertex UV coordinates to location 1 in the array buffer, and the indicies to the element array buffer.'
		
		# TODO add parameters to allow customization of binding things other than vertex position or uv coordinate

		# Doesn't create buffer unless the model is actually bound
		if self.vbo is None:
			self._gen_buffer()
		
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

		# parts of the vbo is only bound to the vao here ...
		# glVertexAttribPointer(index, size, type, normalized, stride, pointer)
		glVertexAttribPointer(0, self.dim, GL_FLOAT, GL_FALSE, sizeof(c_float)*self.size, c_void_p(0))
		glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, sizeof(c_float)*self.size, c_void_p(sizeof(c_float)*self.dim))
			#essentaily, data[(pointer + x)::stride] for x in range(size)
		# https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml

		glEnableVertexAttribArray(0)
		glEnableVertexAttribArray(1)

		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo) # ebo is bound to the vao here


	# def __del__(self):
	# 	glDeleteVertexArrays(1, [self.vbo])
	# 	glDeleteBuffers(2, [self.vao, self.ebo])

	@classmethod
	def load_obj(cls, file):
		with open(file, 'r') as file:

			data = {'v':[], 'vn':[], 'vt':[]}
			vertex:list[float] = []
			index:list[int] = []
			index_dict = {}

			for line in file:
				l = line.split(' ')
				if l[0] in {'v', 'vn', 'vt'}:
					data[l[0]].append([float(f) for f in l[1:]])
				
				if l[0] == 'f':
					for index_data in l[1:]:
						vd = index_data.split('/')
						ind = (int(vd[0])-1, int(vd[1])-1)

						# if the pairing doesn't already exist in the list of vertices
						if ind not in index_dict:
							i = len(index_dict)
							index_dict[ind] = i
							vertex.extend(data['v'][ind[0]])
							vertex.extend(data['vt'][ind[1]])

						index.append(index_dict[ind])

			return cls(vertex = vertex, index = index, dim = len(data['v'][0]))


class MultiModel:
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

		# TODO add parameters to allow customization of binding things other than vertex position or uv coordinate

		# Doesn't create buffer unless the model is actually bound
		if self.vbo is None:
			self._gen_buffer()
		
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

		glVertexAttribPointer(0, self.dim, GL_FLOAT, GL_FALSE, sizeof(c_float)*self.size, c_void_p(0))
		glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, sizeof(c_float)*self.size, c_void_p(sizeof(c_float)*self.dim))

		glEnableVertexAttribArray(0)
		glEnableVertexAttribArray(1)

		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo) # ebo is bound to the vao here

