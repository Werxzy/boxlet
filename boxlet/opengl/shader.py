from OpenGL.GL import *
from OpenGL.GL import shaders


class Shader:

	# TODO? have a dictionary (or hashset?) of already created shaders to save on duplicate vertex/fragment shaders
	# (not sure how useful that would be though.

	global_uniforms = {
		'cameraSize': [glUniform2fv, [0,0]],
		'cameraPos': [glUniform2fv, [0,0]],
	}
	
	def __init__(self, program, uniforms = []) -> None:
		self.program = program

		if uniforms:
			# glLinkProgram(self.program) # this may not be necessary 
			self.uniforms = {u:glGetUniformLocation(self.program, u) for u in uniforms}

	@staticmethod
	def add_global_uniform(name, call, start_value):
		Shader.global_uniforms[name] = [call, [start_value]]

	@staticmethod
	def add_global_matrix_uniform(name, call, start_value):
		Shader.global_uniforms[name] = [call, [GL_FALSE, start_value]]

	@staticmethod
	def set_global_uniform(name, value):
		Shader.global_uniforms[name][1][-1] = value

	def apply_global_uniform(self, name):
		c = Shader.global_uniforms[name]
		c[0](self.uniforms[name], 1, *c[1])

	def apply_global_uniforms(self, *names):
		for n in names:
			c = Shader.global_uniforms[n]
			c[0](self.uniforms[n], 1, *c[1])

	# def destroy(self):
	# 	glDeleteShader(self.program)


class VertFragShader(Shader):
	def __init__(self, vertex, frag, uniforms = []):
		self.vertex = shaders.compileShader(vertex, GL_VERTEX_SHADER)
		self.fragment = shaders.compileShader(frag, GL_FRAGMENT_SHADER)
		
		super().__init__(shaders.compileProgram(self.vertex, self.fragment), uniforms)

class ComputeShader(Shader):
	def __init__(self, compute, uniforms = []):
		self.compute = shaders.compileShader(compute, GL_COMPUTE_SHADER)
		
		super().__init__(shaders.compileProgram(self.compute), uniforms)

