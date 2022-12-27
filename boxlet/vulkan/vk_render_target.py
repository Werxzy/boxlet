from .vk_module import *
from . import *


class RenderTarget(TrackedInstances):
	'Encapsulates everything about the object that is being rendered to.'

	def __init__(self, format, extent) -> None:
		self.format = format
		self.extent = extent

	def remake(self, width, height):
		'''
		reinitializes anything that may have gone out of date.
		
		This is usually used to remake the framebuffers.
		'''

	def get_image(self):
		'Used by BoxletVK to get the correct image to sample from?'

	def get_image_initial_layouts(self) -> list:
		...

	def get_image_final_layouts(self) -> list:
		...

	def get_image_attachment_layouts(self) -> list:
		...

	def get_frame_buffer(self) -> FrameBuffer:
		'Used by BoxletVK to get the correct framebuffer to render to.'

	def init_frame_buffer(self):
		'initializes the buffers associated with the render target.'

	def set_recent_render_pass(self, render_pass):
		'Sets the render pass used for creating frame buffers'
		self.recent_render_pass = render_pass

	def on_destroy(self):
		...

	def begin(self, command_buffer):
		...
	
	def end(self, command_buffer):
		...


class SimpleRenderTarget(RenderTarget):
	def __init__(self, width, height) -> None:
		super().__init__(VK_FORMAT_R16G16B16A16_SFLOAT, VkExtent2D(width, height))
		# TODO, add scaling settings like in opengl version

		self.image = None
		self.depth_buffer = None
		self.frame_buffer = None

		self.extent = VkExtent2D(width, height)

		self.image = Texture(
			format = self.format,
			extent = [width, height],
			tiling = VK_IMAGE_TILING_OPTIMAL,
			usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,

			image_layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
			access_mask = VK_ACCESS_SHADER_READ_BIT,
			stage_mask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT
		)
		
		self.depth_buffer = Texture(
			format = vk_device.find_depth_format(BVKC.physical_device),
			extent = [width, height],
			tiling = VK_IMAGE_TILING_OPTIMAL,
			usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
			aspect_mask = VK_IMAGE_ASPECT_DEPTH_BIT,
		)

	def remake(self, width, height):

		if self.frame_buffer:
			self.frame_buffer.destroy()

		self.extent = VkExtent2D(width, height)

		self.image.remake([width, height, 1])
		self.depth_buffer.remake([width, height, 1])

	def get_image(self):
		return self.image

	def get_image_initial_layouts(self):
		return [
			self.image.image_layout,
			# VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, 
			self.depth_buffer.image_layout
		]

	def get_image_final_layouts(self):
		return [
			VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, 
			# VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, 
			VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
		]

	def get_image_attachment_layouts(self):
		return [
			VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, 
			VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
		]

	def init_frame_buffer(self):
		self.frame_buffer = FrameBuffer(
			self.recent_render_pass, 
			self.extent.width, self.extent.height, 
			[
				self.image.image_view.vk_addr, 
				self.depth_buffer.image_view.vk_addr
			])

	def get_frame_buffer(self) -> FrameBuffer:
		return self.frame_buffer

	def on_destroy(self):
		self.image.destroy()
		self.depth_buffer.destroy()

		if self.frame_buffer:
			self.frame_buffer.destroy()

	def begin(self, command_buffer):
		...
		# self.image.transition_image_layout(
		# 	VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
		# 	VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
		# 	VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
		# 	command_buffer
		# )

	def end(self, command_buffer):
		# self.image.transition_image_layout(
		# 	VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
		# 	VK_ACCESS_SHADER_READ_BIT,
		# 	VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
		# 	command_buffer
		# )
		vkCmdPipelineBarrier(
			command_buffer, 
			VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 
			VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
			0, 0, None, 0, None, 0, None
		)
