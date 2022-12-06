from OpenGL.GL import *

from .. import BoxletGL


class RenderPass:
	def __init__(self, name:str, queue:int):
		self.name = name
		self.queue = queue
		BoxletGL.add_render_pass(self)

	def prepare(self):
		...
	
	def post(self):
		...


class PassOpaque(RenderPass):
	def prepare(self):
		glEnable(GL_CULL_FACE)
		glCullFace(GL_FRONT)
