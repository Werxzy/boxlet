from OpenGL.GL import *
from OpenGL.GL import shaders
from boxlet import Model, RenderInstance, Texture, np

class Shader:

	# TODO? have a dictionary (or hashset?) of already created shaders to save on duplicate vertex/fragment shaders
	# (not sure how useful that would be though.

	_test_vao = glGenVertexArrays(1)
	glBindVertexArray(_test_vao)
	_test_model = Model()
	_test_model.bind(position = 0, texcoord = 1)
	glBindVertexArray(0)

	global_uniforms = {
		'box_frameSize': [[0,0]],
		'box_cameraSize': [[0,0]],
		'box_cameraPos': [[0,0]],
	}
	
	def __init__(self, program) -> None:
		self.program = program

		# if uniforms:
		# 	# glLinkProgram(self.program) # this may not be necessary 
		# 	self.uniforms = {u:glGetUniformLocation(self.program, u) for u in uniforms}

		count = ctypes.c_int()
		buffer_size = 64
		name = ctypes.create_string_buffer(buffer_size)
		name_length = ctypes.c_uint()
		var_size = ctypes.c_int()
		var_type = ctypes.c_uint()

		# Gets the the initial inputs for the shader
		self.vertex_attributes:dict[str, tuple[int,int,int]] = dict()

		# print('- - -')

		glGetProgramiv(self.program, GL_ACTIVE_ATTRIBUTES, count)
		for i in range(count.value):
			glGetActiveAttrib(self.program, i, buffer_size, name_length, var_size, var_type, name)
			n = ''.join(chr(c) for c in name.value)

			self.vertex_attributes[n] = (var_size.value, var_type.value, glGetAttribLocation(self.program, n))
			# print(n, name_length.value, var_size.value, var_type.value)

		# Gets all the available uniforms
		self.uniforms:dict[str, tuple[int,int,int]] = dict()
		self.tracked_global_uniforms:list[str] = []
		'key = uniform name\n\nvalue = (count, type, location)'
		
		glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS, count)
		for i in range(count.value):
			glGetActiveUniform(self.program, i, buffer_size, name_length, var_size, var_type, name)
			n = ''.join(chr(c) for c in name.value)
			if var_size.value > 1:
				n = n[:-3]

			self.uniforms[n] = (var_size.value, var_type.value, glGetUniformLocation(self.program, n))
			if n.startswith('box_'):
				self.tracked_global_uniforms.append(n)
			# print(n, name_length.value, var_size.value, var_type.value, self.uniforms[n])

		# Gets all the available uniform blocks
		self.uniform_blocks:dict[str, int] = dict()
		param = ctypes.c_int()
		glGetProgramiv(self.program, GL_ACTIVE_UNIFORM_BLOCKS, count)
		for i in range(count.value):
			glGetActiveUniformBlockiv(self.program, i, GL_UNIFORM_BLOCK_BINDING, param)
			block_binding = param.value

			glGetActiveUniformBlockiv(self.program, i, GL_UNIFORM_BLOCK_NAME_LENGTH, name_length)
			block_name = ctypes.create_string_buffer(name_length.value)
			glGetActiveUniformBlockName(self.program, i, name_length, param, block_name)
			n = ''.join(chr(c) for c in block_name.value)

			self.uniform_blocks[n] = block_binding
			# print(n)

	def use(self):
		glUseProgram(self.program)
		self.apply_global_uniforms(*self.tracked_global_uniforms)

	@staticmethod
	def add_global_uniform(name, start_value):
		Shader.global_uniforms[name] = [start_value]

	@staticmethod
	def add_global_matrix_uniform(name, start_value, flipped = GL_FALSE):
		Shader.global_uniforms[name] = [start_value, flipped]

	@staticmethod
	def set_global_uniform(name, value):
		Shader.global_uniforms[name][0] = value

	@staticmethod
	def get_global_uniform(name):
		return Shader.global_uniforms[name][0]

	def apply_global_uniform(self, name):
		u = Shader.global_uniforms[name]
		if len(u) > 1:
			self.apply_uniform_matrix(name, *Shader.global_uniforms[name])
		else:
			self.apply_uniform(name, Shader.global_uniforms[name][0])

	def apply_global_uniforms(self, *names):
		for n in names:
			self.apply_global_uniform(n)

	def apply_uniform(self, name, value):
		u = self.uniforms[name]
		Shader.uniform_type_dict[u[1]](u[2], u[0], value)

	def apply_uniform_matrix(self, name, value, flipped = GL_FALSE):
		u = self.uniforms[name]
		Shader.uniform_type_dict[u[1]](u[2], u[0], flipped, value)

	# def destroy(self):
	# 	glDeleteShader(self.program)

	uniform_type_dict = {
		int(GL_FLOAT) : glUniform1fv, 
		int(GL_FLOAT_VEC2) : glUniform2fv, 
		int(GL_FLOAT_VEC3) : glUniform3fv, 
		int(GL_FLOAT_VEC4) : glUniform4fv, 
		int(GL_DOUBLE) : glUniform1dv, 
		int(GL_DOUBLE_VEC2) : glUniform2dv, 
		int(GL_DOUBLE_VEC3) : glUniform3dv, 
		int(GL_DOUBLE_VEC4) : glUniform4dv, 
		int(GL_INT) : glUniform1iv, 
		int(GL_INT_VEC2) : glUniform2iv, 
		int(GL_INT_VEC3) : glUniform3iv, 
		int(GL_INT_VEC4) : glUniform4iv, 
		int(GL_UNSIGNED_INT) : glUniform1uiv, 
		int(GL_UNSIGNED_INT_VEC2) : glUniform2uiv, 
		int(GL_UNSIGNED_INT_VEC3) : glUniform3uiv, 
		int(GL_UNSIGNED_INT_VEC4) : glUniform4uiv, 
		int(GL_BOOL) : glUniform1iv, 
		int(GL_BOOL_VEC2) : glUniform2iv, 
		int(GL_BOOL_VEC3) : glUniform3iv, 
		int(GL_BOOL_VEC4) : glUniform4iv, 
		int(GL_FLOAT_MAT2) : glUniformMatrix2fv, 
		int(GL_FLOAT_MAT3) : glUniformMatrix3fv, 
		int(GL_FLOAT_MAT4) : glUniformMatrix4fv, 
		int(GL_FLOAT_MAT2x3) : glUniformMatrix2x3fv, 
		int(GL_FLOAT_MAT2x4) : glUniformMatrix2x4fv, 
		int(GL_FLOAT_MAT3x2) : glUniformMatrix3x2fv, 
		int(GL_FLOAT_MAT3x4) : glUniformMatrix3x4fv, 
		int(GL_FLOAT_MAT4x2) : glUniformMatrix4x2fv, 
		int(GL_FLOAT_MAT4x3) : glUniformMatrix4x3fv, 
		int(GL_DOUBLE_MAT2) : glUniformMatrix2fv, 
		int(GL_DOUBLE_MAT3) : glUniformMatrix3fv, 
		int(GL_DOUBLE_MAT4) : glUniformMatrix4fv, 
		int(GL_DOUBLE_MAT2x3) : glUniformMatrix2x3fv, 
		int(GL_DOUBLE_MAT2x4) : glUniformMatrix2x4fv, 
		int(GL_DOUBLE_MAT3x2) : glUniformMatrix3x2fv, 
		int(GL_DOUBLE_MAT3x4) : glUniformMatrix3x4fv, 
		int(GL_DOUBLE_MAT4x2) : glUniformMatrix4x2fv, 
		int(GL_DOUBLE_MAT4x3) : glUniformMatrix4x3fv, 
	}
	# There are more, but I don't know yet what else is needed
	# https://registry.khronos.org/OpenGL-Refpages/gl4/html/glGetActiveUniform.xhtml


class VertFragShader(Shader):
	def __init__(self, vertex, frag):
		glBindVertexArray(Shader._test_vao)
		self.vertex = shaders.compileShader(vertex, GL_VERTEX_SHADER)
		self.fragment = shaders.compileShader(frag, GL_FRAGMENT_SHADER)
		
		super().__init__(shaders.compileProgram(self.vertex, self.fragment))
		glBindVertexArray(0)

	@staticmethod
	def gen_basic_shader(include_instancer = False):
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
				fragColor = texture(tex, uv);
			}
			"""
		if not include_instancer:
			return VertFragShader(vertex_shader, fragment_shader)
		
		class ModelInstance(RenderInstance):
			model_matrix:np.ndarray = 'attrib', 'mat4', 'model'
			texture:Texture = 'uniform', 'sampler2D', 'tex'

		return VertFragShader(vertex_shader, fragment_shader), ModelInstance
		

class ComputeShader(Shader):
	def __init__(self, compute):
		self.compute = shaders.compileShader(compute, GL_COMPUTE_SHADER)
		
		super().__init__(shaders.compileProgram(self.compute))

