import numpy as np

class VaryFloats:
	def __init__(self, values=None, size=None) -> None:
		if values:
			self.current = np.array(values, float)
			self.previous = np.array(values, float)
		if size:
			self.current = np.zeros(size)
			self.previous = np.zeros(size)

	def set_full(self, values):
		self.current[:] = values
		self.previous[:] = values

	def set(self, values):
		self.previous[:] = self.current
		self.current[:] = values

	def set_current(self, values):
		'''
		Only updates the current values.  You may be looking for set()
		
		Usually used with push_current() in order to alter the current value.
		'''
		self.current[:] = values

	def push_current(self):
		self.previous[:] = self.current

	def set_full_range(self, values, ran):
		self.current[ran] = values
		self.previous[ran] = values

	def set_range(self, values, ran = None):
		self.previous[ran] = self.current[ran]
		self.current[ran] = values

	def extend(self, values):
		self.previous = np.append(self.previous, values, axis = 0)
		self.current = np.append(self.current, values, axis = 0)

	def delete(self, ran):
		self.previous = np.delete(self.previous, ran, axis = 0)
		self.current = np.delete(self.current, ran, axis = 0)

	def interpolate(self, t):
		return self.previous + (self.current - self.previous) * t
