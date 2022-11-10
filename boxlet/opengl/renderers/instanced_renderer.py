from typing import Generic, TypeVar
from boxlet import BoxletGL, Renderer, VertFragShader, Model, RenderInstance
from OpenGL.GL import *


T = TypeVar('T', bound='RenderInstance')

class InstancedRenderer(Generic[T], Renderer):
	def __init__(self, model: Model, shader:VertFragShader, instance_cls: type[T], pass_name = ''):			
		self._model = model
		self._shader = shader
		self._instance_cls = instance_cls

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)
		model.bind(shader)
		self.instance_list = instance_cls.new_instance_list(shader)
		glBindVertexArray(0)
		
		BoxletGL.add_render_call(pass_name, shader, self.render)

	def set_uniform(self, name, value):
		self.instance_list.uniform_data[name] = value

	def get_uniform(self, name):
		return self.instance_list.uniform_data[name]

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		if self.instance_list.instance_count == 0:
			return
		
		BoxletGL.bind_vao(self.vao)

		self.instance_list.update_data()
		self.instance_list.update_uniforms()

		glDrawElementsInstanced(GL_TRIANGLES, self._model.index_count, GL_UNSIGNED_INT, None, self.instance_list.instance_count)

