def load_obj_data(file):
	def try_int(s):
		try:
			return int(s)-1
		except ValueError:
			return -1

	with open(file, 'r') as file:

		data = {'v':[], 'vt':[], 'vn':[]}
		vertex = {'position' : [], 'texcoord' : [], 'normal' : []}
		index:list[int] = []
		index_dict = {}

		for line in file:
			l = line.split(' ')
			if l[0] in {'v', 'vn', 'vt'}:
				data[l[0]].append([float(f) for f in l[1:]])
			
			if l[0] == 'f':
				for index_data in l[1:]:
					ind = tuple(try_int(vd) for vd in index_data.split('/'))

					# if the pairing doesn't already exist in the list of vertices
					if ind not in index_dict:
						index_dict[ind] = len(index_dict)
						for ind_2, (name, obj_name) in zip(ind, [('position', 'v'), ('texcoord', 'vt'), ('normal', 'vn')]):
							vertex[name].extend(data[obj_name][ind_2])

					index.append(index_dict[ind])

	return vertex, index, len(data['v'][0])