from math import floor

from .. import FauxTexture, FrameBuffer, Texture
from ..vk_module import *


class RenderTarget(TrackedInstances):
	'Encapsulates everything about the object that is being rendered to.'

	def __init__(self, extent) -> None:
		self.extent = extent

	def remake(self, width, height):
		'''
		reinitializes anything that may have gone out of date.
		
		This is usually used to remake the framebuffers.
		'''

	def get_color_images(self) -> list[Texture|FauxTexture]:
		...

	def get_depth_image(self) -> Texture|FauxTexture:
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
	def __init__(self, width = 0, height = 0, width_mult = 1, height_mult = 1, layers = 1, filter = 'clamp edge') -> None:
		# Setting width and/or height to a non-zero value with set the corresponding component.
		# Otherwise, multiply the display's resoultion by the 'mult' value and round down.

		self.size_data = (width, height, width_mult, height_mult)
		width, height = self.gen_size(BVKC.width, BVKC.height)
		# Regenerates the width and height based on the given parameters.

		super().__init__(VkExtent2D(width, height))

		self.images:list[Texture] = []
		
		for _ in range(layers):
			image = Texture(
				# TODO add control over the formats
				format = VK_FORMAT_R16G16B16A16_SFLOAT,
				extent = [width, height],
				tiling = VK_IMAGE_TILING_OPTIMAL,
				usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,

				image_layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
				access_mask = VK_ACCESS_SHADER_READ_BIT,
				stage_mask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
				filter = filter
			)
			self.images.append(image)
		
		self.depth_buffer = Texture(
			format = BVKC.physical_device.find_depth_format(),
			extent = [width, height],
			tiling = VK_IMAGE_TILING_OPTIMAL,
			
			image_layout = VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_STENCIL_ATTACHMENT_OPTIMAL,
			usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
			aspect_mask = VK_IMAGE_ASPECT_DEPTH_BIT,
			filter = filter
		)

		self.frame_buffer = None

	def gen_size(self, width, height):
		(w, h, wm, hm) = self.size_data
		return (
			max(w if w else floor(wm * width), 1),
			max(h if h else floor(hm * height), 1)
		)

	def remake(self, width, height):
		if self.frame_buffer:
			self.frame_buffer.destroy()

		width, height = self.gen_size(width, height)
		self.extent = VkExtent2D(width, height)

		for i in self.images:
			i.remake([width, height, 1])
		self.depth_buffer.remake([width, height, 1])


	def get_color_images(self) -> list[Texture|FauxTexture]:
		return self.images

	def get_depth_image(self) -> Texture|FauxTexture:
		return self.depth_buffer

	def init_frame_buffer(self):
		self.frame_buffer = FrameBuffer(
			self.recent_render_pass, 
			self.extent.width, self.extent.height, 
			[
				*[i.image_view.vk_addr for i in self.images], 
				self.depth_buffer.image_view.vk_addr
			])

	def get_frame_buffer(self) -> FrameBuffer:
		return self.frame_buffer

	def on_destroy(self):
		for i in self.images:
			i.destroy()
		self.depth_buffer.destroy()

		if self.frame_buffer:
			self.frame_buffer.destroy()

	def end(self, command_buffer):
		# Necessary barrier to prevent visual glitches.
		# Though not sure if it is the correct fix.
		vkCmdPipelineBarrier(
			command_buffer, 
			VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 
			VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
			0, 0, None, 0, None, 0, None
		)
