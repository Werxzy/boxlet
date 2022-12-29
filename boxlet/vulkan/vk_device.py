from . import DEBUG_MODE
from .vk_module import *

if TYPE_CHECKING:
	from . import QueueFamilyIndices, VulkanInstance


"""
	Vulkan separates the concept of physical and logical devices. 
	A physical device usually represents a single complete implementation of Vulkan 
	(excluding instance-level functionality) available to the host, 
	of which there are a finite number. 
  
	A logical device represents an instance of that implementation 
	with its own state and resources independent of other logical devices.
"""


class PhysicalDevice:
	def __init__(self, instance:'VulkanInstance'):

		"""
		Choose a suitable physical device from a list of candidates.

		Note: Physical devices are neither created nor destroyed, they exist
		independently to the program.
		"""

		if DEBUG_MODE:
			print("Choosing Physical Device")

		availableDevices = vkEnumeratePhysicalDevices(instance.vk_addr)

		if DEBUG_MODE:
			print(f"There are {len(availableDevices)} physical devices available on this system")

		# check if a suitable device can be found
		for device in availableDevices:
			if DEBUG_MODE:
				self.log_device_properties(device)
			if self.is_suitable(device):
				self.vk_addr = device
				break

	@staticmethod
	def log_device_properties(device):

		properties = vkGetPhysicalDeviceProperties(device)

		print(f"Device name: {properties.deviceName}")

		print("Device type: ",end="")

		if properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_CPU:
			print("CPU")
		elif properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU:
			print("Discrete GPU")
		elif properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU:
			print("Integrated GPU")
		elif properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU:
			print("Virtual GPU")
		else:
			print("Other")

	@staticmethod
	def is_suitable(device):
		"""
		A device is suitable if it can present to the screen, ie support
		the swapchain extension
		"""

		if DEBUG_MODE:
			print("Checking if device is suitable")

		requestedExtensions = [
			VK_KHR_SWAPCHAIN_EXTENSION_NAME
		]

		if DEBUG_MODE:
			print("We are requesting device extensions:")

			for extension in requestedExtensions:
				print(f"\t\"{extension}\"")

		if PhysicalDevice.check_device_extension_support(device, requestedExtensions):

			if DEBUG_MODE:
				print("Device can support the requested extensions!")
			return True
		
		if DEBUG_MODE:
			print("Device can't support the requested extensions!")

		return False

	@staticmethod
	def check_device_extension_support(device, requestedExtensions):
		"""
		Check if a given physical device can satisfy a list of requested device extensions.
		"""

		supportedExtensions = [
			extension.extensionName 
			for extension in vkEnumerateDeviceExtensionProperties(device, None)
		]

		if DEBUG_MODE:
			print("Device can support extensions:")

			for extension in supportedExtensions:
				print(f"\t\"{extension}\"")

		for extension in requestedExtensions:
			if extension not in supportedExtensions:
				return False
		
		return True

	def find_depth_format(self):
		return self.find_supported_format(
			[
				VK_FORMAT_D24_UNORM_S8_UINT,
				VK_FORMAT_D32_SFLOAT, 
				VK_FORMAT_D32_SFLOAT_S8_UINT
			],
			VK_IMAGE_TILING_OPTIMAL, 
			VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT,
		)

	def find_supported_format(self, candidates:list, tiling, features):
		for format in candidates:
			props = vkGetPhysicalDeviceFormatProperties(self.vk_addr, format)

			if (tiling, features) == (VK_IMAGE_TILING_LINEAR, props.linearTilingFeatures & features):
				return format
			if (tiling, features) == (VK_IMAGE_TILING_OPTIMAL, props.optimalTilingFeatures & features):
				return format

		raise Exception('Failed to find suitable format.')


class LogicalDevice:
	def __init__(self, queue_family:'QueueFamilyIndices'):
		unique_indices = list(set([queue_family.graphics_family, queue_family.present_family]))

		queue_create_info = [
			VkDeviceQueueCreateInfo(
				queueFamilyIndex = index, queueCount = 1,
				pQueuePriorities = [1.0]
			)
			for index in unique_indices
		]

		device_features = [
			VkPhysicalDeviceFeatures(
				multiDrawIndirect=VK_KHR_draw_indirect_count,
				samplerAnisotropy=VK_TRUE 
			)
		]

		enabled_layers = []
		if DEBUG_MODE:
			enabled_layers.append("VK_LAYER_KHRONOS_validation")

		device_extensions = [
			VK_KHR_SWAPCHAIN_EXTENSION_NAME,
			VK_KHR_DRAW_INDIRECT_COUNT_EXTENSION_NAME
		]

		create_info = VkDeviceCreateInfo(
			queueCreateInfoCount = len(queue_create_info), pQueueCreateInfos = queue_create_info,
			enabledExtensionCount = len(device_extensions), ppEnabledExtensionNames = device_extensions,
			pEnabledFeatures = device_features,
			enabledLayerCount = len(enabled_layers), ppEnabledLayerNames = enabled_layers
		)

		self.device = vkCreateDevice(physicalDevice = BVKC.physical_device.vk_addr, pCreateInfo = [create_info], pAllocator = None)

	def destroy(self):
		'Everything created using this device needs to be destroyed beforehand.'
		vkDestroyDevice(self.device, None)

