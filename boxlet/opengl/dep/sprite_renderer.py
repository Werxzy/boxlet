from boxlet import manager, Renderer, Texture, VertFragShader, Model, pygame
from OpenGL.GL import *
from ctypes import c_void_p
import numpy as np

# would need to be reworked

class SpriteRenderer(Renderer):
	# position and size are in pixel coordinates

	# vertex_shader = """
	# 	#version 330
	# 	layout(location = 0) in vec2 pos;
	# 	layout(location = 1) in vec2 uvIn;
	# 	out vec2 uv;
	# 	void main() {
	# 		gl_Position = vec4(pos, 0, 1);
	# 		uv = uvIn;
	# 	}
	# 	"""
	vertex_shader = """
		#version 330
		layout(location = 0) in vec2 pos;
		layout(location = 1) in vec2 uvIn;
		uniform vec2 box_cameraSize;
		uniform vec2 box_cameraPos;
		uniform vec2 texSize;
		uniform vec3 texPos;
		out vec2 uv;
		void main() {
			vec2 truePos = pos * texSize + texPos.xy; // may need to adjust model
			vec2 screenPos = truePos / box_cameraSize + box_cameraPos; // may want to floor
			gl_Position = vec4(screenPos, texPos.z, 1);
			uv = uvIn;
		}
		"""
	fragment_shader = """
		#version 330
		out vec4 fragColor;
		in vec2 uv;
		uniform sampler2D tex;
		void main() {
			fragColor = texture(tex, uv);
		}
		"""

	shader = VertFragShader(vertex_shader, fragment_shader)
	model = Model()
	instances:list['SpriteRenderer'] = []

	vao = glGenVertexArrays(1)
	glBindVertexArray(vao)
	model.bind()
	glBindVertexArray(0)

	def __init__(self, image:Texture):		
		self.image = image
		self.position = np.array([0, 0, 0], np.float32)

		SpriteRenderer.instances.append(self)
		
	def destroy(self):
		SpriteRenderer.instances.remove(self)

	# 	self.uniforms = shader.default_uniforms.copy()

	# def set_uniform(self, key, value):
	# 	self.uniforms[key] = value

	@staticmethod
	def render():
		if not SpriteRenderer.instances: 
			return

		glUseProgram(SpriteRenderer.shader.program)

		cs, cp, ts, tp = (SpriteRenderer.shader.uniforms[u] for u in ['box_cameraSize', 'box_cameraPos', 'texSize', 'texPos'])

		# apply camera values
		glUniform2fv(cs, 1, np.array(pygame.display.get_window_size()) * 0.5)
		glUniform2fv(cp, 1, manager.screen_pos)
		
		glBindVertexArray(SpriteRenderer.vao)

		# Enable alpha blending
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glActiveTexture(GL_TEXTURE0)

		for i in SpriteRenderer.instances:
			glBindTexture(GL_TEXTURE_2D, i.image.image_texture)
			# sort by instances of the same texture when added?
			# only calling active texture and bind texture once only causes a slight performance boost

			# apply renderer values
			glUniform2fv(ts, 1, i.image.size)
			glUniform3fv(tp, 1, i.position)

			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, c_void_p(0))