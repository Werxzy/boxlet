from .. import RenderingStep
from ..vk_module import *

if TYPE_CHECKING:
	from .. import RenderTarget


class RenderPass(TrackedInstances, RenderingStep):

	def __init__(self, render_target:'RenderTarget' = None, priority = 0):
		'Render Target as none assumes it will render to the primary render target.'

		super().__init__(priority)
		self.attach_to_base()

		self.render_target = render_target if render_target else BVKC.swapchain
		self.render_target.set_recent_render_pass(self)

		attachment_count = 0
		attachments = []
		color_attachment_refs = []
		depth_attachment_ref = []

		for attach in self.render_target.color_attachments:
			attachments.append(attach.get_description())
			color_attachment_refs.append(attach.get_reference(attachment_count))

			attachment_count += 1

		if attach := self.render_target.depth_attachment:
			attachments.append(attach.get_description())
			depth_attachment_ref = [attach.get_reference(attachment_count)]

			attachment_count += 1

		subpass = VkSubpassDescription(
			pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
			colorAttachmentCount = len(color_attachment_refs),
			pColorAttachments = color_attachment_refs,
			pDepthStencilAttachment = depth_attachment_ref
		)

		render_pass_info = VkRenderPassCreateInfo(
			attachmentCount = len(attachments),
			pAttachments = attachments,
			subpassCount = 1,
			pSubpasses = subpass
		)

		self.vk_addr = vkCreateRenderPass(BVKC.logical_device.device, render_pass_info, None)

		self.clear_values = [VkClearValue([[1.0, 0.5, 0.25, 1.0]]), VkClearValue([[1.0, 0.0]])]

	def begin(self, command_buffer):
		self.render_target.begin(command_buffer)

		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = self.render_target.get_frame_buffer().vk_addr,
			renderArea = [[0,0], self.render_target.extent],
			clearValueCount = 2,
			pClearValues = self.clear_values
		)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

	def end(self, command_buffer):
		vkCmdEndRenderPass(command_buffer)
		
		self.render_target.end(command_buffer)

	def on_destroy(self):
		vkDestroyRenderPass(BVKC.logical_device.device, self.vk_addr, None)

		