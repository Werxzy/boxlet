from .vk_module import *
from . import *


class ImageView:
	def __init__(self, image, format) -> None:
		components = VkComponentMapping(
			VK_COMPONENT_SWIZZLE_IDENTITY,
			VK_COMPONENT_SWIZZLE_IDENTITY,
			VK_COMPONENT_SWIZZLE_IDENTITY,
			VK_COMPONENT_SWIZZLE_IDENTITY,
		)

		subresource_range = VkImageSubresourceRange(
			aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
			baseMipLevel = 0, levelCount = 1,
			baseArrayLayer = 0, layerCount = 1
		)

		create_info = VkImageViewCreateInfo(
			image = image, viewType = VK_IMAGE_VIEW_TYPE_2D,
			format = format, components = components,
			subresourceRange = subresource_range
		)

		self.vk_addr = vkCreateImageView(device = BVKC.logical_device.device, pCreateInfo = create_info, pAllocator = None)

	# def init_frame_buffer(self, render_pass):
	# 	self.frame_buffer = vk_framebuffer.FrameBuffer(
	# 		render_pass, self.swapchain.extent, [self.image_view]
	# 		)
	
	def destroy(self):
		vkDestroyImageView(
			BVKC.logical_device.device, self.vk_addr, None
		)


class SwapChainFrame:
	def __init__(self, image, swapchain:'vk_swapchain.SwapChainBundle') -> None:
		self.image_view = ImageView(image, swapchain.format.format)

		self.frame_buffer = None
		self.command_buffer = None

		self.in_flight = vk_sync.Fence()
		self.image_available = vk_sync.Semaphore()
		self.render_finished = vk_sync.Semaphore()

	def destroy(self):
		self.in_flight.destroy()
		self.image_available.destroy()
		self.render_finished.destroy()

		self.image_view.destroy()
		if self.frame_buffer is not None:
			vkDestroyFramebuffer(
				BVKC.logical_device.device, self.frame_buffer, None
			)
		
