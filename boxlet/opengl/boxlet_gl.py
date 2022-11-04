from typing import Callable
from boxlet import *
from OpenGL.GL import *

class BoxletGL:
	
	render_targets:list['RenderTarget'] = list()
	render_passes:dict[str, 'RenderPass'] = dict()
	render_groups:dict[str, dict['Shader', list[Callable]]] = dict()
	vao = 0
	bound_textures:dict[int, tuple[int, int]] = dict([(int(GL_TEXTURE0) + i, (-1, -1)) for i in range(int(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS))])
	update_order = True
	_viewport_data = (0,0,0,0)
	
	@staticmethod
	def render():
		if BoxletGL.update_order:
			BoxletGL.sort_pass_order()

		for target in BoxletGL.render_targets:
			target.prepare()

			for pass_name in target.pass_names:
				r_pass = BoxletGL.render_passes[pass_name]
				r_pass.prepare()

				for shader, renderers in BoxletGL.render_groups[pass_name].items():
					shader.use()
					for render_call in renderers:
						render_call()

				r_pass.post()
			
			target.post()

	@staticmethod
	def sort_pass_order():
		BoxletGL.update_order = False
		BoxletGL.render_targets.sort(key = lambda rt: rt.queue)

		for target in BoxletGL.render_targets:
			target.pass_names.sort(key = lambda pn: BoxletGL.render_passes[pn].queue)

	@staticmethod
	def add_render_target(render_target:'RenderTarget'):
		BoxletGL.render_targets.append(render_target)
		BoxletGL.update_order = True

	@staticmethod
	def add_render_pass(render_pass:'RenderPass'):
		BoxletGL.render_passes[render_pass.name] = render_pass
		BoxletGL.update_order = True

	@staticmethod
	def add_render_call(pass_name:str, shader:'Shader', call:Callable):
		BoxletGL.render_groups.setdefault(pass_name, dict()).setdefault(shader, list()).append(call)

	@staticmethod
	def bind_vao(vao):
		'Binds a vertex array object (vao) as long as it is not currenly bound.'
		if BoxletGL.vao != vao: # this check turns out to be not that useful at the moment
			BoxletGL.vao = vao
			glBindVertexArray(vao)

	@staticmethod
	def bind_texture(target:int = GL_TEXTURE0, type:int = GL_SAMPLER_2D, texture = 0):
		'Binds a texture as long as it is not currenly bound.'
		if BoxletGL.bound_textures[target] != (type, texture):
			BoxletGL.bound_textures[target] = (type, texture)
			glActiveTexture(target)
			glBindTexture(type, texture)

	@staticmethod
	def viewport(x,y,w,h):
		if BoxletGL._viewport_data != (x,y,w,h):
			BoxletGL._viewport_data = (x,y,w,h)
			glViewport(x,y,w,h)
	
		