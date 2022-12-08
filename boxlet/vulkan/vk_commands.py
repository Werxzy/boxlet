from .vk_module import *
from . import *


class CommandPool:

	def __init__(self, queue_family:vk_queue_families.QueueFamilyIndices, surface, instance) -> None:
		self.surface = surface
		self.instance = instance

		pool_info = VkCommandPoolCreateInfo(
			flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
			queueFamilyIndex = queue_family.graphics_family
		)

		try:
			self.pool = vkCreateCommandPool(BVKC.logical_device.device, pool_info, None)
			if DEBUG_MODE:
				print('Created command pool')

		except:
			self.pool = None
			if DEBUG_MODE:
				print('Failed to create command pool')
			# don't entirely like this error checking method

	def destroy(self):
		vkDestroyCommandPool(BVKC.logical_device.device, self.pool, None)

class CommandBuffer:
	def __init__(self, command_pool:CommandPool) -> None:
			
		alloc_info = VkCommandBufferAllocateInfo(
			commandPool = command_pool.pool,
			level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
			commandBufferCount = 1
		)

		try:
			self.vk_addr = vkAllocateCommandBuffers(BVKC.logical_device.device, alloc_info)[0]
			if DEBUG_MODE:
				print(f'Allocated command buffer')
		except Exception as e:
			if DEBUG_MODE:
				print(f'Failed to allocate command buffer')
			raise e

	
