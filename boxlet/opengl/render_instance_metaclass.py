from typing import Generic, TypeVar
from OpenGL.GL import *
from ctypes import c_void_p, c_float
import numpy as np
from sys import maxsize
import bisect


class RenderInstancePropertyFloats:
	def __init__(self, size, offset, stride) -> None:
		self._stride = stride
		self._offsets = np.arange(size) + offset

	def __get__(self, instance:'RenderInstance', owner):
		return instance.owner._data[self._offsets + self._stride * instance.id]
		
	def __set__(self, instance:'RenderInstance', value):
		r = self._offsets + self._stride * instance.id
		instance.owner._update_range = [
			min(r[0], instance.owner._update_range[0]),
			max(r[-1], instance.owner._update_range[1])
		]
		instance.owner._data[r] = value


class RenderInstancePropertyMatrix4:
	def __init__(self, offset, stride) -> None:
		self._stride = stride
		self._offsets = np.arange(16) + offset

	def __get__(self, instance:'RenderInstance', owner):
		return instance.owner._data[self._offsets + self._stride * instance.id].reshape((4,4))
		
	def __set__(self, instance:'RenderInstance', value):
		r = self._offsets + self._stride * instance.id
		instance.owner._update_range = [
			min(r[0], instance.owner._update_range[0]),
			max(r[-1], instance.owner._update_range[1])
		]
		instance.owner._data[r] = value.reshape((16,))


class RenderInstanceListProperty:
	def __init__(self, name) -> None:
		self._name = name

	def __get__(self, instance:'RenderInstance', owner):
		return getattr(instance.owner, self._name)

	def __set__(self, instance:'RenderInstance', value):
		setattr(instance.owner, self._name, value)


class RenderInstanceMetaclass(type):
	def __new__(cls, clsname, bases, attrs:dict[str], **kwargs):
		vars:list[tuple[str, tuple[tuple, int]]] = []
		total = 0

		# collects all variables
		for k, v in attrs.items():
			if not k.startswith('_') and isinstance(v, (tuple, list)):
				vars.append((k, v))
				if isinstance(v[0], str):
					if v[0] == 'mat4':
						total += 16
				else:
					total += len(v[0]) if isinstance(v[0], (list, tuple)) else 1

		vars.sort(key = lambda kv: kv[1][1])

		running_total = 0
		bind_data:dict[int, list[int, int]] = {} # shader_location : [size, offset]
		attrs['_bind_defaults'] = []
		
		for k, (d, loc) in vars:
			if isinstance(d, str):
				if d == 'mat4':
					attrs[k] = RenderInstancePropertyMatrix4(running_total, total)

					for i in range(4):
						bind_data[loc + i] = (4, running_total + i * 4)

					running_total += 16

					attrs['_bind_defaults'].extend([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]) 
					# identity matrix is the default, maybe allow for custom default

			else:
				s = len(d) if isinstance(d, (list, tuple)) else 1
				attrs[k] = RenderInstancePropertyFloats(s, running_total, total)

				if loc not in bind_data:
					bind_data[loc] = (s, running_total)
				else:
					bind_data[loc] = (bind_data[loc][0] + s, bind_data[loc][1])

				running_total += s

				attrs['_bind_defaults'].extend(d)

		attrs['_bind_data'] = bind_data
		attrs['_bind_stride'] = total	
		
		return super().__new__(cls, clsname, bases, attrs)


T = TypeVar('T', bound='RenderInstance')
class RenderInstanceList(Generic[T]):
	def __init__(self, cls:T, data_vbo, renderer = None):	
		self._cls = cls
		self._instances:list[T] = []
		self._data = np.zeros(0, np.float32)
		self._data_vbo = data_vbo
		self._update_range = [maxsize, -1]
		self._update_full = False # if set to true, sets the full set of data
		self.renderer = renderer # TODO remove this

		self._free_indices = list()
		self._to_delete = set()
		self.instance_count = 0
		self._instance_total_space = 0

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

		r = self._cls.get_stride_range(id)
		self._data[r] = self._cls.get_defaults()
		self._update_range = [
			min(r[0], self._update_range[0]),
			max(r[-1], self._update_range[1])
		]

		for k,v in kwargs.items():
			setattr(new_inst, k, v)

		return new_inst

	def _expand_data(self, amount):
		self._free_indices.extend(range(self._instance_total_space, self._instance_total_space + amount))
		self._instance_total_space += amount
		# self.data = np.append(self.data, np.tile(self.cls.get_defaults(), amount)).astype(np.float32)
		self._data = np.append(self._data, [0] * (amount*self._cls._bind_stride)).astype(np.float32)
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

				r = self._cls.get_stride_range(i)
				self._data[r] = self._data[self._cls.get_stride_range(inst.id)]
				inst.id = i

				# must be 'is None'
				if mi is None: mi = r[0]
				ma = r[-1]

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
			glBindBuffer(GL_ARRAY_BUFFER, self._data_vbo)
			glBufferSubData(GL_ARRAY_BUFFER, sizeof(c_float) * a, sizeof(c_float) * (b - a), self._data[a:b])
			self._update_range = [maxsize, -1]
			# this method is a bit weak to updates that include few bytes, but from opposite ends of the data


class RenderInstance(metaclass = RenderInstanceMetaclass):
	def __init__(self, owner:RenderInstanceList, id) -> None:
		self.owner = owner
		self.id = id

	def destroy(self):
		self.owner.destroy_instance(self.id)

	@classmethod
	def bind_new_vbo(cls):
		""" 
		Generates a VBO to hold data for all instances of the class and binds it to the current VAO
		"""
		data_vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, data_vbo)
		glBufferData(GL_ARRAY_BUFFER, np.zeros(0, np.float32), GL_STREAM_DRAW) # just in case it needs something to start with

		for loc, (si, off) in cls._bind_data.items():
			glVertexAttribPointer(loc, si, GL_FLOAT, GL_FALSE, sizeof(c_float) * cls._bind_stride, c_void_p(sizeof(c_float) * off)) 
			glEnableVertexAttribArray(loc)
			glVertexAttribDivisor(loc, 1)
		
		return data_vbo
	
	@classmethod
	def get_defaults(cls):
		return cls._bind_defaults

	@classmethod
	def get_stride_range(cls, id:int):
		return np.arange(cls._bind_stride) + cls._bind_stride * id

	@classmethod
	def new_instance_list(cls:type[T], renderer = None) -> RenderInstanceList[T]:
		"""
		Creates a new render instance manager and binds a vbo for the data to the current vao.
		"""
		return RenderInstanceList(cls, cls.bind_new_vbo(), renderer)

