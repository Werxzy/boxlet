from boxlet import BoxletGL, Renderer, Texture, VertFragShader, Model, RenderInstance, np
from OpenGL.GL import *


class ModelInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec3 position;
		layout(location = 1) in vec2 texcoord;
		layout(location = 2) in mat4 model;

		uniform mat4 viewProj;

		out vec2 uv;

		void main() {
			gl_Position = viewProj * model * vec4(position, 1);
			uv = texcoord;
		}
		"""
	fragment_shader = """
		#version 330
		in vec2 uv;

		uniform sampler2D tex;

		out vec4 fragColor;

		void main() {
			vec4 color = texture(tex, uv);
			//vec4 color = vec4(uv,0,1);
			fragColor = color;
		}
		"""

	shader = VertFragShader(vertex_shader, fragment_shader)
	cube_model = Model.gen_cube()

	class ModelInstance(RenderInstance):
		model_matrix:np.ndarray = 'mat4', 2

	def __init__(self, model:Model, image:Texture, pass_name = 'default'):			
		self.model = model or self.cube_model
		self.image = image

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind(self.shader)
	
		self.instance_list = self.ModelInstance.new_instance_list()

		glBindVertexArray(0)

		#TODO this is sort of an example
		#TODO, allow for premade vao and multimodel to reduce vao bind count
		BoxletGL.add_render_call(pass_name, self.shader, self.render)

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		if self.instance_list.instance_count == 0:
			return

		glUseProgram(self.shader.program)
		self.shader.apply_global_uniforms('viewProj')

		glEnable(GL_CULL_FACE)
		glCullFace(GL_FRONT)
		
		BoxletGL.bind_vao(self.vao)
		
		BoxletGL.bind_texture(GL_TEXTURE0, GL_TEXTURE_2D, self.image.image_texture)

		self.instance_list.update_data()

		glDrawElementsInstanced(GL_TRIANGLES, self.model.index_count, GL_UNSIGNED_INT, None, self.instance_list.instance_count)

