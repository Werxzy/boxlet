from . import *

class Scene:
	def __init__(self):
		# I really don't like this setup
		self.triangle_positions = []

		for x in np.arange(-1.0, 1.0, 0.2):
			for y in np.arange(-1.0, 1.0, 0.2):
				self.triangle_positions.append(np.array([x, y, 0], dtype=np.float32))
				# I REALLY do not like having a python list of numpy arrays

		
