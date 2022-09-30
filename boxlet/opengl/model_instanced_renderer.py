from boxlet import Renderer, Texture, VertFragShader, Model, RenderInstance, np
from OpenGL.GL import *


class ModelInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec3 pos;
		layout(location = 1) in vec2 uvIn;
		layout(location = 2) in mat4 model;

		uniform mat4 viewProj;

		out vec2 uv;

		void main() {
			gl_Position = viewProj * model * vec4(pos, 1);
			uv = uvIn;
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

	shader = VertFragShader(vertex_shader, fragment_shader, ['viewProj'])
	cube_model = Model(
		vertex = [
			1,-1,-1, 0,0,
			1, 1,-1, 1,0,
			1,-1, 1, 0,1,
			1, 1, 1, 1,1,

			-1,1,-1, 0,0,
			-1,1, 1, 0,1,
			 1,1,-1, 1,0,
			 1,1, 1, 1,1,
			 
			-1,-1,1, 0,0,
			 1,-1,1, 1,0,
			-1, 1,1, 0,1,
			 1, 1,1, 1,1,

			-1,-1,-1, 0,0,
			-1,-1, 1, 1,0,
			-1, 1,-1, 0,1,
			-1, 1, 1, 1,1,

			-1,-1,-1, 0,0,
			 1,-1,-1, 0,1,
			-1,-1, 1, 1,0,
			 1,-1, 1, 1,1,
			 
			-1,-1,-1, 0,0,
			-1, 1,-1, 1,0,
			 1,-1,-1, 0,1,
			 1, 1,-1, 1,1,
		],
		index = [
			0,1,2, 1,3,2,
			4,5,6, 5,7,6,
			8,9,10, 9,11,10,
			12,13,14, 13,15,14,
			16,17,18, 17,19,18,
			20,21,22, 21,23,22,
		],
		dim = 3)

	class ModelInstance(RenderInstance):
		model_matrix:np.ndarray = 'mat4', 2

	def __init__(self, model:Model, image:Texture, queue = 0):	
		super().__init__(queue)
		
		self.model = model or self.cube_model
		self.image = image

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind()
	
		self.instance_list = self.ModelInstance.new_instance_list()

		glBindVertexArray(0)

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		inst_count = len(self.instance_list.instances)
		if inst_count == 0:
			return

		glUseProgram(self.shader.program)
		self.shader.apply_global_uniforms('viewProj')

		glEnable(GL_CULL_FACE)
		glCullFace(GL_FRONT)
		
		glBindVertexArray(self.vao)
		
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.image.image_texture)

		self.instance_list.update_data()

		glDrawElementsInstanced(GL_TRIANGLES, self.model.index_count, GL_UNSIGNED_INT, None, inst_count)

