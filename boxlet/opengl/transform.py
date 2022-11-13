from .. import Tmath, np


class Transform:
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.model_matrix = np.identity(4, np.float32)
		self.model_matrix_changed = False

	def translate(self, amount):
		self.model_matrix[3,:3] += amount

	def look_at(self, eye, target, up):
		self.model_matrix = Tmath.look_at(eye, target, up)

	def look_at_forward(self, pos, forward, up):
		self.model_matrix = Tmath.look_at_forward(pos, forward, up)

	def reset_pos(self):
		self.model_matrix = np.identity(4)

	def fps_look(self, pos, x, y):
		self.model_matrix = Tmath.fps_look(pos, x, y)

	@property
	def right(self):
		return Tmath.normalize(self.model_matrix[0,:3])

	@property
	def up(self):
		return Tmath.normalize(self.model_matrix[1,:3])

	@property
	def forward(self):
		return Tmath.normalize(self.model_matrix[2,:3])

	@property
	def position(self):
		return self.model_matrix[3,:3]

	@position.setter
	def position(self, value):
		self.model_matrix[3,:3] = value
		self.model_matrix_changed = True

	@property
	def x(self):
		return self.model_matrix[3,0]

	@x.setter
	def x(self, value):
		self.model_matrix[3,0] = value
		self.model_matrix_changed = True

	@property
	def y(self):
		return self.model_matrix[3,1]

	@y.setter
	def y(self, value):
		self.model_matrix[3,1] = value
		self.model_matrix_changed = True

	@property
	def z(self):
		return self.model_matrix[3,2]

	@z.setter
	def z(self, value):
		self.model_matrix[3,2] = value
		self.model_matrix_changed = True


if __name__ == '__main__':
	# Can be inherited alongside Entity, though not necessary.

	from boxlet import Entity

	class TestMovableEntity(Entity, Transform):
		def __init__(self) -> None:
			super().__init__()
