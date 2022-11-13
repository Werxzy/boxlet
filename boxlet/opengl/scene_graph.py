from math import ceil

import numpy as np

# this is a very early version that may need to switch to cython, numba, or something else

# https://www.mathworks.com/help/aeroblks/quaternionrotation.html

class Transform:

	def __init__(self, id) -> None:
		self.id = id
		self.position = [0,0,0]
		self.quaternion = [0,0,0,1]
		self.scale = [1,1,1]
		
	@property
	def position(self):
		return SceneGraph.transform_data[self.id, 0:4]

	@position.setter
	def position(self, value):
		SceneGraph.transform_data[self.id, 0:4] = value

	@property
	def quaternion(self):
		return SceneGraph.transform_data[self.id, 4:8]

	@quaternion.setter
	def quaternion(self, value):
		SceneGraph.transform_data[self.id, 4:8] = value

	@property
	def scale(self):
		return SceneGraph.transform_data[self.id, 8:11]

	@scale.setter
	def scale(self, value):
		SceneGraph.transform_data[self.id, 8:11] = value


class SceneGraph:
	
	DATA_SIZE = 11
	# 0:4 = position
	# 4:8 = quaternion
	# 8:11 = scale
	INIT_COUNT = 16

	transform_data = np.zeros((INIT_COUNT, DATA_SIZE))
	transform_data_prev = np.zeros((INIT_COUNT, DATA_SIZE))
	transform_data_is_used = np.zeros(INIT_COUNT, dtype=bool)
	transform_parents = np.repeat(-1, INIT_COUNT, dtype=int)
	transform_unused = [i for i in range(INIT_COUNT)]
	transform_data_size = INIT_COUNT


	@staticmethod
	def generate_world_matricies(self):
		pass
		#todo, 

	@staticmethod
	def new_frame():
		SceneGraph.transform_data_prev[:] = SceneGraph.transform_data

	@staticmethod
	def new_transform():
		if not SceneGraph.transform_unused:
			SceneGraph.expand_data()

		id = SceneGraph.transform_unused.pop()
		SceneGraph.transform_data_is_used[id] = True

		return Transform(id)

	@staticmethod
	def expand_data(amount = 0, mult = 1):
		extend_amount = amount or ceil(mult * SceneGraph.transform_data_size)
		assert extend_amount > 0

		SceneGraph.transform_data = np.vstack((SceneGraph.transform_data, np.zeros(extend_amount, SceneGraph.DATA_SIZE)))
		SceneGraph.transform_data_prev = np.vstack((SceneGraph.transform_data_prev, np.zeros(extend_amount, SceneGraph.DATA_SIZE)))
		SceneGraph.transform_data_is_used = np.vstack((SceneGraph.transform_data_is_used, np.zeros(extend_amount, dtype=bool)))
		SceneGraph.transform_parents = np.vstack((SceneGraph.transform_parents, np.repeat(-1, extend_amount, dtype=bool)))
		SceneGraph.transform_unused.extend(range(SceneGraph.transform_data_size, SceneGraph.transform_data_size + extend_amount))
		SceneGraph.transform_data_size += extend_amount




