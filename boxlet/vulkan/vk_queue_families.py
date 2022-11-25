from . import *


class QueueFamilyIndices:
	def __init__(self, physical_device, instance, surface) -> None:
		self.physical_device = physical_device
		self.instance = instance
		self.surface = surface

		queue_families = vkGetPhysicalDeviceQueueFamilyProperties(physical_device)

		surface_support = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceSupportKHR')

		if DEBUG_MODE:
			print(f'There are {len(queue_families)} queue families available on the system.')

		for i, fam in enumerate(queue_families):
			"""
			* // Provided by VK_VERSION_1_0
				typedef struct VkQueueFamilyProperties {
				VkQueueFlags    queueFlags;
				uint32_t        queueCount;
				uint32_t        timestampValidBits;
				VkExtent3D      minImageTransferGranularity;
				} VkQueueFamilyProperties;
				queueFlags is a bitmask of VkQueueFlagBits indicating capabilities of the queues in this queue family.
				queueCount is the unsigned integer count of queues in this queue family. Each queue family must support 
				at least one queue.
				timestampValidBits is the unsigned integer count of meaningful bits in the timestamps written via 
				vkCmdWriteTimestamp. The valid range for the count is 36..64 bits, or a value of 0, 
				indicating no support for timestamps. Bits outside the valid range are guaranteed to be zeros.
				minImageTransferGranularity is the minimum granularity supported for image transfer 
				operations on the queues in this queue family.
			
				* // Provided by VK_VERSION_1_0
					typedef enum VkQueueFlagBits {
					VK_QUEUE_GRAPHICS_BIT = 0x00000001,
					VK_QUEUE_COMPUTE_BIT = 0x00000002,
					VK_QUEUE_TRANSFER_BIT = 0x00000004,
					VK_QUEUE_SPARSE_BINDING_BIT = 0x00000008,
					} VkQueueFlagBits;
			"""

			if fam.queueFlags & VK_QUEUE_GRAPHICS_BIT:
				self.graphics_family = i

			if surface_support(physical_device, i, surface):
				self.present_family = i

			if self.is_complete():
				break
				
		if DEBUG_MODE:
			print(f"Queue Family {self.graphics_family} is suitable for graphics")
			print(f"Queue Family {self.present_family} is suitable for presenting")

	def is_complete(self):
		return self.graphics_family is not None and self.present_family is not None

	def get_queue(self, logical_device:'vk_device.LogicalDevice'):
		return [
			vkGetDeviceQueue(logical_device.device, self.graphics_family, 0),
			vkGetDeviceQueue(logical_device.device, self.present_family, 0)
		]

