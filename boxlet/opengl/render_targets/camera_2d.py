import numpy as np

from ... import FrameBufferStep, Shader


class Camera2D(FrameBufferStep):
	def __init__(self, width=0, height=0, width_mult=1, height_mult=1, depth=True, nearest=False, queue=0, pass_names: list[str] = None) -> None:
		super().__init__(width, height, width_mult, height_mult, depth, nearest, queue, pass_names)

		self.position = np.array([0,0], np.float32)
		self.zoom:float = 1

	def prepare(self):
		super().prepare()
		Shader.set_global_uniform('box_cameraPos', self.position)
		Shader.set_global_uniform('box_cameraSize', [i * self.zoom for i in Shader.get_global_uniform('box_frameSize')])

	def move(self, amount):
		self.position += amount

	@property
	def x(self):
		return self.position[0]

	@x.setter
	def x(self, value):
		self.position[0] = value

	@property
	def y(self):
		return self.position[1]

	@y.setter
	def y(self, value):
		self.position[1] = value


