import numpy as np
import math

from boxlet import Renderer, Shader, manager
from OpenGL.GL import glUniform2fv


class Camera2D(Renderer):
	def __init__(self, queue, position = None) -> None:
		super().__init__(queue)

		self.position = np.array(position or [0,0], np.float32)
		self.zoom:float = 1

	def render(self):
		Shader.set_global_uniform('box_cameraPos', self.position)
		Shader.set_global_uniform('box_cameraSize', [i * self.zoom for i in Shader.get_global_uniform('frameSize')])

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


