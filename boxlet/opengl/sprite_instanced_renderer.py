from boxlet import manager, Renderer, Texture, VertFragShader, Model
from OpenGL.GL import *
from ctypes import c_float
import numpy as np

class SpriteInstancedRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec2 pos;
		layout(location = 1) in vec2 uvIn;
		layout(location = 2) in vec3 texPos;

		uniform vec2 cameraSize;
		uniform vec2 cameraPos;

		uniform vec2 texSize;
		
		out vec2 uv;

		void main() {
			vec2 truePos = pos * texSize + texPos.xy; // may need to adjust model
			vec2 screenPos = truePos / cameraSize + cameraPos; // may want to floor
			gl_Position = vec4(screenPos, texPos.z, 1);
			uv = uvIn;
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

	shader = VertFragShader(vertex_shader, fragment_shader, ['cameraSize', 'cameraPos', 'texSize'])
	model = Model()

	vao = glGenVertexArrays(1)
	glBindVertexArray(vao)
	model.bind()

	# position_data = np.zeros(0, np.float32)

	# this is potentially not optimal, especially for data that won't change each frame
	position_vbo = glGenBuffers(1)
	glBindBuffer(GL_ARRAY_BUFFER, position_vbo)
	glBufferData(GL_ARRAY_BUFFER, np.zeros(0, np.float32), GL_STREAM_DRAW)

	glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, sizeof(c_float)*3, None) 
	glEnableVertexAttribArray(2)
	glVertexAttribDivisor(2, 1)

	glBindVertexArray(0)

	#could make functions for easy binding arrays

	position_data:dict[Texture, np.ndarray] = {}
	instances:dict[Texture, list['SpriteInstancedRenderer']] = {}

	def __init__(self, image:Texture):	
		if image not in SpriteInstancedRenderer.instances:
			SpriteInstancedRenderer.instances[image] = []
			SpriteInstancedRenderer.position_data[image] = np.zeros(0, np.float32)

		self.image = image
		self.id = len(SpriteInstancedRenderer.instances[image])
		SpriteInstancedRenderer.instances[image].append(self)
		SpriteInstancedRenderer.position_data[image] = np.append(SpriteInstancedRenderer.position_data[image], np.array([0, 0, 0], np.float32))
		self.data_range = np.arange(3) + self.id * 3
		# thought I could do .resize(..., refcheck = False) to reference and skip a indexing step, but this way seems to not be recommended?

	def destroy(self):
		SpriteInstancedRenderer.instances[self.image].pop(self.id)
		SpriteInstancedRenderer.position_data[self.image] = np.delete(SpriteInstancedRenderer.position_data[self.image], self.data_range)
		
		for inst in SpriteInstancedRenderer.instances[self.image][self.id:]:
			inst.id -= 1
			inst.data_range = np.arange(3) + inst.id * 3

	@property
	def position(self):
		return SpriteInstancedRenderer.position_data[self.image][self.data_range]
		# these properties can be expanded for different properties

	@position.setter
	def position(self, value):
		SpriteInstancedRenderer.position_data[self.image][self.data_range] = value

	@staticmethod
	def render():
		if not SpriteInstancedRenderer.instances: 
			return

		glUseProgram(SpriteInstancedRenderer.shader.program)

		cs, cp, ts = (SpriteInstancedRenderer.shader.uniforms[u] for u in ['cameraSize', 'cameraPos', 'texSize'])

		# apply camera values
		glUniform2fv(cs, 1, manager.display_size * 0.5)
		glUniform2fv(cp, 1, manager.screen_pos)
		
		glBindVertexArray(SpriteInstancedRenderer.vao)

		# Enable alpha blending
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		
		glActiveTexture(GL_TEXTURE0)

		for image, data in SpriteInstancedRenderer.position_data.items():
			if data.size == 0: continue

			glUniform2fv(ts, 1, image.size)

			glBindTexture(GL_TEXTURE_2D, image.image_texture)

			glBindBuffer(GL_ARRAY_BUFFER, SpriteInstancedRenderer.position_vbo)
			glBufferData(GL_ARRAY_BUFFER, data, GL_STREAM_DRAW)
			# glBufferSubData(GL_ARRAY_BUFFER, 0, SpriteInstancedRenderer.position_data)

			glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, len(SpriteInstancedRenderer.instances[image]))