from boxlet import manager, Shader, VertFragShader, Model, Renderer, Shader
from OpenGL.GL import *


class FrameBufferStep(Renderer):
	# creates a frame

	def __init__(self, width = 0, height = 0, width_mult = 1, height_mult = 1, depth = True, queue = 0) -> None:
		'''
		Setting a dimension size (width or height) will set the size of the frame buffer and it won't change reguardless of window resizing.
		leaving the non 'mult' dimensions to zero will result in the size of the frame buffer to equal the window size multiplied by the 'mult' parameter.\n
		'''

		super().__init__(queue)

		self.size_settings = [width, height, width_mult, height_mult]
		self.depth = depth

		self.frame_buffer = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER, self.frame_buffer)

		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)

		if self.depth:
			self.render_buffer = glGenRenderbuffers(1)
			
		self.rebuild(False)

	def rebuild(self, rebind = True):
		width, height = self.get_size()

		if rebind:
			glBindFramebuffer(GL_FRAMEBUFFER, self.frame_buffer)

		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR) # GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # GL_NEAREST)

		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)

		if self.depth:
			glBindRenderbuffer(GL_RENDERBUFFER, self.render_buffer)
			glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.render_buffer)

		glBindFramebuffer(GL_FRAMEBUFFER, 0)

	def render(self):
		size = self.get_size()
		self.viewport(0, 0, *size)
		Shader.set_global_uniform('cameraSize', size)

		glBindFramebuffer(GL_FRAMEBUFFER, self.frame_buffer)
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)

	def get_size(self):
		return [self.size_settings[0] or round(self.size_settings[2] * manager.screen_size[0]),
				self.size_settings[1] or round(self.size_settings[3] * manager.screen_size[1])]


class ApplyShaderToFrame(Renderer):
	vertex_screen_shader = """
		#version 330 core
		layout (location = 0) in vec2 aPos;
		layout (location = 1) in vec2 aTexCoords;
		out vec2 TexCoords;
		void main() {
			TexCoords = aTexCoords;
			gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0); 
		}  
		"""

	fragment_screen_shader = """
		#version 330 core
		out vec4 FragColor;
		in vec2 TexCoords;
		uniform sampler2D screenTexture;
		void main() {
			FragColor = vec4(texture(screenTexture, TexCoords).rgb, 1.0);
		} 
		"""
	default_shader = VertFragShader(vertex_screen_shader, fragment_screen_shader)
	
	rect_model = Model([-1, -1, 0, 0,  -1, 1, 0, 1,  1, 1, 1, 1,  1, -1, 1, 0])
	rect_vao = glGenVertexArrays(1)
	glBindVertexArray(rect_vao)
	rect_model.bind()
	glBindVertexArray(0)

	def __init__(self, from_frame, to_frame = 0, shader:VertFragShader = None, queue = 1000):
		"""
		Renders one frame buffer onto another using a shader, if one is provided.
		"""

		super().__init__(queue)

		self.from_frame = from_frame
		self.to_frame = to_frame
		self.shader = shader or self.default_shader

	def render(self):
		self.viewport(0, 0, *manager.screen_size)

		glBindFramebuffer(GL_FRAMEBUFFER, self.to_frame)
		glDisable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)
		
		glUseProgram(self.shader.program)
		glBindVertexArray(ApplyShaderToFrame.rect_vao)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.from_frame)
		glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


class ApplyDitherToFrame(Renderer):
	dither_screen_shader = """
		#version 330 core
		out vec4 FragColor;
		in vec2 TexCoords;
		uniform sampler2D screenTexture;
		uniform float random;

		float dither(vec2 v){
			return (fract(sin(dot(v, vec2(12.9898,78.233))) * 43758.5453) - 0.5) / 256.0;
			// (multiplying by 2 removes the last of the banding at the cost of noise)
		}

		void main() {
			vec3 col = texture(screenTexture, TexCoords).rgb + dither(TexCoords + fract(random));
			FragColor = vec4(col, 1.0);
		} 
		"""
	shader = VertFragShader(ApplyShaderToFrame.vertex_screen_shader, dither_screen_shader, ['random'])

	def __init__(self, from_frame, to_frame = 0, queue = 1000):
		"""
		Renders one frame buffer onto another using a shader, if one is provided.
		
		Uses a dithering shader to reduce color banding.
		"""

		super().__init__(queue)

		self.from_frame = from_frame
		self.to_frame = to_frame
		
	def render(self):
		self.viewport(0, 0, *manager.screen_size)

		glBindFramebuffer(GL_FRAMEBUFFER, self.to_frame)
		glDisable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)
		
		glUseProgram(self.shader.program)
		glUniform1f(self.shader.uniforms['random'], manager.time)
		glBindVertexArray(ApplyShaderToFrame.rect_vao)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.from_frame)
		glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

class SimpleClearStep(Renderer):
	def render(self):
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT)
