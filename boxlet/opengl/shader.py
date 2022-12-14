from . import extra_gl_constants as extra_gl
from OpenGL.GL import *
from OpenGL.GL import shaders as ogl_shaders
import re

from . import BoxletGL, Model, RenderInstance, Texture, np


class Shader:

	# TODO? have a dictionary (or hashset?) of already created shaders to save on duplicate vertex/fragment shaders
	# (not sure how useful that would be though.

	_test_vao = None
	_test_model = None

	global_uniforms = {
		'box_frameSize': [[0,0]],
		'box_cameraSize': [[0,0]],
		'box_cameraPos': [[0,0]],
	}

	_preprocessor_includes:dict[str, str] = {}
	_INCLUDE_REGEX = '#pragma\\s+include\\s+"(.+)"'
	_EXO_INCLUDE_REGEX = '#pragma\\s+exoInclude\\s+"(.+)"'
	_ENDO_INCLUDE_REGEX = '#pragma\\s+endoInclude'
	
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
		self.vertex_attributes:dict[str, tuple[int,int,int]] = {}

		# print('- - -')

		glGetProgramiv(self.program, GL_ACTIVE_ATTRIBUTES, count)
		for i in range(count.value):
			glGetActiveAttrib(self.program, i, buffer_size, name_length, var_size, var_type, name)
			n = ''.join(chr(c) for c in name.value)

			self.vertex_attributes[n] = (var_size.value, var_type.value, glGetAttribLocation(self.program, n))
			# print(n, name_length.value, var_size.value, var_type.value)

		# Gets all the available uniforms
		self.uniforms:dict[str, tuple[int,int,int]] = {}
		self.textures:dict[str, tuple[int,int]] = {}
		self.tracked_global_uniforms:list[str] = []
		self.tracked_global_textures:list[str] = []
		'key = uniform name\n\nvalue = (count, type, location)'

		used_textures = []
		
		glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS, count)
		for i in range(count.value):
			glGetActiveUniform(self.program, i, buffer_size, name_length, var_size, var_type, name)
			n = ''.join(chr(c) for c in name.value)
			if var_size.value > 1:
				n = n[:-3]

			location = glGetUniformLocation(self.program, n)

			if var_type.value in extra_gl.UNIFORM_TEXTURE_DICT: # texture uniform
				texture_Loc = ctypes.c_int()
				glGetUniformiv(self.program, location, texture_Loc)
				loc = texture_Loc.value
				while loc in used_textures:
					loc += 1
				used_textures.append(loc) 
				glProgramUniform1i(self.program, location, loc)
				# sets the binding for a texture if none exists (really needed for 3.3)
				# NOTE there is no guarentee the texture's uniforms are in order in the shader
				# FUTURE NOTE if there is a need to relink programs, this will need to be reapplied
				
				vt = extra_gl.UNIFORM_TEXTURE_DICT[var_type.value][0]
				self.textures[n] = (GL_TEXTURE0 + loc, vt)
				if n.startswith('box_'):
					self.tracked_global_textures.append(n)

				# print(n, name_length.value, GL_TEXTURE0 + loc, var_type.value, self.textures[n])

			else: # normal uniform
				self.uniforms[n] = (var_size.value, var_type.value, location)
				if n.startswith('box_'):
					self.tracked_global_uniforms.append(n)

				# print(n, name_length.value, var_size.value, var_type.value, self.uniforms[n])

		# Gets all the available uniform blocks
		self.uniform_blocks:dict[str, int] = {}
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
		#TODO apply global textures

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

	@staticmethod
	def add_include(name, code):
		'''
		Adds to dictionary of preprocessing includes macros.
		
		If in a shader `#include "[name]"` is added, it is replaced by an earlier all_include(name, code) call.

		Include code can contain include macros, but they cannot be cause cyclical includes.
		'''

		includes_found:list[str] = [found for found in re.findall(Shader._INCLUDE_REGEX, code)]
		while includes_found:
			f = includes_found.pop()
			if f in Shader._preprocessor_includes:
				for found in re.findall(Shader._INCLUDE_REGEX, Shader._preprocessor_includes[f]):
					if found == name:
						raise Exception('Shader include loop discovered.')
					includes_found.append(found)

		Shader._preprocessor_includes[name] = code

	@staticmethod
	def preprocess_shader(code:str):
		processing_count = 0
		
		while True:
			processing_count += 1
			if processing_count > 100:
				raise Exception('Potential include loop discovered:', name)

			if found := re.search(Shader._INCLUDE_REGEX, code):
				name = found.group(1)
				if name not in Shader._preprocessor_includes:
					raise Exception(f'Include key "{name}" does not exist.')
				code = ''.join([
					code[:found.start(0)], 
					Shader._preprocessor_includes[name], 
					code[found.end(0):]
					])
				continue

			if found := re.search(Shader._EXO_INCLUDE_REGEX, code):
				name = found.group(1)
				if name not in Shader._preprocessor_includes:
					raise Exception(f'Include key "{name}" does not exist.')

				incl = Shader._preprocessor_includes[name]
				found2 = re.search(Shader._ENDO_INCLUDE_REGEX, incl)
				if found2 is None:
					raise Exception(f'Include "{name}" does not contain #endoInclude')

				code = ''.join([
					incl[:found2.start(0)], 
					code[:found.start(0)], 
					code[found.end(0):],
					incl[found2.end(0):], 
					])
				continue

			break

		return code

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
		if u[1] == GL_FLOAT_MAT4:
			self.apply_uniform_matrix(name, value)
		else:
			extra_gl.UNIFORM_TYPE_DICT[u[1]][0](u[2], u[0], value)

	def apply_uniform_matrix(self, name, value, flipped = GL_FALSE):
		u = self.uniforms[name]
		extra_gl.UNIFORM_TYPE_DICT[u[1]][0](u[2], u[0], flipped, value)

	def bind_texture(self, name, texture:int|Texture):
		if isinstance(texture, Texture):
			texture = texture.image_texture
		BoxletGL.bind_texture(*self.textures[name], texture)

	# def destroy(self):
	# 	glDeleteShader(self.program)

	@staticmethod
	def init_testing_vao():
		if Shader._test_vao: return

		Shader._test_vao = glGenVertexArrays(1)
		glBindVertexArray(Shader._test_vao)
		Shader._test_model = Model()
		Shader._test_model.bind(position = 0, texcoord = 1)
		glBindVertexArray(0)


def generate_once(func):
	# Runs the function once and returns the results on the current and future calls.
	# Expects there to be no parameters for the function.
	func._data = None
	def gen():
		if func._data is None:
			func._data = func()
		return func._data
	return gen

	
class VertFragShader(Shader):
	def __init__(self, vertex, frag):
		Shader.init_testing_vao()

		glBindVertexArray(Shader._test_vao)
		self.vertex = ogl_shaders.compileShader(Shader.preprocess_shader(vertex), GL_VERTEX_SHADER)
		self.fragment = ogl_shaders.compileShader(Shader.preprocess_shader(frag), GL_FRAGMENT_SHADER)
		
		super().__init__(ogl_shaders.compileProgram(self.vertex, self.fragment))
		glBindVertexArray(0)

	@staticmethod
	@generate_once
	def gen_basic_shader():
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
		return VertFragShader(vertex_shader, fragment_shader)

	@staticmethod
	@generate_once
	def gen_basic_instance_class():
		class ModelInstance(RenderInstance):
			model_matrix:np.ndarray = 'attrib', 'mat4', 'model'
			texture:Texture = 'texture', 'tex'
		return ModelInstance
		

class ComputeShader(Shader):
	def __init__(self, compute):
		self.compute = ogl_shaders.compileShader(Shader.preprocess_shader(compute), GL_COMPUTE_SHADER)
		
		super().__init__(ogl_shaders.compileProgram(self.compute))

