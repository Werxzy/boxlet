import numpy as np


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
# TODO add compatability for double

def gen_dtype(struct):
	'''
	Generates a numpy data type based on a given information.

	Follows std140.
	'''

	names = []
	formats = []
	offsets = []
	item_size = 0
	alignment = 4

	def get_needed_offset(align, current_size):
		return (align*16 - current_size) % align

	for v in struct:
		if isinstance(v[1], list): # struct
			f, s, a = gen_dtype(v[1])
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
	# TODO ??? instead of 16, maybe use alignment, not sure what a struct of 3 vec2s is suppose to look like yet

	return np.dtype({'names' : names, 'formats' : formats, 'offsets' : offsets, 'itemsize' : item_size}), item_size, alignment

if __name__ == '__main__':
	structure = [
		('model', 'mat4'),
		('colors', 'vec4', 4), # array of vectors
		('other', [ # struct
			('pos', 'vec2'),
			('size', 'vec2'),
		]), 
		# ], 16) 
		# can be array of structs
	]
	data_type, _, _ = gen_dtype(structure)


