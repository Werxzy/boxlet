from boxlet import BoxletGL, Renderer, MultiTexture, VertFragShader, Model, RenderInstance
from OpenGL.GL import *


class SpritePaletteInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec2 position;
		layout(location = 1) in vec2 texcoord;
		layout(location = 2) in vec3 texPos;
		layout(location = 3) in vec4 uvPos; // .xy = position, .zw = scale

		uniform vec2 box_cameraSize;
		uniform vec2 box_cameraPos;

		uniform vec2 texSize;
		
		out vec2 uv;

		void main() {
			vec2 truePos = position * texSize * uvPos.zw + texPos.xy;
			vec2 screenPos = (truePos - box_cameraPos) * 2 / box_cameraSize;
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
		position = 'attrib', [0,0,0], 'texPos'
		uv_pos = 'attrib', [0,0,1,1], 'uvPos'

		def set_sprite(self, id):
			data = self.owner.renderer.image.sub_image_data[id]
			self.uv_pos = data

	def __init__(self, image:MultiTexture, pass_name = ''):	
		super().__init__()
		
		self.image = image

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind(self.shader)
		self.instance_list = self.SpritePaletteInstance.new_instance_list(self)

		glBindVertexArray(0)
		
		BoxletGL.add_render_call(pass_name, self.shader, self.render)

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		if self.instance_list.instance_count == 0:
			return

		# apply uniform values
		self.shader.apply_uniform('texSize', self.image.size)
		
		BoxletGL.bind_vao(self.vao)
		BoxletGL.bind_texture(GL_TEXTURE0, GL_TEXTURE_2D, self.image.image_texture)

		self.instance_list.update_data()

		glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, self.instance_list.instance_count)

