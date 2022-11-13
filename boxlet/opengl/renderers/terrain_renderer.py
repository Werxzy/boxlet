from math import ceil, floor

import numpy as np
from OpenGL.GL import *

from ... import BoxletGL, Model, Renderer, Texture, VertFragShader, lerp


class TerrainRenderer(Renderer):
	# position and size are in pixel coordinates

	vertex_shader = """
		#version 330
		layout(location = 0) in vec3 position;
		layout(location = 1) in vec2 texcoord;
		
		uniform mat4 model;
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
			fragColor = texture(tex, uv)*3 + 0.1;
		}
		"""

	shader = VertFragShader(vertex_shader, fragment_shader)

	def __init__(self, image:Texture, pass_name = ''):	
		super().__init__()
		
		self.image = image
		w,h = image.orignal.get_size()
		w1 = w-1
		h1 = h-1

		vertex = {
			'position' : [j for i in ([x, image.orignal.get_at((x,y))[0] * 0.3, h1-y] for x in range(w) for y in range(h)) for j in i],
			'texcoord' : [j for i in ([x / w, -y / h] for x in range(w) for y in range(h)) for j in i]
		}
		index = [j for i in ([x + y*w, x + (y+1)*w, x+1 + y*w, x+1 + y*w, x + (y+1)*w, x+1 + (y+1)*w] for x in range(w1) for y in range(h1)) for j in i]

		self.model = Model(
			vertex,
			index,
			dim = 3
		)

		self.model_matrix = np.array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		self.model.bind(self.shader)

		glBindVertexArray(0)
		BoxletGL.add_render_call(pass_name, self.shader, self.render)

	def render(self):
		self.shader.apply_uniform_matrix('model', self.model_matrix)
		
		BoxletGL.bind_vao(self.vao)
		BoxletGL.bind_texture(GL_TEXTURE0, GL_TEXTURE_2D, self.image.image_texture)

		glDrawElements(GL_TRIANGLES, self.model.index_count, GL_UNSIGNED_INT, None)


	def get_height(self, x, z):
		#TODO correct sample position based on model matrix, or only allow translating the model and no rotation
		w, h = self.image.orignal.get_size()

		if x > w or z > h or x <= -1 or z <= -1:
			return 0

		w, h = w - 1, h - 1
		z = h - z

		def sample_height(xi:int, zi:int):
			if xi > w or zi > h or xi <= 0 or zi <= 0:
				return 0
			return self.image.orignal.get_at((xi, zi))[0]

		if isinstance(x, float) or isinstance(z, float):
			fx, cx, fz, cz = floor(x), ceil(x), floor(z), ceil(z)
			tx = x - fx
			tz = z - fz
			a = sample_height(fx, fz)
			b = sample_height(cx, fz)
			c = sample_height(fx, cz)
			d = sample_height(cx, cz)
			h = lerp(lerp(a,b,tx), lerp(c,d,tx), tz)
		else:
			h = sample_height(x,z)

		return h * 0.3