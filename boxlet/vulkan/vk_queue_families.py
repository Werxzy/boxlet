from . import DEBUG_MODE
from .vk_module import *

if TYPE_CHECKING:
	from . import VulkanInstance


class QueueFamilyIndices:
	def __init__(self, instance:'VulkanInstance', surface) -> None:
		self.instance = instance
		self.surface = surface

		queue_families = vkGetPhysicalDeviceQueueFamilyProperties(BVKC.physical_device.vk_addr)

		surface_support = vkGetInstanceProcAddr(instance.vk_addr, 'vkGetPhysicalDeviceSurfaceSupportKHR')

		if DEBUG_MODE:
			print(f'There are {len(queue_families)} queue families available on the system.')

		for i, fam in enumerate(queue_families):

			if fam.queueFlags & VK_QUEUE_GRAPHICS_BIT:
				self.graphics_family = i

			if surface_support(BVKC.physical_device.vk_addr, i, surface):
				self.present_family = i

			if self.is_complete():
				break
				
		if DEBUG_MODE:
			print(f"Queue Family {self.graphics_family} is suitable for graphics")
			print(f"Queue Family {self.present_family} is suitable for presenting")

	def is_complete(self):
		return self.graphics_family is not None and self.present_family is not None

	def get_queue(self):
		return [
			vkGetDeviceQueue(BVKC.logical_device.device, self.graphics_family, 0),
			vkGetDeviceQueue(BVKC.logical_device.device, self.present_family, 0)
		]

