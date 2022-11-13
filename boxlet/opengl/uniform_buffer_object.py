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

class UBOStruct:
	def __init__(self, data:np.ndarray, base = None) -> None:
		super().__setattr__('attributes', set())
		super().__setattr__('other_attrs', {})
		self._data = data
		self._base = base or self
		if base is None:
			self.needs_to_update = False

		for d in data.dtype.names:
			next_names = data[d].dtype.names

			if next_names is None:
				self.attributes.add(d)
			elif '_' in next_names:
				self.other_attrs[d] = UBOArray(data[d]['_'][0], self._base)
			else:
				self.other_attrs[d] = UBOStruct(data[d], self._base)

	def __getattr__(self, key):
		try:
			if key in self.attributes:
				if self._base is self:
					return self._data[key][0]
				else:
					return self._data[key]
			else:
				return self.other_attrs[key]
		except KeyError:
			return super().__getattribute__(key)

	def __setattr__(self, key, value):
		if key in self.attributes:
			if self._base is self:
				self._data[key][0] = value
			else:
				self._data[key] = value
			self._update_alert()

		elif key in self.other_attrs:
			self.other_attrs[key] = value
			self._update_alert()

		else:
			super().__setattr__(key, value)

	def _update_alert(self):
		self._base.needs_to_update = True

	def __str__(self):
		return str(self._data)


class UBOArray:
	def __init__(self, data:np.ndarray, base:UBOStruct) -> None:
		self._orig_data = data
		self.base = base
		if data[0].dtype.names is None:
			self._data = data
		else:
			self._data = [UBOStruct(d, self.base) for d in data]

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__ (self, key, item):
		if isinstance(item, UBOStruct) and self._data[key]._data.dtype == item._data.dtype:
			self._orig_data[key] = item._data
		else:
			self._data[key] = item
		self.base.needs_to_update = True

	def swap_data(self, a, b):
		self._orig_data[[a,b]] = self._orig_data[[b,a]]
		self.base.needs_to_update = True

	def swap_properties(self, a, b):
		if isinstance(self._data[a], UBOStruct):
			(self._data[a], self._data[b]) = (self._data[b], self._data[a])
			(self._data[a]._data, self._data[b]._data) = (self._data[b]._data, self._data[a]._data) 
			(self._data[a].other_attrs, self._data[b].other_attrs) = (self._data[b].other_attrs, self._data[a].other_attrs)

		self.swap_data(a,b)

	def __str__(self):
		return str(self._orig_data)


class UniformBufferObject:

	'The purpose of this class is to structure data so that it can be used in a uniform buffer object with layout std140'

	structure = None
	_test_without_opengl = False
	_binding_point_count = 0

	def __init__(self, structure = None, create_opengl_buffer = True):
		self.structure = self.structure or structure
		self._data_type, _, _ = self._recursive_check(self.structure)
		self._numpy_data = np.zeros(1, self._data_type)
		self.data = UBOStruct(self._numpy_data)

		if create_opengl_buffer:
			self.binding_point = self.new_binding_point()
			self.uniform_buffer = glGenBuffers(1)

			glBindBuffer(GL_UNIFORM_BUFFER, self.uniform_buffer)
			glBindBufferBase(GL_UNIFORM_BUFFER, self.binding_point, self.uniform_buffer)
			glBufferData(GL_UNIFORM_BUFFER, self._numpy_data.itemsize, self._numpy_data, GL_DYNAMIC_DRAW)

	def bind(self, shader, index):
		# Earlier the following, or something similar, needs to be called
		# index = glGetUniformBlockIndex(shader.program, name)

		glUniformBlockBinding(shader.program, index, self.binding_point)

	def update_data(self):
		if self.data.needs_to_update:
			self.data.needs_to_update = False
			glBindBuffer(GL_UNIFORM_BUFFER, self.uniform_buffer)
			glBufferData(GL_UNIFORM_BUFFER, self._numpy_data.itemsize, self._numpy_data, GL_DYNAMIC_DRAW)
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
	max_light_count = 16
	structure = [
		('light_count', 'int'),
		('lights', [
			('pos_dir', 'vec4'), # represents position if .w = 1, represents direciton if .w = 0
			('color_range', 'vec4'), # .xyz = color, while .w is the light's range (if point light)
		], max_light_count)
	]

	class LightSource:
		def __init__(self, data, id, owner:'LightUniformBuffer'):
			self.data = data
			self.id = id
			self.owner = owner
		
		def destroy(self):
			self.owner.destroy(self.id)
			self.data = self.owner = self.id = None

	def __init__(self):
		super().__init__()
		self.instances = []

	def new_instance(self):
		if self.data.light_count >= self.max_light_count:
			raise Exception('No room left in Uniform Buffer Object.')

		light = LightUniformBuffer.LightSource(self.data.lights[self.data.light_count], self.data.light_count, self)
		self.instances.append(light)
		self.data.light_count += 1
		return light

	def destroy(self, id):
		self.data.light_count -= 1
		if id != self.data.light_count:
			self.data.lights.swap_properties(id, self.data.light_count)
			self.instances[id] = self.instances[self.data.light_count]
		self.instances.pop()


if __name__ == '__main__':
	# Buffer initialized with all 0s
	f = UniformBufferObject([
		('light_count', 'int'),
		('lights', [
			('position', 'vec4'),
			('color', 'vec4'),
		], 4)
	], False)

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
	assert np.all(l.position == [3,3,3,3])
	# print(l.position) # will print [3,3,3,3]

	# values in an array can be easily swapped without messing with
	# This will affect previous references
	f.data.lights.swap_data(1, 3)
	assert np.all(l.position == [0,0,0,0])
	assert np.all(pos == [0,0,0,0])
	# print(l.position, pos) # will both print [0,0,0,0]

	# structs themselves can be swapped without affecting any reference's data
	f.data.lights.swap_properties(1, 3)
	assert np.all(l.position == [0,0,0,0])
	assert np.all(pos == [3,3,3,3])
	# print(l.position) # will still print [0,0,0,0]
	# print(pos) # BUT this will now print [3,3,3,3], since pos is pointing to the position in raw data
