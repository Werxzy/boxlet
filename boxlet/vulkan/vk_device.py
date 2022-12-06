from . import * 
from .vk_library import *


"""
	Vulkan separates the concept of physical and logical devices. 
	A physical device usually represents a single complete implementation of Vulkan 
	(excluding instance-level functionality) available to the host, 
	of which there are a finite number. 
  
	A logical device represents an instance of that implementation 
	with its own state and resources independent of other logical devices.
"""


def log_device_properties(device):
	
	"""
		void vkGetPhysicalDeviceProperties(
			VkPhysicalDevice                            physicalDevice,
			VkPhysicalDeviceProperties*                 pProperties);
	"""

	properties = vkGetPhysicalDeviceProperties(device)

	"""
		typedef struct VkPhysicalDeviceProperties {
			uint32_t                            apiVersion;
			uint32_t                            driverVersion;
			uint32_t                            vendorID;
			uint32_t                            deviceID;
			VkPhysicalDeviceType                deviceType;
			char                                deviceName[VK_MAX_PHYSICAL_DEVICE_NAME_SIZE];
			uint8_t                             pipelineCacheUUID[VK_UUID_SIZE];
			VkPhysicalDeviceLimits              limits;
			VkPhysicalDeviceSparseProperties    sparseProperties;
			} VkPhysicalDeviceProperties;
	"""

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

def is_suitable(device):

	if DEBUG_MODE:
		print("Checking if device is suitable")

	"""
		A device is suitable if it can present to the screen, ie support
		the swapchain extension
	"""
	requestedExtensions = [
		VK_KHR_SWAPCHAIN_EXTENSION_NAME
	]

	if DEBUG_MODE:
		print("We are requesting device extensions:")

		for extension in requestedExtensions:
			print(f"\t\"{extension}\"")

	if check_device_extension_support(device, requestedExtensions):

		if DEBUG_MODE:
			print("Device can support the requested extensions!")
		return True
	
	if DEBUG_MODE:
		print("Device can't support the requested extensions!")

	return False

def choose_physical_device(instance):

	"""
		Choose a suitable physical device from a list of candidates.
	
		Note: Physical devices are neither created nor destroyed, they exist
		independently to the program.
	"""

	if DEBUG_MODE:
		print("Choosing Physical Device")

	"""
		vkEnumeratePhysicalDevices(instance) -> List(vkPhysicalDevice)
	"""
	availableDevices = vkEnumeratePhysicalDevices(instance)

	if DEBUG_MODE:
		print(f"There are {len(availableDevices)} physical devices available on this system")

	# check if a suitable device can be found
	for device in availableDevices:
		if DEBUG_MODE:
			log_device_properties(device)
		if is_suitable(device):
			return device

	return None

class LogicalDevice:
	def __init__(self, physical_device, queue_family:'vk_queue_families.QueueFamilyIndices'):
		unique_indices = list(set([queue_family.graphics_family, queue_family.present_family]))

		queue_create_info = [
			VkDeviceQueueCreateInfo(
				queueFamilyIndex = index, queueCount = 1,
				pQueuePriorities = [1.0]
			)
			for index in unique_indices
		]

		device_features = VkPhysicalDeviceFeatures()

		enabled_layers = []
		if DEBUG_MODE:
			enabled_layers.append("VK_LAYER_KHRONOS_validation")

		device_extensions = [
			VK_KHR_SWAPCHAIN_EXTENSION_NAME
		]

		create_info = VkDeviceCreateInfo(
			queueCreateInfoCount = len(queue_create_info), pQueueCreateInfos = queue_create_info,
			enabledExtensionCount = len(device_extensions), ppEnabledExtensionNames = device_extensions,
			pEnabledFeatures = [device_features],
			enabledLayerCount = len(enabled_layers), ppEnabledLayerNames = enabled_layers
		)

		self.device = vkCreateDevice(physicalDevice = physical_device, pCreateInfo = [create_info], pAllocator = None)

	def destroy(self):
		'Everything created using this device needs to be destroyed beforehand.'
		vkDestroyDevice(self.device, None)




