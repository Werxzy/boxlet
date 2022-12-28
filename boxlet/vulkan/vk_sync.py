from .vk_module import *
from . import *


class Semaphore:
	def __init__(self):
		semaphore_info = VkSemaphoreCreateInfo()

		try:
			self.vk_addr = vkCreateSemaphore(BVKC.logical_device.device, semaphore_info, None)
		except Exception as ex:
			if DEBUG_MODE:
				print('Failed to create semaphore')
			raise ex

	def destroy(self):
		vkDestroySemaphore(BVKC.logical_device.device, self.vk_addr, None)

class Fence:
	def __init__(self):
		fence_info = VkFenceCreateInfo(flags = VK_FENCE_CREATE_SIGNALED_BIT)

		try:
			self.vk_addr = vkCreateFence(BVKC.logical_device.device, fence_info, None)
		except Exception as ex:
			if DEBUG_MODE:
				print('Failed to create fence')
			raise ex

	def wait_for(self, *additional_fences:'Fence'):
		fences = [self.vk_addr]
		if additional_fences:
			fences.extend(f.vk_addr for f in additional_fences)

		vkWaitForFences(
			device = BVKC.logical_device.device, fenceCount = len(fences), pFences = fences,
			waitAll = VK_TRUE, timeout = 1000000000
		)

	def reset(self, *additional_fences:'Fence'):
		fences = [self.vk_addr]
		if additional_fences:
			fences.extend(f.vk_addr for f in additional_fences)

		vkResetFences(
			device = BVKC.logical_device.device, fenceCount = len(fences), pFences = fences
		)

	def destroy(self):
		vkDestroyFence(BVKC.logical_device.device, self.vk_addr, None)
		