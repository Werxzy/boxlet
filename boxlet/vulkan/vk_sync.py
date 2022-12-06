from . import *
from .vk_library import *


class Semaphore:
	def __init__(self, logical_device:vk_device.LogicalDevice):
		self.logical_device = logical_device
		semaphore_info = VkSemaphoreCreateInfo()

		try:
			self.vk_id = vkCreateSemaphore(logical_device.device, semaphore_info, None)
		except Exception as ex:
			if DEBUG_MODE:
				print('Failed to create semaphore')
			raise ex

	def destroy(self):
		vkDestroySemaphore(self.logical_device.device, self.vk_id, None)

class Fence:
	def __init__(self, logical_device:vk_device.LogicalDevice):
		self.logical_device = logical_device
		fence_info = VkFenceCreateInfo(flags = VK_FENCE_CREATE_SIGNALED_BIT)

		try:
			self.vk_id = vkCreateFence(logical_device.device, fence_info, None)
		except Exception as ex:
			if DEBUG_MODE:
				print('Failed to create fence')
			raise ex

	def wait_for(self, *additional_fences:'Fence'):
		fences = [self.vk_id]
		if additional_fences:
			fences.extend(f.vk_id for f in additional_fences)

		vkWaitForFences(
			device = self.logical_device.device, fenceCount = len(fences), pFences = fences,
			waitAll = VK_TRUE, timeout = 1000000000
		)

	def reset(self, *additional_fences:'Fence'):
		fences = [self.vk_id]
		if additional_fences:
			fences.extend(f.vk_id for f in additional_fences)

		vkResetFences(
			device = self.logical_device.device, fenceCount = len(fences), pFences = fences
		)

	def destroy(self):
		vkDestroyFence(self.logical_device.device, self.vk_id, None)