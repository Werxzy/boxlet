from .vk_module import *
from . import *


class FrameBuffer:
	def __init__(self, render_pass:'vk_pipeline.RenderPass', width, height, attachments:list):

		frame_buffer_info = VkFramebufferCreateInfo(
			renderPass = render_pass.vk_addr,
			attachmentCount = len(attachments),
			pAttachments = attachments,
			width = width,
			height = height,
			layers = 1
		)

		try:
			self.vk_addr = vkCreateFramebuffer(BVKC.logical_device.device, frame_buffer_info, None)
		except:
			if DEBUG_MODE:
				print(f'Failed to make framebuffer')

	def destroy(self):
		vkDestroyFramebuffer(BVKC.logical_device.device, self.vk_addr, None)

