from OpenGL.GL import *


class RenderPass:
	def __init__(self, name:str, queue:int):
		self.name = name
		self.queue = queue

	def prepare(self):
		...
	
	def post(self):
		...


class PassOpaque(RenderPass):
	def prepare(self):
		glEnable(GL_CULL_FACE)
		glCullFace(GL_FRONT)
