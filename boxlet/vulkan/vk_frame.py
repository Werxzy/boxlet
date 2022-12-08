from .vk_module import *
from . import *


class ImageView:
	def __init__(self, image, format, extent) -> None:
		self.format = format
		self.extent = extent

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

	def init_frame_buffer(self, render_pass):
		return FrameBuffer(
			render_pass, self.extent, [self.vk_addr]
			)
	
	def destroy(self):
		vkDestroyImageView(
			BVKC.logical_device.device, self.vk_addr, None
		)


class SwapChainFrame:
	def __init__(self, image, swapchain:'vk_swapchain.SwapChainBundle') -> None:
		self.image_view = ImageView(image, swapchain.format.format, swapchain.extent)

		self.frame_buffer:FrameBuffer = None
		self.command_buffer = None

		self.in_flight = vk_sync.Fence()
		self.image_available = vk_sync.Semaphore()
		self.render_finished = vk_sync.Semaphore()

	def init_buffers(self, render_pass, command_pool:'CommandPool'):
		self.frame_buffer = self.image_view.init_frame_buffer(render_pass)

		alloc_info = VkCommandBufferAllocateInfo(
			commandPool = command_pool.pool,
			level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
			commandBufferCount = 1
		)

		self.command_buffer = vkAllocateCommandBuffers(BVKC.logical_device.device, alloc_info)[0]

	def destroy(self):
		self.in_flight.destroy()
		self.image_available.destroy()
		self.render_finished.destroy()

		self.image_view.destroy()
		if self.frame_buffer is not None:
			self.frame_buffer.destroy()
		
