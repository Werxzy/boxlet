from .vk_module import *
from . import *


class SwapChainFrame:
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
			format = format.format, components = components,
			subresourceRange = subresource_range
		)

		self.image_view = vkCreateImageView(device = BVKC.logical_device.device, pCreateInfo = create_info, pAllocator = None)
		
		self.frame_buffer = None
		self.command_buffer = None

		self.in_flight = vk_sync.Fence()
		self.image_available = vk_sync.Semaphore()
		self.render_finished = vk_sync.Semaphore()

		# TODO if this is created in only one way
		# or requires all future variables
		# move everything into this init function

	def destroy(self):
		self.in_flight.destroy()
		self.image_available.destroy()
		self.render_finished.destroy()

		vkDestroyImageView(
			BVKC.logical_device.device, self.image_view, None
		)
		if self.frame_buffer is not None:
			vkDestroyFramebuffer(
				BVKC.logical_device.device, self.frame_buffer, None
			)
		