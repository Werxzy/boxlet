from boxlet import Renderer, Texture, VertFragShader, Model, RenderInstance, np, Tmath
from OpenGL.GL import *


class MultiModelRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		#extension GL_ARB_shader_draw_parameters : enable
		layout(location = 0) in vec3 pos;
		layout(location = 1) in vec2 uvIn;
		
		layout(std140) uniform paramData {
			mat4 model[64];
		} parry;
		uniform mat4 viewProj;

		out vec2 uv;

		void main() {
			gl_Position = viewProj * parry.model[gl_DrawIDARB] * vec4(pos, 1);
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

	shader = VertFragShader(vertex_shader, fragment_shader, ['viewProj', 'parry'])
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

			# test model 2
			 2, 0, 0, 1,0,
			-2, 0, 0, 0,0,
			 0, 2, 2, 0,1,
		],
		index = [
			0,1,2, 1,3,2,
			4,5,6, 5,7,6,
			8,9,10, 9,11,10,
			12,13,14, 13,15,14,
			16,17,18, 17,19,18,
			20,21,22, 21,23,22,

			# test model 2
			24,25,26,
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

		for i in range(4):
			self.new_instance(model_matrix = Tmath.translate((i * 2.5, 0, 0)))

		

	def new_instance(self, **kwargs):
		return self.instance_list.new_instance(**kwargs)

	def render(self):
		# if self.instance_list.instance_count == 0:
		if self.instance_list.instance_count < 4:
			return

		glUseProgram(self.shader.program)
		self.shader.apply_global_uniforms('viewProj')

		glEnable(GL_CULL_FACE)
		glCullFace(GL_FRONT)
		
		glBindVertexArray(self.vao)
		
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.image.image_texture)

		self.instance_list.update_data()


		# uniform struct test
		from ctypes import c_void_p, c_int, c_float
		bindingPoint = 1
		buffer = glGenBuffers(1)
		glBindBuffer(GL_UNIFORM_BUFFER, buffer)
		glBindBufferBase(GL_UNIFORM_BUFFER, bindingPoint, buffer)
		glBufferData(GL_UNIFORM_BUFFER, self.instance_list.data.size * sizeof(c_float), self.instance_list.data, GL_DYNAMIC_DRAW)

		u = glGetUniformBlockIndex(self.shader.program, 'paramData')
		glUniformBlockBinding(self.shader.program, u, bindingPoint)

		glMultiDrawElements(GL_TRIANGLES, np.array([36, 3, 36, 3], np.uint32), GL_UNSIGNED_INT, np.array([0, 36, 0, 36]) * sizeof(c_int), 4)

		glDeleteBuffers(1,[buffer])
		


		# glDrawElementsInstanced(GL_TRIANGLES, self.model.index_count, GL_UNSIGNED_INT, None, inst_count)
		# glMultiDrawElements(GL_TRIANGLES, np.array([36, 3, 36, 3], np.uint32), GL_UNSIGNED_INT, np.array([0, 36, 0, 36]) * sizeof(c_int), 4)
		# draw elements, for whatever reason, does not use glVertexAttribDivisor with multiple divisors

	ith = 0
