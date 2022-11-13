from typing import TYPE_CHECKING, Generic, TypeVar
from OpenGL.GL import *
from ctypes import c_void_p, c_float
import numpy as np
from sys import maxsize
import bisect
import boxlet.opengl.extra_gl_constants as extra_gl
from itertools import chain

if TYPE_CHECKING:
	from boxlet import Shader


class RenderInstanceProperty:
	def __init__(self, name) -> None:
		self._name = name

	def __get__(self, instance:'RenderInstance', owner):
		return instance.owner._data[instance.id][self._name]
		
	def __set__(self, instance:'RenderInstance', value):
		instance.owner._update_range = [
			min(instance.id, instance.owner._update_range[0]),
			max(instance.id, instance.owner._update_range[1])
		]
		instance.owner._data[instance.id][self._name] = value


class RenderInstanceListProperty:
	# not 100% sure if I can just remove this class
	# or if there's a better way to manage uniform data
	def __init__(self, name) -> None:
		self._name = name

	def __get__(self, instance:'RenderInstance', owner):
		return instance.owner.uniform_data[self._name]
		# return getattr(instance.owner, self._name)

	def __set__(self, instance:'RenderInstance', value):
		instance.owner.uniform_data[self._name] = value
		# setattr(instance.owner, self._name, value)


class RenderInstanceMetaclass(type):
	def __new__(cls, clsname, bases, attrs:dict[str], **kwargs):
		# collects all variables
		shader_attributes:list[tuple[str, str, int, np.ndarray | None, int]] = []
		total = 0
		dtype_names = []
		dtype_formats = []
		shader_uniforms = dict()
		shader_textures = dict()

		for k, v in attrs.items():
			if not k.startswith('_') and isinstance(v, tuple):
				attr_type  = v[1]
				if v[0] == 'attrib':
					default = None
					if isinstance(attr_type, str):
						t = extra_gl.UNIFORM_SYMBOL_DICT[attr_type]
						s = extra_gl.UNIFORM_TYPE_DICT[t][2]
						if attr_type.startswith('mat4'):
							default = np.identity(4)

					elif isinstance(attr_type, list):
						s = len(attr_type)
						t = extra_gl.VECTOR_TYPES['f'][s - 1]
						default = np.array(attr_type)

					elif isinstance(attr_type, np.ndarray):
						t = attr_type.dtype.kind
						s = attr_type.size
						default = np.array(attr_type)

						if t not in extra_gl.VECTOR_TYPES:
							raise Exception('Invalid numpy type.')

						t = extra_gl.VECTOR_TYPES[t][s - 1]

					else:
						raise Exception()

					
					total += s
					shader_attributes.append((k, v[2], t, default, s, attr_type))
					dtype_names.append(k)
					dtype_formats.append(extra_gl.UNIFORM_TYPE_DICT[t][3])

				elif v[0] == 'uniform':
					shader_uniforms[v[1]] = k
					attrs[k] = RenderInstanceListProperty(k)

				elif v[0] == 'texture':
					shader_textures[v[1]] = k
					attrs[k] = RenderInstanceListProperty(k)

		full_dtype = np.dtype({'names' : dtype_names, 'formats' : dtype_formats})
		full_default = np.array([0], full_dtype)
		bind_info = []
		total *= sizeof(c_float)
		offset = 0

		for local_name, shader_name, attr_type, default, size, full_type in shader_attributes:
			attrs[local_name] = RenderInstanceProperty(local_name)
			if default is not None:
				full_default[local_name] = default
			
			if full_type == 'mat4': # matricies take up multiple locations
				for i in range(4):
					bind_info.append((shader_name, i, (size//4, extra_gl.UNIFORM_TYPE_DICT[attr_type][1], GL_FALSE, total, c_void_p(offset + i * sizeof(c_float) * 4))))
			else:
				bind_info.append((shader_name, 0, (size, extra_gl.UNIFORM_TYPE_DICT[attr_type][1], GL_FALSE, total, c_void_p(offset))))
			
			offset += size * sizeof(c_float)

		attrs['_bind_defaults'] = full_default
		attrs['_bind_stride'] = total	
		attrs['_bind_info'] = bind_info
		attrs['_bind_dtype'] = full_dtype

		attrs['_uniform_texture_info'] = shader_textures
		attrs['_uniform_info'] = shader_uniforms

		return super().__new__(cls, clsname, bases, attrs)


T = TypeVar('T', bound='RenderInstance')
class RenderInstanceList(Generic[T]):
	def __init__(self, cls:T, shaders:'tuple[Shader]|list[Shader]'):	
		self._cls = cls
		self._instances:list[T] = []
		self._data = np.zeros(0, cls._bind_dtype)
		self._data_vbo = cls.bind_new_vbo(shaders)
		self._update_range = [maxsize, -1]
		self._update_full = False # if set to true, sets the full set of data

		self._free_indices = list()
		self._to_delete = set()
		self.instance_count = 0
		self._instance_total_space = 0
		self.uniform_data = dict((u,None) for u in chain(cls._uniform_texture_info.values(), cls._uniform_info.values()))
		self.uniform_info:dict['Shader', list[tuple[str,str]]] = dict([
				(
					s, 
					[(sn, ln) for sn, ln in cls._uniform_info.items() if sn in s.uniforms]
				) 
				for s in shaders
			])
		self.uniform_texture_info:dict['Shader', list[tuple[str,str]]] = dict([
				(
					s, 
					[(sn, ln) for sn, ln in cls._uniform_texture_info.items() if sn in s.textures]
				) 
				for s in shaders
			])

		self._expand_data(16)

	# TODO make a function for creating multiple instances at once, or even one for just making room ahead of time
	def new_instance(self, **kwargs) -> T:
		if not self._free_indices:
			self._expand_data(self._instance_total_space) # Currently just double the amount every time it needs more space.
			self._update_full = True

		id = self._free_indices.pop(0)
		new_inst = self._cls(self, id)
		if id in self._to_delete:
			self._to_delete.remove(id)
			self._instances[id] = new_inst
		else:
			self._instances.append(new_inst)
		self.instance_count += 1

		r = id
		self._data[r] = self._cls.get_defaults()
		self._update_range = [
			min(r, self._update_range[0]),
			max(r, self._update_range[1])
		]

		for k,v in kwargs.items():
			setattr(new_inst, k, v)

		return new_inst

	def _expand_data(self, amount):
		self._free_indices.extend(range(self._instance_total_space, self._instance_total_space + amount))
		self._instance_total_space += amount
		self._data = np.append(self._data, np.array([0]*amount, dtype=self._data.dtype)) # TODO double check that this creates the proper space
		self._update_full = True

	def destroy_instance(self, id):
		self._to_delete.add(id)
		bisect.insort(self._free_indices, id)
		self.instance_count -= 1

	def update_data(self):
		"""
		Updates the data to the VBO.
		"""

		if self._to_delete:
			for i in sorted(self._to_delete, reverse=True):
				self._instances.pop(i)
			self._to_delete.clear()

			mi = None
			ma = 0

			for i, inst in enumerate(self._instances): # instances should preserve order
				if i == inst.id: continue

				r = i
				self._data[r] = self._data[inst.id]
				inst.id = i

				# must be 'is None'
				if mi is None: mi = r
				ma = r

			if mi is not None:
				self._update_range = [mi, ma]
			
			self._free_indices = list(range(self.instance_count, self._instance_total_space))

		if self._update_full: # updates the entire buffer object, needed if the size changes.
			self._update_full = False
			glBindBuffer(GL_ARRAY_BUFFER, self._data_vbo)
			glBufferData(GL_ARRAY_BUFFER, self._data, GL_STREAM_DRAW)
			self._update_range = [maxsize, -1]

		elif self._update_range[1] != -1: # updates part of the buffer object
			a, b = self._update_range[0], self._update_range[1] + 1
			s = self._cls._bind_stride
			glBindBuffer(GL_ARRAY_BUFFER, self._data_vbo)
			glBufferSubData(GL_ARRAY_BUFFER, s * a, s * (b - a), self._data[a:b])
			self._update_range = [maxsize, -1]
			# this method is a bit weak to updates that include few bytes, but from opposite ends of the data

	def update_uniforms(self, shader:'Shader'):
		for shader_name, local_name in self.uniform_info[shader]:
			shader.apply_uniform(shader_name, self.uniform_data[local_name])

		for shader_name, local_name in self.uniform_texture_info[shader]:
			shader.bind_texture(shader_name, self.uniform_data[local_name])


class RenderInstance(metaclass = RenderInstanceMetaclass):
	def __init__(self, owner:RenderInstanceList, id) -> None:
		self.owner = owner
		self.id = id

	def destroy(self):
		self.owner.destroy_instance(self.id)

	@classmethod
	def bind_new_vbo(cls, shaders:'tuple[Shader]|list[Shader]'):
		""" 
		Generates a VBO to hold data for all instances of the class and binds it to the current VAO
		"""

		data_vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, data_vbo)
		glBufferData(GL_ARRAY_BUFFER, np.zeros(0, np.float32), GL_STREAM_DRAW) # just in case it needs something to start with

		for name, locOffset, binds in cls._bind_info:
			for s in shaders:
				if name in s.vertex_attributes:
					loc = s.vertex_attributes[name][2] + locOffset
					glVertexAttribPointer(loc, *binds) 
					glEnableVertexAttribArray(loc)
					glVertexAttribDivisor(loc, 1)

		return data_vbo

	@classmethod
	def get_defaults(cls):
		return cls._bind_defaults

	@classmethod
	def new_instance_list(cls:type[T], *shaders:'Shader') -> RenderInstanceList[T]:
		"""
		Creates a new render instance manager and binds a vbo for the data to the current vao.
		"""
		return RenderInstanceList(cls, shaders)

