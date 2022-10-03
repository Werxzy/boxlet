from boxlet import Renderer, Texture, VertFragShader, Model, RenderInstance
from OpenGL.GL import *


class SpritePaletteInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec2 pos;
		layout(location = 1) in vec2 uvIn;
		layout(location = 2) in vec3 texPos;
		layout(location = 3) in vec4 uvPos; // .xy = scale, .zw = position

		uniform vec2 cameraSize;
		uniform vec2 cameraPos;

		uniform vec2 texSize;
		
		out vec2 uv;

		void main() {
			vec2 truePos = pos * texSize * uvPos.xy + texPos.xy;
			vec2 screenPos = (truePos - cameraPos) * 2 / cameraSize;
			gl_Position = vec4(screenPos, texPos.z, 1);
			uv = uvIn * uvPos.xy + uvPos.zw;
		}
		"""
	fragment_shader = """
		#version 330
		in vec2 uv;

		uniform sampler2D tex;

		out vec4 fragColor;

		void main() {
			vec4 color = texture(tex, uv);
			fragColor = color;
		}
		"""

	shader = VertFragShader(vertex_shader, fragment_shader, ['cameraSize', 'cameraPos', 'texSize'])
	model = Model()

	class SpritePaletteInstance(RenderInstance):
		position = [0,0,0], 2
		uv_size = [1,1], 3
		uv_pos = [0,0], 3

	def __init__(self, image:Texture, queue = 0):	
		super().__init__(queue)
		
		self.image = image

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind()
		self.instance_list = self.SpritePaletteInstance.new_instance_list()

		glBindVertexArray(0)

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		if self.instance_list.instance_count == 0:
			return

		glUseProgram(self.shader.program)

		# apply uniform values
		self.shader.apply_global_uniforms('cameraSize', 'cameraPos')
		glUniform2fv(self.shader.uniforms['texSize'], 1, self.image.size)

		glEnable(GL_ALPHA_TEST)
		glAlphaFunc(GL_GREATER, 0.5)
		
		glBindVertexArray(self.vao)
		
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.image.image_texture)

		self.instance_list.update_data()

		glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, self.instance_list.instance_count)

