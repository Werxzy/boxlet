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

		initial_layouts = self.render_target.get_image_initial_layouts()
		final_layouts = self.render_target.get_image_final_layouts()
		attach_layouts = self.render_target.get_image_attachment_layouts()

		color_attachment = VkAttachmentDescription(
			format = self.render_target.format,
			samples = VK_SAMPLE_COUNT_1_BIT,

			loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
			storeOp = VK_ATTACHMENT_STORE_OP_STORE,
			
			stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
			stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,

			initialLayout = initial_layouts[0],
			finalLayout = final_layouts[0]
		)

		color_attachment_ref = VkAttachmentReference(
			attachment = 0,
			layout = attach_layouts[0]
		)

		depth_attachment = VkAttachmentDescription(
			format = BVKC.physical_device.find_depth_format(),
			samples = VK_SAMPLE_COUNT_1_BIT,

			loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
			storeOp = VK_ATTACHMENT_STORE_OP_STORE,
			
			stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
			stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,

			initialLayout = initial_layouts[1],
			finalLayout = final_layouts[1]
		)

		depth_attachment_ref = VkAttachmentReference(
			attachment = 1,
			layout = attach_layouts[1]
		)

		attachments = [color_attachment, depth_attachment]

		subpass = VkSubpassDescription(
			pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
			colorAttachmentCount = 1,
			pColorAttachments = [color_attachment_ref],
			pDepthStencilAttachment = [depth_attachment_ref]
		)

		render_pass_info = VkRenderPassCreateInfo(
			attachmentCount = len(attachments),
			pAttachments = attachments,
			subpassCount = 1,
			pSubpasses = subpass
		)

		self.vk_addr = vkCreateRenderPass(BVKC.logical_device.device, render_pass_info, None)

	def begin(self, command_buffer):
		self.render_target.begin(command_buffer)

		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = self.render_target.get_frame_buffer().vk_addr,
			renderArea = [[0,0], self.render_target.extent],
			clearValueCount = 2,
			pClearValues = [VkClearValue([[1.0, 0.5, 0.25, 1.0]]), VkClearValue([[1.0, 0.0]])]
		)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

	def end(self, command_buffer):
		vkCmdEndRenderPass(command_buffer)
		
		self.render_target.end(command_buffer)

	def on_destroy(self):
		vkDestroyRenderPass(BVKC.logical_device.device, self.vk_addr, None)

		