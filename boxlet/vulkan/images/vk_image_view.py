from ..vk_module import *
from .. import *


class ImageView:
	def __init__(self, image, format, extent, aspect_mask = VK_IMAGE_ASPECT_COLOR_BIT) -> None:
		self.format = format
		self.extent = extent

		components = VkComponentMapping(
			VK_COMPONENT_SWIZZLE_IDENTITY,
			VK_COMPONENT_SWIZZLE_IDENTITY,
			VK_COMPONENT_SWIZZLE_IDENTITY,
			VK_COMPONENT_SWIZZLE_IDENTITY,
		)

		subresource_range = VkImageSubresourceRange(
			aspectMask = aspect_mask,
			baseMipLevel = 0, levelCount = 1,
			baseArrayLayer = 0, layerCount = 1
		)

		create_info = VkImageViewCreateInfo(
			image = image, viewType = VK_IMAGE_VIEW_TYPE_2D,
			format = format, components = components,
			subresourceRange = subresource_range
		)

		self.vk_addr = vkCreateImageView(BVKC.logical_device.device, create_info, None)
	
	def destroy(self):
		vkDestroyImageView(BVKC.logical_device.device, self.vk_addr, None)
