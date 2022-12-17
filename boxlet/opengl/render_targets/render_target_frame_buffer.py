from OpenGL.GL import *

from .. import BoxletGL, Model, RenderTarget, Shader, VertFragShader
from ... import manager


class FrameBufferStep(RenderTarget):
	# creates a frame

	def __init__(self, width = 0, height = 0, width_mult = 1, height_mult = 1, depth = True, nearest = False, queue = 0, pass_names:list[str] = None) -> None:
		'''
		Setting a dimension size (width or height) will set the size of the frame buffer and it won't change reguardless of window resizing.
		leaving the non 'mult' dimensions to zero will result in the size of the frame buffer to equal the window size multiplied by the 'mult' parameter.\n
		'''

		super().__init__(queue, pass_names)

		self.size_settings = [width, height, width_mult, height_mult]
		self.depth = depth
		self.nearest = nearest

		self._frame_buffer = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER, self._frame_buffer)

		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)

		if self.depth:
			self.render_buffer = glGenRenderbuffers(1)
			
		self.rebuild(False)

	def rebuild(self, rebind = True):
		width, height = self.get_size()

		if rebind:
			glBindFramebuffer(GL_FRAMEBUFFER, self._frame_buffer)

		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST if self.nearest else GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST if self.nearest else GL_LINEAR)

		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)

		if self.depth:
			glBindRenderbuffer(GL_RENDERBUFFER, self.render_buffer)
			glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.render_buffer)

		glBindFramebuffer(GL_FRAMEBUFFER, 0)

	def prepare(self):
		size = self.get_size()
		BoxletGL.viewport(0, 0, *size)
		Shader.set_global_uniform('box_frameSize', size)
		Shader.set_global_uniform('box_cameraSize', size)

		glBindFramebuffer(GL_FRAMEBUFFER, self._frame_buffer)
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)

	def get_size(self):
		return [self.size_settings[0] or round(self.size_settings[2] * manager.display_size[0]),
				self.size_settings[1] or round(self.size_settings[3] * manager.display_size[1])]


class ApplyShaderToFrame(RenderTarget):
	vertex_screen_shader = """
		#version 330 core
		layout (location = 0) in vec2 position;
		layout (location = 1) in vec2 texcoord;
		out vec2 uv;
		void main() {
			uv = texcoord;
			gl_Position = vec4(position.x, position.y, 0.0, 1.0); 
		}  
		"""

	fragment_screen_shader = """
		#version 330 core
		out vec4 FragColor;
		in vec2 uv;
		uniform sampler2D screenTexture;
		void main() {
			FragColor = vec4(texture(screenTexture, uv).rgb, 1.0);
		} 
		"""

	default_shader = None
	rect_model = None
	rect_vao = None

	def __init__(self, from_texture, to_frame = 0, shader:VertFragShader = None, queue = 1000, pass_names:list[str] = None):
		"""
		Renders one frame buffer onto another using a shader, if one is provided.
		"""

		super().__init__(queue, pass_names)

		if ApplyShaderToFrame.default_shader == None:
			ApplyShaderToFrame.default_shader = VertFragShader(ApplyShaderToFrame.vertex_screen_shader, ApplyShaderToFrame.fragment_screen_shader)

		ApplyShaderToFrame.init_rect(ApplyShaderToFrame.default_shader)		

		self.from_texture = from_texture
		self.to_frame = to_frame
		self.shader = shader or self.default_shader

	@staticmethod
	def init_rect(shader):
		if ApplyShaderToFrame.rect_model: return

		ApplyShaderToFrame.rect_model = Model.gen_quad_2d()
		ApplyShaderToFrame.rect_vao = glGenVertexArrays(1)
		glBindVertexArray(ApplyShaderToFrame.rect_vao)
		ApplyShaderToFrame.rect_model.bind(shader)
		glBindVertexArray(0)

	def prepare(self):
		BoxletGL.viewport(0, 0, *manager.display_size)

		glBindFramebuffer(GL_FRAMEBUFFER, self.to_frame)
		glDisable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)
		
		self.shader.use()
		BoxletGL.bind_vao(ApplyShaderToFrame.rect_vao)
		BoxletGL.bind_texture(GL_TEXTURE0, GL_TEXTURE_2D, self.from_texture)
		
		glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


class ApplyDitherToFrame(RenderTarget):
	dither_screen_shader = """
		#version 330 core
		out vec4 FragColor;
		in vec2 uv;
		uniform sampler2D screenTexture;
		uniform float random;

		float dither(vec2 v){
			return (fract(sin(dot(v, vec2(12.9898,78.233))) * 43758.5453) - 0.5) / 256.0;
			// (multiplying by 2 removes the last of the banding at the cost of noise)
		}

		void main() {
			vec3 col = texture(screenTexture, uv).rgb + dither(uv + fract(random));
			FragColor = vec4(col, 1.0);
		} 
		"""
	shader = None

	def __init__(self, from_texture, to_frame = 0, queue = 1000, pass_names:list[str] = None):
		"""
		Renders one frame buffer onto another using a shader, if one is provided.
		
		Uses a dithering shader to reduce color banding.
		"""

		if ApplyDitherToFrame.shader is None:
			ApplyDitherToFrame.shader = VertFragShader(ApplyShaderToFrame.vertex_screen_shader, ApplyDitherToFrame.dither_screen_shader)

		ApplyShaderToFrame.init_rect(ApplyDitherToFrame.shader)

		super().__init__(queue, pass_names)

		self.from_texture = from_texture
		self.to_frame = to_frame
		
	def prepare(self):
		BoxletGL.viewport(0, 0, *manager.display_size)

		glBindFramebuffer(GL_FRAMEBUFFER, self.to_frame)
		glDisable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)
		
		self.shader.use()
		self.shader.apply_uniform('random', manager.time)
		BoxletGL.bind_vao(ApplyShaderToFrame.rect_vao)
		BoxletGL.bind_texture(GL_TEXTURE0, GL_TEXTURE_2D, self.from_texture)

		glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


class SimpleClearStep(RenderTarget):
	def prepare(self):
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)
		Shader.set_global_uniform('frameSize', manager.display_size)

