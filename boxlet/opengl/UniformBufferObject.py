import numpy as np
from OpenGL.GL import *

DATATYPES = {
	# glsl type : (how data is stored, size, alignment)
	'int' : (np.dtype('i4'),4,4),
	'ivec2' : (np.dtype('(2,)i4'),8,8),
	'ivec3' : (np.dtype('(3,)i4'),12,16),
	'ivec4' : (np.dtype('(4,)i4'),16,16),
	
	'uint' : (np.dtype('u4'),4,4),
	'uvec2' : (np.dtype('(2,)u4'),2,2),
	'uvec3' : (np.dtype('(3,)u4'),12,16),
	'uvec4' : (np.dtype('(4,)u4'),16,16),

	'float' : (np.dtype('f4'),4,4),
	'vec2' : (np.dtype('(2,)f4'),8,8),
	'vec3' : (np.dtype('(3,)f4'),12,16),
	'vec4' : (np.dtype('(4,)f4'),16,16),

	'mat4' : (np.dtype('(4,4)f4'),64,16),
}
# important to note how values are laid out
# https://ptgmedia.pearsoncmg.com/images/9780321552624/downloads/0321552628_AppL.pdf
# floats are size 1
# vec2 are size 2
# vec3 and vec4 are size 4
# size is the element type's size, rounded up to nearest 4, time the number of elements
# for structs, alignment is the same as it's largest member, 

# only going to support mat4 for now

class UBOStructProperty:
	def __init__(self, data:np.ndarray, base = None) -> None:
		super().__setattr__('attributes', set())
		super().__setattr__('other_attrs', {})
		super().__setattr__('data', data)
		super().__setattr__('base', base)
		if base is None:
			super().__setattr__('needs_to_update', True)

		for d in data.dtype.names:
			next_names = data[d].dtype.names

			if next_names is None:
				self.attributes.add(d)
			elif '_' in next_names:
				self.other_attrs[d] = UBOArrayProperty(data[d]['_'][0])
			else:
				self.other_attrs[d] = UBOStructProperty(data[d], False)

	def __getattr__(self, key):
		try:
			if key in self.attributes:
				if self.base:
					return self.data[key][0]
				else:
					return self.data[key]
			else:
				return self.other_attrs[key]
		except KeyError:
			return super().__getattribute__(key)

	def __setattr__(self, key, value):
		if key in self.attributes:
			if self.base:
				self.data[key][0] = value
			else:
				self.data[key] = value
			self._update_alert()

		elif key in self.other_attrs:
			self.other_attrs[key] = value
			self._update_alert()

		else:
			super().__setattr__(key, value)

	def _update_alert(self):
		if self.base is None:
			self.needs_to_update = True
		else:
			self.base.needs_to_update = True

	def __str__(self):
		return str(self.data)


class UBOArrayProperty:
	def __init__(self, data:np.ndarray, base = None) -> None:
		self._orig_data = data
		self.base = None
		if data[0].dtype.names is None:
			self.data = data
		else:
			self.data = [UBOStructProperty(d, False) for d in data]

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__ (self, key, item):
		if isinstance(item, UBOStructProperty) and self.data[key].data.dtype == item.data.dtype:
			self._orig_data[key] = item.data
		else:
			self.data[key] = item
		self.base.needs_to_update = True

	def swap_data(self, a, b):
		self._orig_data[[a,b]] = self._orig_data[[b,a]]
		self.base.needs_to_update = True

	def swap_properties(self, a, b):
		if isinstance(self.data[a], UBOStructProperty):
			(self.data[a], self.data[b]) = (self.data[b], self.data[a])
			(self.data[a].data, self.data[b].data) = (self.data[b].data, self.data[a].data) 
			(self.data[a].other_attrs, self.data[b].other_attrs) = (self.data[b].other_attrs, self.data[a].other_attrs)

		self.swap_data(a,b)


	def __str__(self):
		return str(self._orig_data)


class UniformBufferObject:

	'The purpose of this class is to structure data so that it can be used in a uniform buffer object with layout std140'

	structure = None
	_test_without_opengl = False
	_binding_point_count = 0

	def __init__(self, structure = None):
		self.structure = self.structure or structure
		self._data_type, _, _ = self._recursive_check(self.structure)
		self._numpy_data = np.zeros(1, self._data_type)
		self.data = UBOStructProperty(self._numpy_data)

		if not self._test_without_opengl:
			self.binding_point = self.new_binding_point()
			self.uniform_buffer = glGenBuffers(1)

			glBindBuffer(GL_UNIFORM_BUFFER, self.uniform_buffer)
			glBindBufferBase(GL_UNIFORM_BUFFER, self.binding_point, self.uniform_buffer)
			glBufferData(GL_UNIFORM_BUFFER, self._numpy_data.itemsize, self._numpy_data, GL_DYNAMIC_DRAW)


	def bind(self, shader, index):
		# Earlier the following needs to be called
		# index = glGetUniformBlockIndex(shader.program, name)

		glUniformBlockBinding(shader.program, index, self.binding_point)

	def update_data(self):
		if self.data.needs_to_update:
			self.data.needs_to_update = False
			glBindBuffer(GL_UNIFORM_BUFFER, self.uniform_buffer)
			glBufferData(GL_UNIFORM_BUFFER, self.light_data.strides[0], self.light_data, GL_DYNAMIC_DRAW)
			# it would be a bit too difficult in this version to use glBufferSubData
			
	@staticmethod
	def new_binding_point():
		UniformBufferObject._binding_point_count += 1
		return UniformBufferObject._binding_point_count

	@staticmethod
	def _recursive_check(struct):
		names = []
		formats = []
		offsets = []
		item_size = 0
		alignment = 4

		def get_needed_offset(align, current_size):
			return (align*16 - current_size) % align

		for v in struct:
			if isinstance(v[1], list): # struct
				f, s, a = UniformBufferObject._recursive_check(v[1])
			else: # value
				f, s, a = DATATYPES[v[1]]

			if len(v) == 3: # array
				a = max(16, a)
				am = get_needed_offset(16, a)
				a += am
				s += am

				f = np.dtype({'names':['_'], 'formats':[f], 'itemsize':s})
				f = np.dtype((f, v[2]))
				s *= v[2]

			names.append(v[0]) # append name
			formats.append(f) # append dtype
			
			item_size += get_needed_offset(a, item_size) # gets the offset needed to add to fit the dtype
			offsets.append(item_size) # append the current offset
			item_size += s # increase the item size
			
			alignment = max(alignment, a)

		item_size += get_needed_offset(16, item_size)
		# TODO ??? the instead of 16, maybe use alignment, not sure what a struct of 3 vec2s is suppose to look like yet

		return np.dtype({'names' : names, 'formats' : formats, 'offsets' : offsets, 'itemsize' : item_size}), item_size, alignment


class LightUniformBuffer(UniformBufferObject):
	structure = [
		('light_count', 'int'),
		('lights', [
			('position', 'vec4'),
			('direction', 'vec4'),
			('color', 'vec4'),
		], 16)
	]


if __name__ == '__main__':
	UBOStructProperty._test_without_opengl = True

	# Buffer initialized with all 0s
	f = LightUniformBuffer()

	# values can be assigned
	# single component values need to be assigned with a single value
	f.data.light_count = 2

	# values in an array of structs can be assigned to like normal
	# multiple component types need to be assigned with an array
	f.data.lights[0].position = [2,2,2,2]

	# stucts can be stored like objects and their properties assigned to normally
	l = f.data.lights[1]
	l.position = [1,1,1,1]

	# when assigning from one struct to another of the type while using the index, 
	# the data values will be copied over.
	f.data.lights[2] = l

	# attributes of structs will also affect the data's values
	# NOTE however, this is pointing to the memory location and not the struct reference
	#	This is more apparent between swap_data() and swap_properties()
	pos = l.position
	pos += 2
	# print(l.position) # will print [3,3,3,3]

	# values in an array can be easily swapped without messing with
	# This will affect previous references
	f.data.lights.swap_data(1, 3)
	# print(l.position, pos) # will both print [0,0,0,0]

	# structs themselves can be swapped without affecting any reference's data
	f.data.lights.swap_properties(1, 3)
	print(l.position) # will still print [0,0,0,0]
	# print(pos) # BUT this will now print [3,3,3,3], since pos is pointing to the position in raw data
