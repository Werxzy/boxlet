from .. import RenderingStep
from ..vk_module import *

if TYPE_CHECKING:
	from .. import FauxTexture, RenderTarget, Texture


class RenderPass(TrackedInstances, RenderingStep):

	def __init__(self, 
			render_target:'RenderTarget' = None, 
			*,
			priority = 0,
			clear_colors = []
		):
		'Render Target as none assumes it will render to the primary render target.'

		super().__init__(priority)
		self.attach_to_base()

		self.render_target = render_target if render_target else BVKC.swapchain
		self.render_target.set_recent_render_pass(self)

		self.sample_count = VK_SAMPLE_COUNT_1_BIT

		attachments = []
		color_attachment_refs = []
		depth_attachment_ref = []
		self.clear_values = []

		# Currently, if the swapchain is the render target
		# we assume that the final layout is always preseting.
		# Otherwise, we assume it's read by a shader 
		if render_target:
			final_layout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
		else:
			final_layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL

		for i, image in enumerate(self.render_target.get_color_images()):
			attachments.append(self.create_description(image, final_layout))

			color_attachment_refs.append(
				VkAttachmentReference(
					attachment = i,
					layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
				)
			)

			if i < len(clear_colors):
				self.clear_values.append(VkClearValue([clear_colors[i]]))
			else:
				self.clear_values.append(VkClearValue([[0.0, 0.0, 0.0, 1.0]]))


		if image := self.render_target.get_depth_image():
			if render_target:
				final_layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
			else:
				final_layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL

			attachments.append(self.create_description(image, final_layout))

			depth_attachment_ref = [
				VkAttachmentReference(
					attachment = len(attachments) - 1,
					layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
				)
			]

			self.clear_values.append(VkClearValue(None, [1.0, 0]))
		
		# currently, we are assuming that all subpasses will be using all attachments
		# even though there's only one subpass

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

	def get_color_attachment_count(self):
		return len(self.render_target.get_color_images())

	def create_description(self, image:'Texture|FauxTexture', final_layout):
		return VkAttachmentDescription(
			format = image.format,
			samples = image.sample_count,

			loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
			storeOp = VK_ATTACHMENT_STORE_OP_STORE,
			
			#TODO check for stencil on texture
			stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
			stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,

			initialLayout = image.image_layout,
			finalLayout = final_layout
		)

	def begin(self, command_buffer):
		self.render_target.begin(command_buffer)

		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = self.render_target.get_frame_buffer().vk_addr,
			renderArea = [[0,0], self.render_target.extent],
			clearValueCount = len(self.clear_values),
			pClearValues = self.clear_values
		)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

	def end(self, command_buffer):
		vkCmdEndRenderPass(command_buffer)
		
		self.render_target.end(command_buffer)

	def on_destroy(self):
		vkDestroyRenderPass(BVKC.logical_device.device, self.vk_addr, None)

		