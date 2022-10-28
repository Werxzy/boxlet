from boxlet import Renderer, MultiTexture, VertFragShader, Model, RenderInstance
from OpenGL.GL import *


class SpritePaletteInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec2 position;
		layout(location = 1) in vec2 texcoord;
		layout(location = 2) in vec3 texPos;
		layout(location = 3) in vec4 uvPos; // .xy = position, .zw = scale

		uniform vec2 cameraSize;
		uniform vec2 cameraPos;

		uniform vec2 texSize;
		
		out vec2 uv;

		void main() {
			vec2 truePos = position * texSize * uvPos.zw + texPos.xy;
			vec2 screenPos = (truePos - cameraPos) * 2 / cameraSize;
			gl_Position = vec4(screenPos, texPos.z, 1);
			uv = texcoord * uvPos.zw + uvPos.xy;
		}
		"""
	fragment_shader = """
		#version 330
		in vec2 uv;

		uniform sampler2D tex;

		out vec4 fragColor;

		void main() {
			vec4 color = texture(tex, uv);
			if(color.a < 0.5) discard;
			fragColor = color;
		}
		"""

	shader = VertFragShader(vertex_shader, fragment_shader)
	model = Model()

	class SpritePaletteInstance(RenderInstance):
		position = [0,0], 2
		z = [0], 2
		uv_pos = [0,0], 3
		uv_size = [1,1], 3

		def set_sprite(self, id):
			data = self.owner.renderer.image.sub_image_data[id]
			self.uv_pos = data[0:2]
			self.uv_size = data[2:4]

	def __init__(self, image:MultiTexture, queue = 0):	
		super().__init__(queue)
		
		self.image = image

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind(self.shader)
		self.instance_list = self.SpritePaletteInstance.new_instance_list(self)

		glBindVertexArray(0)

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		if self.instance_list.instance_count == 0:
			return

		glUseProgram(self.shader.program)

		# apply uniform values
		self.shader.apply_global_uniforms('cameraSize', 'cameraPos')
		self.shader.apply_uniform('texSize', self.image.size)
		
		glBindVertexArray(self.vao)
		
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.image.image_texture)

		self.instance_list.update_data()

		glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, self.instance_list.instance_count)

