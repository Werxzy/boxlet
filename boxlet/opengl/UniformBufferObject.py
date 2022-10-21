import numpy as np

vec4 = np.dtype('(4,)f4')
vec3 = np.dtype('(3,)f4')
light_data = np.dtype([('position', vec4), ('direction', vec4), ('color', vec4)])
d = np.dtype([('light_count','i4'), ('data', light_data, 16)])
# d = np.dtype([('light_count','i4'), ('position', vec4, 16)])

print(d)

a = np.array([(0,0)],d)
# print(a)
# print(a[0])
# print(a[0]['data'])
# print(a[0]['data'][0])
# print(a[0]['data'][0]['position'])
# print(a.strides)
# print(a.strides[0] / 4)
b = a[0]
b['light_count'] = 2
c = a[0]['data'][0]
c['position'] = [1,2,3,4]
a[0]['data'][1]['position'] = c['position']
c['position'] = [5,5,5,5]

d = a[0]['data']['direction']
d[0] = [2,2,2,2]

e = a[0]['data']['position']
e[3] = [6,3,6,3]
print(a)
a[0]['data'][0] = a[0]['data'][1]

print(a)

# asdf = np.dtype([('', vec3),('', 'f4')])
# print(asdf)
# print({'names' : ['']} | {'formats' : ['(4,)f4'], 'itemsize' : 16})
# asdf = np.dtype({'names' : [''], 'formats' : ['(3,)f4'], 'itemsize' : 16})
# print(asdf)
# print(np.array([0,0], asdf)[0])
# asdf = np.dtype({'names' : [''], 'formats' : [vec3], 'itemsize' : 16})
# # asdf = np.dtype('(4,)f4')
# print(asdf)
# print(np.array([0,0], asdf)[0])
# asdf = np.dtype({
# 	'names' : ['position', 'color'],
# 	'formats' : [vec3, vec3],
# 	'offsets' : [0, 16],
# 	'itemsize' : 32
# 	})

# print(asdf)
# test = np.array([0,0], asdf)
# print(test)
# print(test[0][0])
# test[0] = [1,2,3]
# print(test)
# print(test.tobytes())
# print(len(test.tobytes()))

# asdf = np.dtype({
# 	'names' : ['position','a', 'color','b'],
# 	'formats' : [vec3, np.flexible, vec3, np.flexible],
# 	})

# print(asdf)
# print(np.zeros(1, asdf))
# print(np.zeros(1, asdf).tobytes())


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

# only going to support mat4, because the gaps on the other array types are too annoying to manage


class UBOStructProperty:
	def __init__(self, data:np.ndarray, base = True) -> None:
		super().__setattr__('attributes', set())
		super().__setattr__('other_attrs', {})
		super().__setattr__('data', data)
		super().__setattr__('base', base)
		# self.attributes = set()
		# self.other_attrs = {}
		# self.data = data

		for d in data.dtype.names:
			next_names = data[d].dtype.names

			if next_names is None:
				self.attributes.add(d)

			elif '_' in next_names:
				self.other_attrs[d] = UBOArrayProperty(data[d]['_'][0])
				print('a',data[d]['_'])

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
		try:
			if key in self.attributes:
				if self.base:
					self.data[key][0] = value
				else:
					self.data[key] = value
			else:
				self.other_attrs[key] = value
		except KeyError:
			super().__setattr__(key, value)

	def __str__(self):
		return str(self.data)

class UBOArrayProperty:
	def __init__(self, data:np.ndarray) -> None:
		self._orig_data = data
		if data[0].dtype.names is None:
			self.data = data
		else:
			self.data = [UBOStructProperty(d, False) for d in data]

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__ (self, key, item):
		self.data[key] = item

	def __str__(self):
		return str(self._orig_data)


class UniformBufferObject:

	structure = None

	def __init__(self, structure = None):
		self.structure = self.structure or structure
		self._data_type, _, _ = self._recursive_check(self.structure)
		self._numpy_data = np.zeros(1, self._data_type)
		self.data = UBOStructProperty(self._numpy_data)

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
				s *= s * v[2]
				f = np.dtype({'names' : ['_'], 'formats' : [np.dtype((f, v[2]))], 'itemsize' : s})

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

# How this should be accessed
# data.light_count = 1
# l = data.lights[0]
# l.position = [3,3,3,1]
# data.lights[0].direction = [1,0,0,0]

f = LightUniformBuffer()
print(f.data.light_count)
print(f.data.lights[0].position)
f.data.light_count = 1
l = f.data.lights[0]
l.position = [2,2,2,1]
print(f.data.light_count)
print(f.data.lights[0].position)
print(f.data.lights)
# print(f._data_type)
# print(f.data.tobytes())
# print(f.data.tobytes())
# print(f.data.data)
# print('light_count' in f.data.dtype.names, f.data.dtype.names)
# print('_' in f.data['lights'].dtype.names, f.data['lights'].dtype.names)
# print(f.data['lights']['_'].dtype.names)
# print(f.data['lights']['_']['position'].dtype.names)
# print(f.data[0].dtype)
# print(f.data.dtype)

# structobject
#	list[tuple(contained_type, starting_pos, stride_length)]
#	

# arrayobject
#	contained_type
#	starting_pos
#	stride_length
#	count