from . import *
from .vk_library import *


class FramebufferInput:

	def __init__(self, logical_device:vk_device.LogicalDevice, render_pass, swapchain_extent, frames:list[vk_frame.SwapChainFrame]) -> None:
		self.logical_device = logical_device
		self.render_pass = render_pass
		self.swapchain_extent = swapchain_extent

		for i,frame in enumerate(frames): # TODO individualize frame buffers and assign them to this class
			attachments = [frame.image_view]

			frame_buffer_info = VkFramebufferCreateInfo(
				renderPass = render_pass,
				attachmentCount = len(attachments),
				pAttachments = attachments,
				width = swapchain_extent.width,
				height = swapchain_extent.height,
				layers = 1
			)

			try:
				frame.frame_buffer = vkCreateFramebuffer(logical_device.device, frame_buffer_info, None)
				if DEBUG_MODE:
					print(f'Made framebuffer for frame {i}')
			except:
				if DEBUG_MODE:
					print(f'Failed to make framebuffer for frame {i}')

		
