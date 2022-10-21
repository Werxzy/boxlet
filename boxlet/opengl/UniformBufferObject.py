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

# asdf = np.dtype([('', vec3),('', 'f4')])
# print(asdf)

asdf = np.dtype([('', vec3),('', 'f4')])

asdf = np.dtype({
	'names' : ['position', 'color'],
	'formats' : [vec3, vec3],
	'offsets' : [0, 16],
	'itemsize' : 32
	})

print(asdf)
test = np.array([0,0], asdf)
print(test.tobytes())
print(len(test.tobytes()))

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



class UBOProperty:
	def __init__(self) -> None:
		...

	def __get__(self, instance, owner):
		...
		
	def __set__(self, instance, value):
		...

class UBOArrayProperty:
	def __init__(self) -> None:
		...

	def __get__(self, instance, owner):
		...
		
	def __set__(self, instance, value):
		...
# TODO

class UniformBufferObject:
	structure = None
	def __init__(self, structure = None):
		self.structure = self.structure or structure

		self._data_type,_,_ = self._recursive_check(self.structure)

		self.data = np.zeros(1, self._data_type)

	@staticmethod
	def _recursive_check(struct):
		data_type = []
		size = 0
		offset = 0 # just the offset from 0 to 3, the size of vec4 (was planned for something else)
		alignment = 1

		def fit_whats_left(m, size, offset, data_type:list):
			if am := (m*4 - offset) % m: 
				data_type.append(('', f'({am},)f4'))
				size += am
				offset = (offset + am) % 4
			return size, offset

		for v in struct:
			if isinstance(v[1], list): # struct
				f, s, a = UniformBufferObject._recursive_check(v[1])
			else: # value
				f, s, a = DATATYPES[v[1]]

			l = len(v)
			if l == 2: # single value
				size, offset = fit_whats_left(a, size, offset, data_type)
				data_type.append((v[0], f))
			elif l == 3: # array
				size, offset = fit_whats_left(4, size, offset, data_type)
				a = 4
				if(s % a != 0):
					f = np.dtype([('', f),('', f'({a - (s%a)},)f4')])
				data_type.append((v[0], f, v[2]))
			
			size += s
			offset = (offset + s) % 4
			alignment = max(alignment, a)

		size, offset = fit_whats_left(4, size, offset, data_type) 
		# TODO ??? the instead of 4, maybe use alignment, not sure what a struct of 3 vec2s are suppose to look like yet

		return np.dtype(data_type), size, alignment


class LightUniformBuffer(UniformBufferObject):
	structure = [
		('light_count', 'int'),
		('lights', [
			('position', 'vec4'),
			('direction', 'vec4'),
			('color', 'vec4'),
		], 16)
	]

f = LightUniformBuffer()
print(f._data_type)

# structobject
#	list[tuple(contained_type, starting_pos, stride_length)]
#	

# arrayobject
#	contained_type
#	starting_pos
#	stride_length
#	count