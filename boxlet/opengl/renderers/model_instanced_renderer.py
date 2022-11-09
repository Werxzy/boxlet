from boxlet import BoxletGL, Renderer, Texture, VertFragShader, Model, RenderInstance, np
from OpenGL.GL import *


class ModelInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec3 position;
		layout(location = 1) in vec2 texcoord;
		layout(location = 2) in mat4 model;

		uniform mat4 box_viewProj;

		out vec2 uv;

		void main() {
			gl_Position = box_viewProj * model * vec4(position, 1);
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
		model_matrix:np.ndarray = 'attrib', 'mat4', 'model'
		texture = 'texture', 'tex'

	def __init__(self, model:Model, image:Texture, pass_name = 'default'):			
		self.model = model or self.cube_model
		self.image = image

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind(self.shader)
	
		self.instance_list = self.ModelInstance.new_instance_list(self.shader)
		self.instance_list.uniform_data['texture'] = self.image

		glBindVertexArray(0)

		#TODO this is sort of an example
		#TODO, allow for premade vao and multimodel to reduce vao bind count
		BoxletGL.add_render_call(pass_name, self.shader, self.render)

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		if self.instance_list.instance_count == 0:
			return
		
		BoxletGL.bind_vao(self.vao)

		self.instance_list.update_data()
		self.instance_list.update_uniforms()

		glDrawElementsInstanced(GL_TRIANGLES, self.model.index_count, GL_UNSIGNED_INT, None, self.instance_list.instance_count)

